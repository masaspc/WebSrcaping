"""プロファイル管理モジュール."""

import logging
import shutil
from datetime import datetime
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

DEFAULT_PROFILE = {
    "profile_name": "",
    "description": "",
    "created_at": "",
    "updated_at": "",
    "target": {
        "mode": "single",
        "url": "",
        "url_file": "",
    },
    "engine": {
        "type": "requests",
        "encoding": "auto",
        "wait_seconds": 2,
        "timeout": 30,
        "max_retries": 3,
        "respect_robots_txt": True,
        "user_agent": "MyCompanyScraper/1.0",
    },
    "authentication": {
        "type": "none",
        "username": "",
        "password": "",
    },
    "selectors": {
        "container": "",
        "fields": [],
    },
    "pagination": {
        "enabled": False,
        "type": "next_button",
        "selector": "",
        "max_pages": 10,
    },
    "output": {
        "directory": "",
        "filename_template": "{profile_name}_{date}",
        "write_mode": "new",
        "add_timestamp": True,
        "add_source_url": True,
        "add_run_id": False,
        "format_header": True,
        "auto_column_width": True,
        "add_log_sheet": False,
    },
}


class ProfileManager:
    """スクレイピングプロファイルのCRUD管理を行うクラス."""

    def __init__(self, config_dir: str | Path = "config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.profiles: dict[str, dict] = {}

    def load_all(self) -> dict[str, dict]:
        """config_dir内の全YAMLプロファイルを読み込む."""
        self.profiles.clear()
        for yaml_file in sorted(self.config_dir.glob("*.yaml")):
            if yaml_file.name.startswith("_"):
                continue
            try:
                with open(yaml_file, "r", encoding="utf-8") as f:
                    profile = yaml.safe_load(f)
                if profile and isinstance(profile, dict):
                    name = profile.get("profile_name", yaml_file.stem)
                    self.profiles[name] = profile
            except Exception as e:
                logger.error("プロファイル読み込みエラー: %s (%s)", yaml_file, e)
        return self.profiles

    def load(self, name: str) -> dict:
        """指定されたプロファイルを返す."""
        if name in self.profiles:
            return self.profiles[name]
        # ファイルから直接読み込みを試みる
        yaml_file = self._name_to_path(name)
        if yaml_file.exists():
            with open(yaml_file, "r", encoding="utf-8") as f:
                profile = yaml.safe_load(f)
            if profile:
                self.profiles[name] = profile
                return profile
        raise KeyError(f"プロファイルが見つかりません: {name}")

    def save(self, name: str, profile: dict):
        """プロファイルをYAMLファイルに保存する."""
        now = datetime.now().isoformat(timespec="seconds")
        profile["updated_at"] = now
        if not profile.get("created_at"):
            profile["created_at"] = now
        profile["profile_name"] = name

        yaml_file = self._name_to_path(name)
        with open(yaml_file, "w", encoding="utf-8") as f:
            yaml.dump(
                profile,
                f,
                allow_unicode=True,
                default_flow_style=False,
                sort_keys=False,
            )
        self.profiles[name] = profile
        logger.info("プロファイル保存: %s", yaml_file)

    def delete(self, name: str):
        """プロファイルを削除する."""
        yaml_file = self._name_to_path(name)
        if yaml_file.exists():
            yaml_file.unlink()
        self.profiles.pop(name, None)
        logger.info("プロファイル削除: %s", name)

    def duplicate(self, name: str, new_name: str):
        """プロファイルを複製する."""
        profile = self.load(name).copy()
        import copy

        profile = copy.deepcopy(profile)
        profile["profile_name"] = new_name
        profile["created_at"] = ""
        self.save(new_name, profile)
        logger.info("プロファイル複製: %s → %s", name, new_name)

    def list_profiles(self) -> list[str]:
        """プロファイル名の一覧を返す."""
        return list(self.profiles.keys())

    def create_new(self, name: str) -> dict:
        """デフォルト値で新規プロファイルを作成する."""
        import copy

        profile = copy.deepcopy(DEFAULT_PROFILE)
        profile["profile_name"] = name
        self.save(name, profile)
        return profile

    def validate(self, profile: dict) -> list[str]:
        """プロファイルのバリデーションを行い、エラーリストを返す."""
        errors = []

        # URL チェック
        target = profile.get("target", {})
        if target.get("mode") == "single":
            url = target.get("url", "").strip()
            if not url:
                errors.append("ターゲットURLが未入力です")
            elif not (url.startswith("http://") or url.startswith("https://")):
                errors.append("URLはhttp://またはhttps://で始まる必要があります")
        elif target.get("mode") == "list":
            url_file = target.get("url_file", "").strip()
            if not url_file:
                errors.append("URLリストファイルが未指定です")
            elif not Path(url_file).exists():
                errors.append(f"URLリストファイルが見つかりません: {url_file}")

        # セレクタチェック
        selectors = profile.get("selectors", {})
        if not selectors.get("container", "").strip():
            errors.append("コンテナセレクタが未入力です")
        if not selectors.get("fields"):
            errors.append("抽出フィールドが1つも定義されていません")

        # 出力チェック
        output = profile.get("output", {})
        if not output.get("directory", "").strip():
            errors.append("出力フォルダが未指定です")

        return errors

    def _name_to_path(self, name: str) -> Path:
        """プロファイル名からファイルパスを生成する."""
        safe_name = "".join(
            c if c.isalnum() or c in ("_", "-", "　") else "_" for c in name
        )
        return self.config_dir / f"{safe_name}.yaml"
