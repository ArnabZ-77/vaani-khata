# Measured on the target device

Device: Samsung Galaxy Book4 Edge, Snapdragon X (X126100), Windows 11 ARM64, 16 GB RAM, on battery.
Stack: onnxruntime 1.30 + onnxruntime-qnn 2.6 (QNN EP), Python 3.12 ARM64.
Script: `python app/bench.py` (30 timed runs after 5 warm-ups; same 30 s input for both).

## Whisper-Base encoder, 30 s audio window

| Run | NPU median (fp16) | CPU median (fp32) | Speed-up |
|---|---|---|---|
| 1 | 44.7 ms | 1058.7 ms | 23.7x |
| 2 | 45.4 ms | 1406.1 ms | 31.0x |
| 3 | 44.7 ms | 1017.3 ms | 22.8x |
| 4 | 45.3 ms | 1030.4 ms | 22.7x |
| 5 (outlier) | 44.8 ms | 296.1 ms | 6.6x |

The NPU is stable at ~45 ms in every run. The CPU baseline varies with the laptop's power/thermal state;
in 4 of 5 runs it was ~1.0-1.4 s. We report the typical figure (~23x) and disclose the outlier (6.6x).

Baseline note: CPU = the open `onnx-community/whisper-base` encoder (same architecture) on the ORT CPU EP.
AI Hub ships no CPU build of Whisper, so this compares the same model family, not the same file.

## End-to-end (mel + encoder + greedy decode of 27 tokens), 10.8 s spoken clip, all on NPU

| Metric | Value |
|---|---|
| Total latency (median of 5) | 229-266 ms |
| Real-time factor | ~45x |
| Model load (encoder+decoder context binaries) | ~0.4-0.6 s |
