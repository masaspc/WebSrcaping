"""Webスクレイピングツール - エントリーポイント."""

import logging
import sys
from pathlib import Path

import yaml


def setup_logging(log_dir: str = "logs", log_level: str = "INFO"):
    """ロギングの初期設定を行う."""
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(
                log_path / "scraper.log", encoding="utf-8"
            ),
            logging.StreamHandler(sys.stdout),
        ],
    )


def load_app_config() -> dict:
    """アプリケーション設定ファイルを読み込む."""
    config_path = Path("app_config.yaml")
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


def main():
    """アプリケーションのメインエントリーポイント."""
    app_config = load_app_config()
    app_settings = app_config.get("app", {})

    setup_logging(
        log_dir=app_settings.get("log_dir", "logs"),
        log_level=app_settings.get("log_level", "INFO"),
    )

    logger = logging.getLogger(__name__)
    logger.info("Webスクレイピングツール 起動")

    # ディレクトリ作成
    for dir_name in ["config", "output", "logs"]:
        Path(dir_name).mkdir(parents=True, exist_ok=True)

    from gui.main_window import MainWindow

    window = MainWindow(app_config=app_config)
    window.run()

    logger.info("Webスクレイピングツール 終了")


if __name__ == "__main__":
    main()
