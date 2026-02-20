"""基本設定タブ."""

import tkinter as tk
from tkinter import ttk

from core.utils import is_valid_url


class BasicSettingsTab(ttk.Frame):
    """スクレイピングの基本設定を行うタブ."""

    def __init__(self, parent):
        super().__init__(parent, padding=10)
        self._create_widgets()

    def _create_widgets(self):
        row = 0

        # --- ターゲットURL ---
        url_frame = ttk.LabelFrame(self, text="ターゲットURL", padding=10)
        url_frame.grid(row=row, column=0, sticky="ew", pady=(0, 10))
        self.columnconfigure(0, weight=1)

        self.url_mode_var = tk.StringVar(value="single")
        ttk.Radiobutton(
            url_frame, text="単一URL", variable=self.url_mode_var, value="single"
        ).grid(row=0, column=0, sticky="w")

        self.url_entry = ttk.Entry(url_frame, width=60)
        self.url_entry.grid(row=0, column=1, sticky="ew", padx=5)

        self.validate_btn = ttk.Button(url_frame, text="検証", command=self._validate_url)
        self.validate_btn.grid(row=0, column=2, padx=5)

        ttk.Radiobutton(
            url_frame, text="URLリスト", variable=self.url_mode_var, value="list"
        ).grid(row=1, column=0, sticky="w", pady=(5, 0))

        self.url_file_entry = ttk.Entry(url_frame, width=60)
        self.url_file_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=(5, 0))

        self.url_file_btn = ttk.Button(url_frame, text="参照...", command=self._browse_url_file)
        self.url_file_btn.grid(row=1, column=2, padx=5, pady=(5, 0))

        url_frame.columnconfigure(1, weight=1)

        row += 1

        # --- スクレイピングエンジン ---
        engine_frame = ttk.LabelFrame(self, text="スクレイピングエンジン", padding=10)
        engine_frame.grid(row=row, column=0, sticky="ew", pady=(0, 10))

        self.engine_var = tk.StringVar(value="requests")
        ttk.Radiobutton(
            engine_frame, text="requests（静的HTML）", variable=self.engine_var, value="requests"
        ).grid(row=0, column=0, sticky="w")
        ttk.Radiobutton(
            engine_frame, text="Playwright（JS描画対応）", variable=self.engine_var, value="playwright"
        ).grid(row=0, column=1, sticky="w", padx=(20, 0))

        row += 1

        # --- リクエスト設定 ---
        req_frame = ttk.LabelFrame(self, text="リクエスト設定", padding=10)
        req_frame.grid(row=row, column=0, sticky="ew", pady=(0, 10))

        ttk.Label(req_frame, text="待機秒数:").grid(row=0, column=0, sticky="w")
        self.wait_var = tk.StringVar(value="2")
        ttk.Entry(req_frame, textvariable=self.wait_var, width=8).grid(
            row=0, column=1, sticky="w", padx=5
        )
        ttk.Label(req_frame, text="秒（リクエスト間隔）").grid(row=0, column=2, sticky="w")

        ttk.Label(req_frame, text="タイムアウト:").grid(row=1, column=0, sticky="w", pady=(5, 0))
        self.timeout_var = tk.StringVar(value="30")
        ttk.Entry(req_frame, textvariable=self.timeout_var, width=8).grid(
            row=1, column=1, sticky="w", padx=5, pady=(5, 0)
        )
        ttk.Label(req_frame, text="秒").grid(row=1, column=2, sticky="w", pady=(5, 0))

        ttk.Label(req_frame, text="リトライ回数:").grid(row=2, column=0, sticky="w", pady=(5, 0))
        self.retries_var = tk.StringVar(value="3")
        ttk.Entry(req_frame, textvariable=self.retries_var, width=8).grid(
            row=2, column=1, sticky="w", padx=5, pady=(5, 0)
        )

        ttk.Label(req_frame, text="エンコーディング:").grid(row=3, column=0, sticky="w", pady=(5, 0))
        self.encoding_var = tk.StringVar(value="自動検出")
        encoding_combo = ttk.Combobox(
            req_frame,
            textvariable=self.encoding_var,
            values=["自動検出", "utf-8", "shift_jis", "euc-jp"],
            state="readonly",
            width=15,
        )
        encoding_combo.grid(row=3, column=1, columnspan=2, sticky="w", padx=5, pady=(5, 0))

        row += 1

        # --- User-Agent ---
        ua_frame = ttk.LabelFrame(self, text="User-Agent", padding=10)
        ua_frame.grid(row=row, column=0, sticky="ew", pady=(0, 10))

        self.ua_entry = ttk.Entry(ua_frame, width=60)
        self.ua_entry.insert(0, "MyCompanyScraper/1.0")
        self.ua_entry.grid(row=0, column=0, sticky="ew")
        ua_frame.columnconfigure(0, weight=1)

        row += 1

        # --- robots.txt ---
        self.robots_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            self, text="robots.txt を遵守する（推奨）", variable=self.robots_var
        ).grid(row=row, column=0, sticky="w", pady=(0, 10))

        row += 1

        # --- 認証（オプション） ---
        auth_frame = ttk.LabelFrame(self, text="認証（オプション）", padding=10)
        auth_frame.grid(row=row, column=0, sticky="ew", pady=(0, 10))

        ttk.Label(auth_frame, text="認証方式:").grid(row=0, column=0, sticky="w")
        self.auth_type_var = tk.StringVar(value="なし")
        ttk.Combobox(
            auth_frame,
            textvariable=self.auth_type_var,
            values=["なし", "Basic認証", "Cookie"],
            state="readonly",
            width=15,
        ).grid(row=0, column=1, sticky="w", padx=5)

        ttk.Label(auth_frame, text="ユーザー名:").grid(row=1, column=0, sticky="w", pady=(5, 0))
        self.username_entry = ttk.Entry(auth_frame, width=30)
        self.username_entry.grid(row=1, column=1, sticky="w", padx=5, pady=(5, 0))

        ttk.Label(auth_frame, text="パスワード:").grid(row=2, column=0, sticky="w", pady=(5, 0))
        self.password_entry = ttk.Entry(auth_frame, width=30, show="*")
        self.password_entry.grid(row=2, column=1, sticky="w", padx=5, pady=(5, 0))

    def _validate_url(self):
        """URLの形式を検証してフィードバックを表示する."""
        url = self.url_entry.get().strip()
        if is_valid_url(url):
            self.validate_btn.config(text="OK")
            self.after(2000, lambda: self.validate_btn.config(text="検証"))
        else:
            self.validate_btn.config(text="無効")
            self.after(2000, lambda: self.validate_btn.config(text="検証"))

    def _browse_url_file(self):
        """URLリストファイルを選択するダイアログを開く."""
        from tkinter import filedialog

        filepath = filedialog.askopenfilename(
            title="URLリストファイルを選択",
            filetypes=[
                ("CSVファイル", "*.csv"),
                ("Excelファイル", "*.xlsx"),
                ("テキストファイル", "*.txt"),
                ("すべてのファイル", "*.*"),
            ],
        )
        if filepath:
            self.url_file_entry.delete(0, tk.END)
            self.url_file_entry.insert(0, filepath)

    def load_from_profile(self, profile: dict):
        """プロファイルからフォームに値をロードする."""
        target = profile.get("target", {})
        self.url_mode_var.set(target.get("mode", "single"))
        self.url_entry.delete(0, tk.END)
        self.url_entry.insert(0, target.get("url", ""))
        self.url_file_entry.delete(0, tk.END)
        self.url_file_entry.insert(0, target.get("url_file", ""))

        engine = profile.get("engine", {})
        self.engine_var.set(engine.get("type", "requests"))
        self.wait_var.set(str(engine.get("wait_seconds", 2)))
        self.timeout_var.set(str(engine.get("timeout", 30)))
        self.retries_var.set(str(engine.get("max_retries", 3)))

        enc = engine.get("encoding", "auto")
        self.encoding_var.set("自動検出" if enc == "auto" else enc)

        self.ua_entry.delete(0, tk.END)
        self.ua_entry.insert(0, engine.get("user_agent", "MyCompanyScraper/1.0"))
        self.robots_var.set(engine.get("respect_robots_txt", True))

        auth = profile.get("authentication", {})
        auth_type = auth.get("type", "none")
        type_map = {"none": "なし", "basic": "Basic認証", "cookie": "Cookie"}
        self.auth_type_var.set(type_map.get(auth_type, "なし"))
        self.username_entry.delete(0, tk.END)
        self.username_entry.insert(0, auth.get("username", ""))
        self.password_entry.delete(0, tk.END)
        self.password_entry.insert(0, auth.get("password", ""))

    def save_to_profile(self) -> dict:
        """フォームの値をプロファイル辞書として返す."""
        enc = self.encoding_var.get()
        if enc == "自動検出":
            enc = "auto"

        auth_type = self.auth_type_var.get()
        auth_map = {"なし": "none", "Basic認証": "basic", "Cookie": "cookie"}

        return {
            "target": {
                "mode": self.url_mode_var.get(),
                "url": self.url_entry.get().strip(),
                "url_file": self.url_file_entry.get().strip(),
            },
            "engine": {
                "type": self.engine_var.get(),
                "encoding": enc,
                "wait_seconds": int(self.wait_var.get() or 2),
                "timeout": int(self.timeout_var.get() or 30),
                "max_retries": int(self.retries_var.get() or 3),
                "respect_robots_txt": self.robots_var.get(),
                "user_agent": self.ua_entry.get().strip(),
            },
            "authentication": {
                "type": auth_map.get(auth_type, "none"),
                "username": self.username_entry.get(),
                "password": self.password_entry.get(),
            },
        }

    def validate(self) -> list[str]:
        """入力値のバリデーションを行う."""
        errors = []
        if self.url_mode_var.get() == "single":
            url = self.url_entry.get().strip()
            if not url:
                errors.append("ターゲットURLが未入力です")
            elif not is_valid_url(url):
                errors.append("URLの形式が正しくありません")
        else:
            if not self.url_file_entry.get().strip():
                errors.append("URLリストファイルが未指定です")

        try:
            wait = int(self.wait_var.get())
            if wait < 0:
                errors.append("待機秒数は0以上を指定してください")
        except ValueError:
            errors.append("待機秒数には数値を入力してください")

        try:
            timeout = int(self.timeout_var.get())
            if timeout <= 0:
                errors.append("タイムアウトは1以上を指定してください")
        except ValueError:
            errors.append("タイムアウトには数値を入力してください")

        return errors
