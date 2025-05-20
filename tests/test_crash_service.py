import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import base64
import io
import json
import os
import urllib.request
import zipfile
import unittest
import tempfile

from services.api import crash


def _start_server():
    server = crash.run_server(host="127.0.0.1", port=0)
    return server, server.server_address[1]


def _create_zip_bytes() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("test.txt", b"hello")
    return buf.getvalue()


class CrashServiceTest(unittest.TestCase):
    def test_health_post(self):
        tmp_dir = tempfile.mkdtemp()
        os.chdir(tmp_dir)
        server, port = _start_server()
        try:
            req = urllib.request.Request(
                f"http://127.0.0.1:{port}/health",
                method="POST",
            )
            with urllib.request.urlopen(req) as resp:
                self.assertEqual(resp.status, 200)
        finally:
            server.shutdown()
            server.server_close()

    def test_post_crash_writes_file(self):
        tmp_dir = tempfile.mkdtemp()
        os.chdir(tmp_dir)
        server, port = _start_server()
        try:
            data = base64.b64encode(_create_zip_bytes()).decode()
            body = json.dumps({"base64_zip": data}).encode()
            req = urllib.request.Request(
                f"http://127.0.0.1:{port}/crash",
                data=body,
                method="POST",
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req) as resp:
                self.assertEqual(resp.status, 200)
            files = os.listdir("crash_store")
            self.assertEqual(len(files), 1)
            self.assertTrue(files[0].endswith(".zip"))
        finally:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    unittest.main()
