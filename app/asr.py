"""On-device speech-to-text: Qualcomm AI Hub Whisper-Base (multilingual) on the Hexagon NPU.

Encoder + decoder are AI Hub precompiled QNN context binaries executed through the
ONNX Runtime QNN execution provider. Falls back to nothing silently: if the NPU is
missing we raise, so benchmark numbers are never mislabeled.
"""
import glob
import os
import time

import numpy as np
import onnxruntime as ort
import onnxruntime_qnn as qnn
from tokenizers import Tokenizer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = glob.glob(os.path.join(ROOT, "models", "whisper_base", "*"))[0]

SR, N_FFT, HOP, N_MELS, CHUNK = 16000, 400, 160, 80, 30
SOT, EOT, TRANSCRIBE, NO_TS = 50258, 50257, 50359, 50363
LANGS = {"en": 50259, "hi": 50276}  # english, hindi
N_LAYERS, SELF_LEN = 6, 199

_registered = False


def _npu_options():
    global _registered
    if not _registered:
        ort.register_execution_provider_library(qnn.get_ep_name(), qnn.get_library_path())
        _registered = True
    devs = [d for d in ort.get_ep_devices()
            if d.ep_name == "QNNExecutionProvider" and "NPU" in str(d.device.type)]
    if not devs:
        raise RuntimeError("No Hexagon NPU device found for QNNExecutionProvider")
    so = ort.SessionOptions()
    so.add_provider_for_devices(devs, {})
    return so


def log_mel(audio: np.ndarray) -> np.ndarray:
    audio = np.pad(audio.astype(np.float32), (0, max(0, CHUNK * SR - len(audio))))[: CHUNK * SR]
    win = np.hanning(N_FFT + 1)[:-1].astype(np.float32)
    padded = np.pad(audio, (N_FFT // 2, N_FFT // 2), mode="reflect")
    n_frames = 1 + (len(padded) - N_FFT) // HOP
    idx = np.arange(N_FFT)[None, :] + HOP * np.arange(n_frames)[:, None]
    stft = np.fft.rfft(padded[idx] * win, axis=-1)
    mag = (np.abs(stft) ** 2)[:-1].T  # drop last frame -> 3000
    filters = np.load(os.path.join(ROOT, "models", "mel_filters.npz"))[f"mel_{N_MELS}"]
    mel = filters @ mag
    log = np.log10(np.clip(mel, 1e-10, None))
    log = np.maximum(log, log.max() - 8.0)
    return ((log + 4.0) / 4.0).astype(np.float16)[None]


class Whisper:
    def __init__(self):
        so = _npu_options()
        t = time.time()
        self.enc = ort.InferenceSession(os.path.join(MODEL_DIR, "encoder.onnx"), sess_options=so)
        self.dec = ort.InferenceSession(os.path.join(MODEL_DIR, "decoder.onnx"), sess_options=so)
        self.load_s = time.time() - t
        self.tok = Tokenizer.from_file(os.path.join(ROOT, "models", "tokenizer.json"))
        suppress = [i for i in range(50257, 51865)]  # all special tokens except we allow EOT below
        self.suppress = np.array([i for i in suppress if i != EOT], dtype=np.int64)

    def transcribe(self, audio: np.ndarray, language: str | None = None):
        """audio: float32 mono 16 kHz. Returns (text, language, stats)."""
        t0 = time.time()
        mel = log_mel(audio)
        t_mel = time.time()
        enc_out = self.enc.run(None, {"input_features": mel})
        enc_names = [o.name for o in self.enc.get_outputs()]
        cross = dict(zip(enc_names, enc_out))
        t_enc = time.time()

        selfc = {}
        for i in range(N_LAYERS):
            selfc[f"k_cache_self_{i}_in"] = np.zeros((8, 1, 64, SELF_LEN), np.float16)
            selfc[f"v_cache_self_{i}_in"] = np.zeros((8, 1, SELF_LEN, 64), np.float16)
        mask = np.full((1, 1, 1, SELF_LEN + 1), -100.0, np.float16)
        mask[..., -1] = 0

        def step(tok, pos):
            feed = {"input_ids": np.array([[tok]], np.int32),
                    "position_ids": np.array([pos], np.int32),
                    "attention_mask": mask, **cross, **selfc}
            out = self.dec.run(None, feed)
            names = [o.name for o in self.dec.get_outputs()]
            res = dict(zip(names, out))
            for i in range(N_LAYERS):
                selfc[f"k_cache_self_{i}_in"] = res[f"k_cache_self_{i}_out"]
                selfc[f"v_cache_self_{i}_in"] = res[f"v_cache_self_{i}_out"]
            mask[..., -(pos + 2)] = 0
            return res["logits"].reshape(-1).astype(np.float32)

        pos = 0
        logits = step(SOT, pos); pos += 1
        if language is None:
            cand = np.array(list(LANGS.values()))
            language = {v: k for k, v in LANGS.items()}[int(cand[np.argmax(logits[cand])])]
        prompt = [LANGS[language], TRANSCRIBE, NO_TS]
        for tk in prompt:
            logits = step(tk, pos); pos += 1
        out_tokens = []
        while pos < SELF_LEN - 1:
            logits[self.suppress] = -1e9
            nxt = int(np.argmax(logits))
            if nxt == EOT:
                break
            out_tokens.append(nxt)
            logits = step(nxt, pos); pos += 1
        t_dec = time.time()
        text = self.tok.decode(out_tokens).strip()
        stats = {"mel_ms": (t_mel - t0) * 1e3, "encoder_ms": (t_enc - t_mel) * 1e3,
                 "decoder_ms": (t_dec - t_enc) * 1e3, "total_ms": (t_dec - t0) * 1e3,
                 "tokens": len(out_tokens), "audio_s": len(audio) / SR}
        return text, language, stats


def load_wav(path: str) -> np.ndarray:
    import soundfile as sf
    a, sr = sf.read(path, dtype="float32")
    if a.ndim > 1:
        a = a.mean(1)
    if sr != SR:
        n = int(len(a) * SR / sr)
        a = np.interp(np.linspace(0, len(a) - 1, n), np.arange(len(a)), a).astype(np.float32)
    return a


if __name__ == "__main__":
    import sys
    w = Whisper()
    print(f"models loaded on NPU in {w.load_s:.2f}s")
    text, lang, st = w.transcribe(load_wav(sys.argv[1]), sys.argv[2] if len(sys.argv) > 2 else None)
    print(lang, "|", text)
    print({k: round(v, 1) for k, v in st.items()})
