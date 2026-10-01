"""UI-only preview when PostgreSQL/Ollama are not running. No sample API data."""
import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent


class PreviewHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_GET(self):
        if self.path == "/":
            self.send_response(302)
            self.send_header("Location", "/workspace/")
            self.end_headers()
        elif self.path.startswith("/workspace/"):
            self.path = self.path.removeprefix("/workspace")
            super().do_GET()
        else:
            self.api_unavailable()

    def api_unavailable(self):
        payload = json.dumps({"detail": "화면 미리보기 모드예요. 실제 데이터를 사용하려면 FastAPI 서버를 실행해 주세요."}).encode()
        self.send_response(503)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    do_POST = api_unavailable
    do_PUT = api_unavailable


if __name__ == "__main__":
    print("UI preview: http://127.0.0.1:8080/workspace/", flush=True)
    ThreadingHTTPServer(("127.0.0.1", 8080), PreviewHandler).serve_forever()
