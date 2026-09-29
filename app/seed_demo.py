"""Load a small demo ledger into a running Vaani Khata server (used for screenshots)."""
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from asr import load_wav  # noqa: E402

BASE = "http://127.0.0.1:8765"


def post(path, data, headers=None):
    req = urllib.request.Request(BASE + path, data=data, headers=headers or {})
    return json.loads(urllib.request.urlopen(req).read())


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    audio = (load_wav(os.path.join(here, "test_en.wav")) * 32767).astype("<i2").tobytes()
    post("/api/reset", b"{}")
    post("/api/transcribe", audio, {"X-Lang": "auto"})
    for t in ["रमेश ने 300 रुपये उधार लिए।", "Sunita ne 150 rupaye wapas diye"]:
        post("/api/text", json.dumps({"text": t}).encode())
    r = post("/api/text", json.dumps({"text": "How much does Ramesh owe?"}).encode())
    print(r["answers"], r["balances"])
