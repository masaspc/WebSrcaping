"""HTML解析・データ抽出モジュール."""

import logging

from bs4 import BeautifulSoup

from core.utils import apply_regex, resolve_url

logger = logging.getLogger(__name__)


class Parser:
    """HTMLからデータを抽出するクラス."""

    def parse(
        self,
        html: str,
        container_selector: str,
        fields: list[dict],
        base_url: str = "",
    ) -> list[dict]:
        """HTMLを解析し、コンテナ内の各要素からフィールドデータを抽出する.

        Args:
            html: HTMLソース文字列
            container_selector: 繰り返し要素のCSSセレクタ
            fields: フィールド定義のリスト
            base_url: 相対URL解決用のベースURL

        Returns:
            抽出データの辞書リスト
        """
        soup = BeautifulSoup(html, "html.parser")
        containers = soup.select(container_selector)

        if not containers:
            logger.warning(
                "コンテナセレクタに一致する要素が見つかりません: %s",
                container_selector,
            )
            return []

        results = []
        for container in containers:
            row = {}
            for field in fields:
                value = self.extract_field(container, field, base_url)
                row[field["name"]] = value
            results.append(row)

        logger.info("→ %d件のデータを抽出", len(results))
        return results

    def extract_field(
        self,
        element,
        field_config: dict,
        base_url: str = "",
    ) -> str:
        """単一要素から指定フィールドの値を抽出する.

        Args:
            element: BeautifulSoup要素
            field_config: フィールド設定辞書
            base_url: 相対URL解決用のベースURL

        Returns:
            抽出された値の文字列
        """
        selector = field_config.get("selector", "")
        attribute = field_config.get("attribute", "text")
        should_resolve_url = field_config.get("resolve_url", False)
        regex = field_config.get("regex", "")

        target = element.select_one(selector)
        if target is None:
            return ""

        if attribute == "text":
            value = target.get_text(strip=True)
        else:
            value = target.get(attribute, "")
            if isinstance(value, list):
                value = " ".join(value)

        if should_resolve_url and base_url and value:
            value = resolve_url(base_url, value)

        if regex:
            value = apply_regex(value, regex)

        return value

    def find_next_page(
        self,
        html: str,
        pagination_config: dict,
        base_url: str = "",
    ) -> str | None:
        """次ページのURLを取得する.

        Args:
            html: 現在のページのHTML
            pagination_config: ページネーション設定
            base_url: 相対URL解決用のベースURL

        Returns:
            次ページのURL、存在しない場合はNone
        """
        if not pagination_config.get("enabled", False):
            return None

        soup = BeautifulSoup(html, "html.parser")
        selector = pagination_config.get("selector", "")
        if not selector:
            return None

        next_element = soup.select_one(selector)
        if next_element is None:
            return None

        href = next_element.get("href", "")
        if not href:
            return None

        if base_url:
            href = resolve_url(base_url, href)

        return href
