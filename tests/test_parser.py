"""Parser モジュールのテスト."""

import unittest

from core.parser import Parser


class TestParser(unittest.TestCase):
    """Parser クラスのテスト."""

    def setUp(self):
        self.parser = Parser()

    def test_parse_basic(self):
        """基本的なHTML解析テスト."""
        html = """
        <div class="list">
            <div class="item">
                <h2 class="title">記事タイトル1</h2>
                <span class="date">2026-01-01</span>
            </div>
            <div class="item">
                <h2 class="title">記事タイトル2</h2>
                <span class="date">2026-01-02</span>
            </div>
        </div>
        """
        fields = [
            {"name": "タイトル", "selector": "h2.title", "attribute": "text"},
            {"name": "日付", "selector": "span.date", "attribute": "text"},
        ]
        result = self.parser.parse(html, "div.item", fields)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["タイトル"], "記事タイトル1")
        self.assertEqual(result[1]["日付"], "2026-01-02")

    def test_parse_href_attribute(self):
        """href属性の抽出テスト."""
        html = """
        <ul>
            <li><a class="link" href="/page/1">リンク1</a></li>
            <li><a class="link" href="/page/2">リンク2</a></li>
        </ul>
        """
        fields = [
            {"name": "URL", "selector": "a.link", "attribute": "href", "resolve_url": True},
            {"name": "テキスト", "selector": "a.link", "attribute": "text"},
        ]
        result = self.parser.parse(html, "li", fields, base_url="https://example.com")
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["URL"], "https://example.com/page/1")
        self.assertEqual(result[0]["テキスト"], "リンク1")

    def test_parse_no_match(self):
        """コンテナセレクタに一致しない場合."""
        html = "<div>何もない</div>"
        result = self.parser.parse(html, "div.nonexistent", [])
        self.assertEqual(result, [])

    def test_parse_with_regex(self):
        """正規表現フィルタのテスト."""
        html = """
        <div class="item">
            <span class="info">更新日: 2026-02-20 公開</span>
        </div>
        """
        fields = [
            {
                "name": "日付",
                "selector": "span.info",
                "attribute": "text",
                "regex": r"\d{4}-\d{2}-\d{2}",
            },
        ]
        result = self.parser.parse(html, "div.item", fields)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["日付"], "2026-02-20")

    def test_find_next_page(self):
        """次ページURL検出テスト."""
        html = '<a class="next" href="/page/2">次へ</a>'
        config = {"enabled": True, "selector": "a.next"}
        result = self.parser.find_next_page(
            html, config, base_url="https://example.com"
        )
        self.assertEqual(result, "https://example.com/page/2")

    def test_find_next_page_disabled(self):
        """ページネーション無効時のテスト."""
        html = '<a class="next" href="/page/2">次へ</a>'
        config = {"enabled": False}
        result = self.parser.find_next_page(html, config)
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
