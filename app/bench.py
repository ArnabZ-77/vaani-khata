"""Benchmark: Whisper-Base encoder on Hexagon NPU vs the same architecture on the Oryon CPU (ORT CPU EP, fp32).
Run on the Snapdragon target machine; prints a markdown table used in the README/pitch."""
import glob, os, statistics as st, sys, time
import numpy as np, onnxruntime as ort
sys.path.insert(0, os.path.dirname(__file__))
from asr import _npu_options, ROOT, Whisper, load_wav
MODEL = os.environ.get("WHISPER_MODEL", "whisper_small")
MODEL_DIR = glob.glob(os.path.join(ROOT, "models", MODEL, "*"))[0]

def bench(sess, x, n=30, warm=5):
    name = sess.get_inputs()[0].name
    for _ in range(warm): sess.run(None, {name: x})
    t = []
    for _ in range(n):
        s = time.perf_counter(); sess.run(None, {name: x}); t.append((time.perf_counter() - s) * 1e3)
    return st.median(t), min(t), max(t)

x16 = np.random.randn(1, 80, 3000).astype(np.float16)
npu = ort.InferenceSession(os.path.join(MODEL_DIR, "encoder.onnx"), sess_options=_npu_options())
cpu = ort.InferenceSession(os.path.join(ROOT, "models", f"enc_cpu_{MODEL}.onnx"), providers=["CPUExecutionProvider"])
a = bench(npu, x16); b = bench(cpu, x16.astype(np.float32))
print(f"| {MODEL} encoder (30 s audio) | median ms | min | max |\n|---|---|---|---|")
print(f"| Hexagon NPU (QNN, fp16) | {a[0]:.1f} | {a[1]:.1f} | {a[2]:.1f} |")
print(f"| Oryon CPU (ORT CPU, fp32) | {b[0]:.1f} | {b[1]:.1f} | {b[2]:.1f} |")
print(f"\nNPU speed-up: {b[0]/a[0]:.1f}x")

w = Whisper(MODEL); clip = os.path.join(ROOT, "app", "test_en.wav")
runs = [w.transcribe(load_wav(clip), "en")[2] for _ in range(5)]
tot = st.median(r["total_ms"] for r in runs)
print(f"\nEnd-to-end (mel + encoder + 27-token decode) on NPU, {runs[0]['audio_s']:.1f}s clip: {tot:.0f} ms median = {runs[0]['audio_s']*1000/tot:.0f}x real-time")

