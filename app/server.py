"""Vaani Khata local server. Everything runs on-device; binds to localhost only."""
import io
import json
import os
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from asr import Whisper, load_wav  # noqa: E402
from ledger import Khata  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(os.path.dirname(HERE), "khata.sqlite3")
lock = threading.Lock()
whisper = Whisper()
khata = Khata(DB)
last_stats = {}


def state():
    return {"balances": khata.balances(), "recent": khata.recent(), "sales_total": khata.sales_total(),
            "stats": last_stats, "device": "Snapdragon X · Hexagon NPU (QNN)", "load_s": whisper.load_s}


class H(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json"):
        data = body if isinstance(body, bytes) else json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype + ("; charset=utf-8" if "json" in ctype or "html" in ctype else ""))
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _body(self):
        return self.rfile.read(int(self.headers.get("Content-Length", 0)))

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._send(200, open(os.path.join(HERE, "index.html"), "rb").read(), "text/html")
        elif self.path == "/api/state":
            self._send(200, state())
        else:
            self._send(404, {"error": "not found"})

    def do_POST(self):
        global last_stats
        if self.path == "/api/transcribe":
            lang = self.headers.get("X-Lang") or None
            lang = None if lang in (None, "", "auto") else lang
            raw = self._body()
            audio = np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0  # 16 kHz mono PCM16
            with lock:
                text, detected, st = whisper.transcribe(audio, lang)
                entries, answers = khata.apply(text)
                last_stats = {k: round(v, 1) for k, v in st.items()}
            self._send(200, {"text": text, "lang": detected, "entries": entries, "answers": answers, **state()})
        elif self.path == "/api/text":
            text = json.loads(self._body())["text"]
            with lock:
                entries, answers = khata.apply(text)
            self._send(200, {"text": text, "entries": entries, "answers": answers, **state()})
        elif self.path == "/api/reset":
            with lock:
                khata.db.execute("DELETE FROM entries")
                khata.db.commit()
            self._send(200, state())
        else:
            self._send(404, {"error": "not found"})

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8765"))
    print(f"Vaani Khata on http://127.0.0.1:{port}  (Whisper-Base on Hexagon NPU, loaded in {whisper.load_s:.2f}s)")
    ThreadingHTTPServer(("127.0.0.1", port), H).serve_forever()
