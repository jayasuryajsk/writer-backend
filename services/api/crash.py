import base64
import json
import os
import uuid
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

try:
    import sentry_sdk
    from sentry_sdk import Attachment
except Exception:  # pragma: no cover - fallback when sentry_sdk is missing
    class Attachment:
        def __init__(self, bytes: bytes, filename: str):
            self.bytes = bytes
            self.filename = filename

    class _Dummy:
        @staticmethod
        def init(*a, **k):
            pass

        @staticmethod
        def capture_message(*a, **k):
            pass

    sentry_sdk = _Dummy()

sentry_sdk.init(dsn=os.environ.get("SENTRY_DSN"))


class CrashHandler(BaseHTTPRequestHandler):
    def _ok(self) -> None:
        self.send_response(200)
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802 - http.server naming
        if self.path == "/health":
            self._ok()
        else:
            self.send_error(404)

    def do_POST(self) -> None:  # noqa: N802 - http.server naming
        if self.path == "/crash":
            length = int(self.headers.get("Content-Length", 0))
            data = self.rfile.read(length)
            payload = json.loads(data.decode()) if data else {}
            b64_zip = payload.get("base64_zip")
            if not b64_zip:
                self.send_error(400)
                return
            zip_bytes = base64.b64decode(b64_zip)
            os.makedirs("crash_store", exist_ok=True)
            filename = f"{uuid.uuid4()}.zip"
            with open(os.path.join("crash_store", filename), "wb") as f:
                f.write(zip_bytes)
            sentry_sdk.capture_message(
                "client_crash",
                attachments=[Attachment(bytes=zip_bytes, filename=filename)],
            )
            self._ok()
        elif self.path == "/health":
            self._ok()
        else:
            self.send_error(404)


def run_server(host: str = "0.0.0.0", port: int = 8000) -> HTTPServer:
    server = HTTPServer((host, port), CrashHandler)
    Thread(target=server.serve_forever, daemon=True).start()
    return server


if __name__ == "__main__":  # pragma: no cover
    run_server().serve_forever()
