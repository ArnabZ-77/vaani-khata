"""Download the Qualcomm AI Hub precompiled Whisper-Small (Snapdragon X) + tokenizer/mel assets into ./models.
Whisper-Small is the default (much better Hindi than Base). ~1 GB download."""
import io, os, urllib.request, zipfile
R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models"); os.makedirs(R, exist_ok=True)
AI = "https://qaihub-public-assets.s3.us-west-2.amazonaws.com/qai-hub-models/models/whisper_small/releases/v0.63.0/"
def get(u): print("downloading", u); return urllib.request.urlopen(u).read()
zipfile.ZipFile(io.BytesIO(get(AI + "whisper_small-precompiled_qnn_onnx-float-qualcomm_snapdragon_x_elite.zip"))).extractall(os.path.join(R, "whisper_small"))
open(os.path.join(R, "tokenizer.json"), "wb").write(get("https://huggingface.co/openai/whisper-base/resolve/main/tokenizer.json"))
open(os.path.join(R, "mel_filters.npz"), "wb").write(get("https://raw.githubusercontent.com/openai/whisper/main/whisper/assets/mel_filters.npz"))
# optional: CPU baseline for app/bench.py
open(os.path.join(R, "enc_cpu_whisper_small.onnx"), "wb").write(get("https://huggingface.co/onnx-community/whisper-small/resolve/main/onnx/encoder_model.onnx"))
print("done")
