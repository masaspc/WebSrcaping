"""robots.txt チェックモジュール."""

import logging
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

logger = logging.getLogger(__name__)


class RobotsChecker:
    """robots.txt の遵守チェックを行うクラス."""

    def __init__(self):
        self._parsers: dict[str, RobotFileParser] = {}

    def _get_parser(self, url: str) -> RobotFileParser:
        """URLのドメインに対応するRobotFileParserを取得・キャッシュする."""
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

        if robots_url not in self._parsers:
            rp = RobotFileParser()
            rp.set_url(robots_url)
            try:
                rp.read()
            except Exception as e:
                logger.warning("robots.txt の読み込みに失敗: %s (%s)", robots_url, e)
                rp = RobotFileParser()
                rp.allow_all = True
            self._parsers[robots_url] = rp

        return self._parsers[robots_url]

    def can_fetch(self, url: str, user_agent: str = "*") -> bool:
        """指定URLへのアクセスが許可されているかチェックする."""
        try:
            parser = self._get_parser(url)
            return parser.can_fetch(user_agent, url)
        except Exception as e:
            logger.warning("robots.txt チェックでエラー: %s", e)
            return True

    def get_crawl_delay(self, url: str, user_agent: str = "*") -> float | None:
        """Crawl-Delay の値を取得する."""
        try:
            parser = self._get_parser(url)
            delay = parser.crawl_delay(user_agent)
            return float(delay) if delay is not None else None
        except Exception:
            return None
