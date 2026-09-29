"""Download the Qualcomm AI Hub precompiled Whisper-Base (Snapdragon X) + tokenizer/mel assets into ./models."""
import io, os, urllib.request, zipfile
R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models"); os.makedirs(R, exist_ok=True)
AI = "https://qaihub-public-assets.s3.us-west-2.amazonaws.com/qai-hub-models/models/whisper_base/releases/v0.63.0/"
def get(u): print("downloading", u); return urllib.request.urlopen(u).read()
zipfile.ZipFile(io.BytesIO(get(AI + "whisper_base-precompiled_qnn_onnx-float-qualcomm_snapdragon_x_elite.zip"))).extractall(os.path.join(R, "whisper_base"))
open(os.path.join(R, "tokenizer.json"), "wb").write(get("https://huggingface.co/openai/whisper-base/resolve/main/tokenizer.json"))
open(os.path.join(R, "mel_filters.npz"), "wb").write(get("https://raw.githubusercontent.com/openai/whisper/main/whisper/assets/mel_filters.npz"))
# optional: CPU baseline for app/bench.py
open(os.path.join(R, "enc_cpu.onnx"), "wb").write(get("https://huggingface.co/onnx-community/whisper-base/resolve/main/onnx/encoder_model.onnx"))
print("done")
