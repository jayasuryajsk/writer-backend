import os
import sys
import sqlite3
import time
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.api import ai_proxy

class AiProxyQuotaTest(unittest.TestCase):
    def setUp(self):
        if os.path.exists(ai_proxy.DB_PATH):
            os.remove(ai_proxy.DB_PATH)
        ai_proxy.init_db()

    def fake_create(self, *args, **kwargs):
        return {'choices': [{'message': {'content': 'after'}}]}

    def test_quota_exceeded(self):
        with patch('openai.ChatCompletion.create', self.fake_create):
            conn = sqlite3.connect(ai_proxy.DB_PATH)
            c = conn.cursor()
            c.execute('INSERT INTO usage VALUES (?, ?, ?)', ('bob', 50000, time.time()))
            conn.commit()
            conn.close()

            with self.assertRaises(ValueError):
                ai_proxy.completions({'messages': []}, user='bob')

if __name__ == '__main__':
    unittest.main()
