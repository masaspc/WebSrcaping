"""Fetcher モジュールのテスト."""

import unittest

from core.fetcher import FetchError, Fetcher


class TestFetcher(unittest.TestCase):
    """Fetcher クラスのテスト."""

    def test_init(self):
        """初期化テスト."""
        fetcher = Fetcher(user_agent="TestBot/1.0", timeout=10, encoding="utf-8")
        self.assertEqual(fetcher.timeout, 10)
        self.assertEqual(fetcher.encoding, "utf-8")
        fetcher.close()

    def test_invalid_url(self):
        """無効なURLのテスト."""
        fetcher = Fetcher(timeout=5)
        with self.assertRaises(FetchError):
            fetcher.get("http://invalid.localhost.test")
        fetcher.close()


if __name__ == "__main__":
    unittest.main()
