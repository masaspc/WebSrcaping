"""ユーティリティ関数群."""

import re
from urllib.parse import urljoin, urlparse


def resolve_url(base_url: str, relative_url: str) -> str:
    """相対URLを絶対URLに変換する."""
    if not relative_url:
        return ""
    parsed = urlparse(relative_url)
    if parsed.scheme:
        return relative_url
    return urljoin(base_url, relative_url)


def apply_regex(text: str, pattern: str) -> str:
    """正規表現パターンにマッチする最初の部分を返す.

    パターンが空の場合は元のテキストをそのまま返す.
    """
    if not pattern:
        return text
    match = re.search(pattern, text)
    if match:
        return match.group(0)
    return text


def sanitize_filename(name: str) -> str:
    """ファイル名に使用できない文字を置換する."""
    invalid_chars = r'[<>:"/\\|?*]'
    return re.sub(invalid_chars, "_", name)


def is_valid_url(url: str) -> bool:
    """URLの基本的な形式チェック."""
    try:
        result = urlparse(url)
        return all([result.scheme in ("http", "https"), result.netloc])
    except Exception:
        return False
