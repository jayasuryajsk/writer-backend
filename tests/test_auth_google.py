import unittest
from base64 import b64encode
from urllib.parse import urlparse, parse_qs

from services.api import auth_google


class MockAuth:
    def __init__(self):
        self.received_code = None

    def exchange_code_for_session(self, code):
        self.received_code = code

        class User:
            id = "uid123"

        class Sess:
            access_token = "token456"

        class Session:
            user = User()
            session = Sess()

        return Session()


class MockSupabase:
    def __init__(self):
        self.auth = MockAuth()


class AuthGoogleFlowTest(unittest.TestCase):
    def setUp(self):
        auth_google.supabase_client = MockSupabase()
        auth_google._STATE_DB.clear()

    def test_full_flow(self):
        resp = auth_google.native_app_signin(
            callback_port="5555",
            pubkey="testkey",
            state_db=auth_google._STATE_DB,
        )
        self.assertEqual(resp.status_code, 307)
        loc = resp.headers["location"]
        parsed = urlparse(loc)
        qs = parse_qs(parsed.query)
        state = qs["state"][0]
        self.assertIn(state, auth_google._STATE_DB)
        self.assertEqual(auth_google._STATE_DB[state], ("5555", "testkey"))

        called = {}

        def fake_urlopen(url):
            called["url"] = url
            class Dummy:
                pass
            return Dummy()

        auth_google.request.urlopen = fake_urlopen

        resp2 = auth_google.oauth_callback(
            code="thecode",
            state=state,
            state_db=auth_google._STATE_DB,
            client=auth_google.supabase_client,
        )
        expected_data = b64encode(b"uid123 token456").decode()
        self.assertEqual(
            called["url"], f"http://127.0.0.1:5555/token?data={expected_data}"
        )
        self.assertEqual(auth_google.supabase_client.auth.received_code, "thecode")
        self.assertEqual(resp2.status_code, 307)
        self.assertEqual(resp2.headers["location"], "/native_app_signin_succeeded")
        self.assertNotIn(state, auth_google._STATE_DB)


if __name__ == "__main__":
    unittest.main()
