"""HTTP通信モジュール."""

import logging
import time

import requests

logger = logging.getLogger(__name__)


class FetchError(Exception):
    """HTTP取得時のエラー."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class Fetcher:
    """HTTP GETリクエストを行うクラス."""

    def __init__(
        self,
        user_agent: str = "MyCompanyScraper/1.0",
        timeout: int = 30,
        encoding: str = "auto",
    ):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent})
        self.timeout = timeout
        self.encoding = encoding

    def get(
        self,
        url: str,
        headers: dict | None = None,
        auth: tuple | None = None,
    ) -> requests.Response:
        """単一のHTTP GETリクエストを実行する."""
        try:
            response = self.session.get(
                url,
                headers=headers,
                auth=auth,
                timeout=self.timeout,
            )
            response.raise_for_status()
            if self.encoding != "auto":
                response.encoding = self.encoding
            elif response.encoding is None:
                response.encoding = self._detect_encoding(response)
            return response
        except requests.exceptions.ConnectionError as e:
            raise FetchError(f"接続エラー: {e}") from e
        except requests.exceptions.Timeout as e:
            raise FetchError(f"タイムアウト: {e}") from e
        except requests.exceptions.HTTPError as e:
            raise FetchError(
                f"HTTPエラー: {e}",
                status_code=e.response.status_code if e.response else None,
            ) from e

    def get_with_retry(
        self,
        url: str,
        max_retries: int = 3,
        wait_seconds: float = 2.0,
        headers: dict | None = None,
        auth: tuple | None = None,
    ) -> requests.Response:
        """リトライ付きでHTTP GETリクエストを実行する."""
        last_error = None
        for attempt in range(max_retries + 1):
            try:
                return self.get(url, headers=headers, auth=auth)
            except FetchError as e:
                last_error = e
                if e.status_code and 400 <= e.status_code < 500:
                    raise
                if attempt < max_retries:
                    logger.warning(
                        "リトライ %d/%d（%s）: %s",
                        attempt + 1,
                        max_retries,
                        type(e).__name__,
                        url,
                    )
                    time.sleep(wait_seconds)
        raise last_error  # type: ignore[misc]

    def _detect_encoding(self, response: requests.Response) -> str:
        """レスポンスからエンコーディングを推定する."""
        content_type = response.headers.get("Content-Type", "")
        if "charset=" in content_type:
            return content_type.split("charset=")[-1].strip()
        if response.apparent_encoding:
            return response.apparent_encoding
        return "utf-8"

    def close(self):
        """セッションを閉じる."""
        self.session.close()
