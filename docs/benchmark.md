# Measured on the target device

Device: Samsung Galaxy Book4 Edge, Snapdragon X (X126100), Windows 11 ARM64, 16 GB RAM, on battery.
Stack: onnxruntime 1.30 + onnxruntime-qnn 2.6 (QNN EP), Python 3.12 ARM64.
Script: `python app/bench.py` (30 timed runs after 5 warm-ups; same 30 s input for both).

## Default model: Whisper-Small (multilingual), encoder, 30 s audio window

| Run | NPU median (fp16) | CPU median (fp32) | Speed-up |
|---|---|---|---|
| 1 | 115.8 ms | 5627.7 ms | 48.6x |
| 2 | 114.8 ms | 5841.0 ms | 50.9x |

The NPU is stable at ~115 ms (min-max spread under 12 ms). The CPU baseline is slower and noisier; in run 1 one
CPU iteration stalled for 202 s (an OS-level stall), which does not affect the median but is disclosed here.

End-to-end on the NPU (mel + encoder + 27-token greedy decode), 10.8 s English clip: **646-679 ms median, about 16-17x real-time.**
Short Hindi sentences (~4 s) take about 0.9-1.5 s end to end including decoder prompt priming.

Baseline note: CPU = the open `onnx-community/whisper-small` encoder (same architecture) on the ORT CPU EP.
AI Hub ships no CPU build of Whisper, so this compares the same model family, not the same file.

## Why Whisper-Small: Hindi accuracy (6 synthetic Hindi/Hinglish sentences, neural TTS voices)

| Model | Correct ledger entries | Typical errors |
|---|---|---|
| Whisper-Base | 2 of 6 | garbled words ("वुपय" for रुपये), hallucinated repeats, wrong names |
| Whisper-Small | 6 of 6 | spelling variants only (सूनीता, दिये, उदार), handled by the parser |

Whisper-Base is 2.6x faster than Small (encoder ~45 ms vs ~115 ms on the NPU, ~23x over CPU), and is still
supported: `WHISPER_MODEL=whisper_base`. We default to Small because correct Hindi matters more than 70 ms.
Caveat: test audio was synthetic; real shop noise and accents will be harder.
Without a Devanagari priming prompt, Whisper writes Hindi speech in Urdu script; `app/asr.py` primes the decoder to avoid this.
