"""极简 ASR 服务：Vosk + OpenAI 兼容接口。

- POST /v1/audio/transcriptions  (multipart: file, model)  -> {"text": "..."}
- GET  /healthz                                            -> {"ok": true, "model": ...}
- GET  /v1/models

只依赖标准库 + vosk + ffmpeg。第一次请求才加载模型，避免启动拖慢。
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import wave
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, "/AstrBot/data/site-packages")

MODEL_DIR = os.environ.get("VOSK_MODEL_DIR", "/AstrBot/data/vosk-model")
PORT = int(os.environ.get("PORT", "9001"))

_model = None
_lock = threading.Lock()


def get_model():
    global _model
    if _model is None:
        with _lock:
            if _model is None:
                import vosk
                vosk.SetLogLevel(-1)
                _model = vosk.Model(MODEL_DIR)
    return _model


def to_wav16k(src: str) -> str:
    """任意音频 -> 16k 单声道 wav（vosk 只吃这个）。"""
    dst = src + ".16k.wav"
    cmd = ["ffmpeg", "-nostdin", "-y", "-i", src, "-ar", "16000", "-ac", "1",
           "-f", "wav", dst]
    r = subprocess.run(cmd, capture_output=True, timeout=120)
    if r.returncode != 0 or not os.path.exists(dst):
        raise RuntimeError("ffmpeg 转换失败: " + (r.stderr or b"").decode("utf-8", "ignore")[-300:])
    return dst


def transcribe(path: str) -> str:
    import vosk
    wav = to_wav16k(path)
    wf = wave.open(wav, "rb")
    rec = vosk.KaldiRecognizer(get_model(), wf.getframerate())
    rec.SetWords(False)
    out = []
    while True:
        data = wf.readframes(4000)
        if not data:
            break
        if rec.AcceptWaveform(data):
            t = json.loads(rec.Result()).get("text", "").strip()
            if t:
                out.append(t)
    tail = json.loads(rec.FinalResult()).get("text", "").strip()
    if tail:
        out.append(tail)
    wf.close()
    return "".join(out).replace(" ", "")   # 中文去掉空格


def parse_multipart(body: bytes, ctype: str):
    """返回 (filename, bytes)。够用就行，不做完整 MIME 解析。"""
    if "boundary=" not in ctype:
        return None, body
    boundary = ctype.split("boundary=", 1)[1].strip().strip('"').encode()
    parts = body.split(b"--" + boundary)
    for part in parts:
        if b"filename=" not in part:
            continue
        head, _, data = part.partition(b"\r\n\r\n")
        name = b""
        for token in head.split(b";"):
            if b"filename=" in token:
                name = token.split(b"filename=", 1)[1].strip().strip(b'"')
        return name.decode("utf-8", "ignore") or "audio", data.rstrip(b"\r\n-")
    return None, b""


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def _json(self, code, obj):
        data = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path.startswith("/healthz"):
            self._json(200, {"ok": True, "model": os.path.basename(MODEL_DIR),
                             "loaded": _model is not None})
        elif self.path.startswith("/v1/models"):
            self._json(200, {"object": "list",
                             "data": [{"id": "vosk-cn", "object": "model"}]})
        else:
            self._json(404, {"error": "not found"})

    def do_POST(self):
        if not self.path.startswith("/v1/audio/transcriptions"):
            self._json(404, {"error": "not found"})
            return
        try:
            n = int(self.headers.get("Content-Length") or 0)
            body = self.rfile.read(n) if n else b""
            fname, payload = parse_multipart(body, self.headers.get("Content-Type", ""))
            if not payload:
                self._json(400, {"error": "empty audio"})
                return
            ext = os.path.splitext(fname or "")[1] or ".amr"
            tmp = tempfile.mkdtemp(prefix="asr-")
            src = os.path.join(tmp, "in" + ext)
            with open(src, "wb") as f:
                f.write(payload)
            text = transcribe(src)
            shutil.rmtree(tmp, ignore_errors=True)
            self._json(200, {"text": text})
        except Exception as e:
            self._json(500, {"error": repr(e)[:400]})


if __name__ == "__main__":
    if not os.path.isdir(MODEL_DIR):
        print("模型目录不存在:", MODEL_DIR, flush=True)
        sys.exit(1)
    print(f"ASR listening on :{PORT}, model={MODEL_DIR}", flush=True)
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
