"""スクレイピング実行制御モジュール."""

import logging
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Callable

from core.excel_exporter import ExcelExporter
from core.fetcher import FetchError, Fetcher
from core.parser import Parser
from core.robots_checker import RobotsChecker
from core.utils import sanitize_filename

logger = logging.getLogger(__name__)


class ScraperEngine:
    """スクレイピングの実行を制御するクラス.

    GUIのメインスレッドからrun()を呼び出すと、ワーカースレッドで
    スクレイピング処理を実行する。進捗やログはコールバック経由で通知する。
    """

    def __init__(self):
        self.is_running: bool = False
        self.should_stop: threading.Event = threading.Event()
        self.progress_callback: Callable | None = None
        self.log_callback: Callable | None = None
        self._thread: threading.Thread | None = None

    def run(
        self,
        profile: dict,
        progress_callback: Callable | None = None,
        log_callback: Callable | None = None,
    ):
        """ワーカースレッドでスクレイピングを開始する."""
        if self.is_running:
            return

        self.should_stop.clear()
        self.progress_callback = progress_callback
        self.log_callback = log_callback

        self._thread = threading.Thread(
            target=self._execute,
            args=(profile,),
            daemon=True,
        )
        self._thread.start()

    def stop(self):
        """停止要求を出す."""
        self.should_stop.set()
        self._log("INFO", "停止要求を受信しました")

    def _execute(self, profile: dict):
        """ワーカースレッドで実行されるメインロジック."""
        self.is_running = True
        all_data: list[dict] = []
        log_entries: list[dict] = []
        start_time = time.time()

        try:
            self._log("INFO", f"実行開始: {profile.get('profile_name', '不明')}")

            engine_config = profile.get("engine", {})
            target = profile.get("target", {})
            selectors = profile.get("selectors", {})
            pagination = profile.get("pagination", {})
            output_config = profile.get("output", {})
            auth_config = profile.get("authentication", {})

            # Fetcher初期化
            fetcher = Fetcher(
                user_agent=engine_config.get("user_agent", "MyCompanyScraper/1.0"),
                timeout=engine_config.get("timeout", 30),
                encoding=engine_config.get("encoding", "auto"),
            )
            parser = Parser()
            exporter = ExcelExporter()

            # 認証設定
            auth = None
            if auth_config.get("type") == "basic":
                auth = (auth_config.get("username", ""), auth_config.get("password", ""))

            # robots.txt チェック
            url = target.get("url", "")
            if engine_config.get("respect_robots_txt", True):
                self._log("INFO", "robots.txt チェック中...")
                checker = RobotsChecker()
                if not checker.can_fetch(url, engine_config.get("user_agent", "*")):
                    self._log("WARN", f"robots.txt によりアクセスが拒否されています: {url}")
                    self._progress("robots_blocked", url=url)
                    return
                self._log("INFO", "robots.txt チェック: OK")

                crawl_delay = checker.get_crawl_delay(
                    url, engine_config.get("user_agent", "*")
                )
                if crawl_delay is not None:
                    wait = max(engine_config.get("wait_seconds", 2), crawl_delay)
                    engine_config["wait_seconds"] = wait
                    self._log("INFO", f"Crawl-Delay適用: {wait}秒")

            # ページ取得ループ
            max_pages = pagination.get("max_pages", 1) if pagination.get("enabled") else 1
            current_url = url
            page_count = 0
            error_count = 0

            while current_url and page_count < max_pages:
                if self.should_stop.is_set():
                    self._log("INFO", "ユーザーにより停止されました")
                    break

                page_count += 1
                self._log("INFO", f"ページ {page_count}/{max_pages} 取得中... {current_url}")
                self._progress("fetching", page=page_count, max_pages=max_pages)

                try:
                    response = fetcher.get_with_retry(
                        current_url,
                        max_retries=engine_config.get("max_retries", 3),
                        wait_seconds=engine_config.get("wait_seconds", 2),
                        auth=auth,
                    )
                    html = response.text
                except FetchError as e:
                    error_count += 1
                    self._log("ERROR", f"ページ取得失敗: {e}")
                    if e.status_code and e.status_code < 500:
                        break
                    current_url = None
                    continue

                # データ抽出
                page_data = parser.parse(
                    html,
                    selectors.get("container", ""),
                    selectors.get("fields", []),
                    base_url=current_url,
                )

                if not page_data:
                    self._log("WARN", "このページからデータを抽出できませんでした")

                # 追加列の付与
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                for row in page_data:
                    if output_config.get("add_timestamp", True):
                        row["取得日時"] = now_str
                    if output_config.get("add_source_url", True):
                        row["ソースURL"] = current_url

                all_data.extend(page_data)
                self._log("INFO", f"→ {len(page_data)}件のデータを抽出")

                # 次ページ判定
                if pagination.get("enabled"):
                    current_url = parser.find_next_page(html, pagination, base_url=current_url)
                else:
                    current_url = None

                # 待機
                if current_url:
                    wait = engine_config.get("wait_seconds", 2)
                    time.sleep(wait)

            # Excel出力
            if all_data:
                filepath = self._build_output_path(profile)
                write_mode = output_config.get("write_mode", "new")

                options = {
                    "format_header": output_config.get("format_header", True),
                    "auto_column_width": output_config.get("auto_column_width", True),
                }

                if write_mode == "append" and Path(filepath).exists():
                    headers = list(all_data[0].keys())
                    result_path = exporter.append(filepath, all_data, headers)
                else:
                    headers = list(all_data[0].keys())
                    result_path = exporter.create(filepath, all_data, headers, options)

                self._log("INFO", f"出力: {result_path}")
            else:
                self._log("WARN", "抽出データが0件のため、Excel出力をスキップしました")

            # 完了サマリー
            elapsed = time.time() - start_time
            minutes = int(elapsed // 60)
            seconds = int(elapsed % 60)
            self._log(
                "INFO",
                f"完了: 合計{len(all_data)}件 | "
                f"ページ数: {page_count} | エラー: {error_count}件 | "
                f"所要時間: {minutes}分{seconds}秒",
            )
            self._progress(
                "completed",
                total=len(all_data),
                pages=page_count,
                errors=error_count,
            )

        except Exception as e:
            self._log("ERROR", f"予期せぬエラー: {e}")
            logger.exception("スクレイピング実行中の例外")
            # 取得済みデータがあれば保存を試みる
            if all_data:
                try:
                    filepath = self._build_output_path(profile)
                    exporter = ExcelExporter()
                    headers = list(all_data[0].keys())
                    exporter.create(filepath, all_data, headers)
                    self._log("INFO", f"エラー発生前のデータを保存: {filepath}")
                except Exception:
                    self._log("ERROR", "データの緊急保存にも失敗しました")
            self._progress("error", message=str(e))
        finally:
            self.is_running = False
            try:
                fetcher.close()
            except Exception:
                pass

    def _build_output_path(self, profile: dict) -> str:
        """出力ファイルパスを組み立てる."""
        output_config = profile.get("output", {})
        directory = output_config.get("directory", "output")
        template = output_config.get("filename_template", "{profile_name}_{date}")

        filename = template.format(
            profile_name=sanitize_filename(profile.get("profile_name", "data")),
            date=datetime.now().strftime("%Y-%m-%d"),
            datetime=datetime.now().strftime("%Y%m%d_%H%M%S"),
            site="",
        )

        path = Path(directory) / f"{filename}.xlsx"
        path.parent.mkdir(parents=True, exist_ok=True)
        return str(path)

    def _log(self, level: str, message: str):
        """ログコールバックに通知する."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = {"timestamp": timestamp, "level": level, "message": message}

        log_func = getattr(logger, level.lower(), logger.info)
        log_func(message)

        if self.log_callback:
            self.log_callback(log_entry)

    def _progress(self, status: str, **kwargs):
        """進捗コールバックに通知する."""
        if self.progress_callback:
            self.progress_callback(status, **kwargs)
