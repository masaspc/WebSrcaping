"""実行ログタブ."""

import tkinter as tk
from datetime import datetime
from tkinter import filedialog, scrolledtext, ttk


class LogViewerTab(ttk.Frame):
    """実行ログの表示・管理を行うタブ."""

    def __init__(self, parent, max_lines: int = 1000):
        super().__init__(parent, padding=10)
        self.max_lines = max_lines
        self.log_entries: list[dict] = []
        self._create_widgets()

    def _create_widgets(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # --- ツールバー ---
        toolbar = ttk.Frame(self)
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 5))

        ttk.Button(toolbar, text="クリア", command=self.clear_log).pack(
            side="left", padx=(0, 5)
        )
        ttk.Button(toolbar, text="ファイルに保存", command=self.save_log_to_file).pack(
            side="left", padx=(0, 5)
        )

        ttk.Label(toolbar, text="フィルタ:").pack(side="right", padx=(5, 5))
        self.filter_var = tk.StringVar(value="すべて")
        filter_combo = ttk.Combobox(
            toolbar,
            textvariable=self.filter_var,
            values=["すべて", "INFO", "WARN", "ERROR"],
            state="readonly",
            width=10,
        )
        filter_combo.pack(side="right")
        filter_combo.bind("<<ComboboxSelected>>", self._apply_filter)

        # --- ログテキスト ---
        self.log_text = scrolledtext.ScrolledText(
            self,
            wrap="word",
            state="disabled",
            font=("Consolas", 9),
            bg="#1e1e1e",
            fg="#d4d4d4",
        )
        self.log_text.grid(row=1, column=0, sticky="nsew")

        # タグ定義（色分け）
        self.log_text.tag_configure("INFO", foreground="#4ec9b0")
        self.log_text.tag_configure("WARN", foreground="#dcdcaa")
        self.log_text.tag_configure("ERROR", foreground="#f44747")

        # --- サマリー ---
        summary_frame = ttk.LabelFrame(self, text="実行サマリー", padding=5)
        summary_frame.grid(row=2, column=0, sticky="ew", pady=(5, 0))

        self.summary_label = ttk.Label(summary_frame, text="待機中")
        self.summary_label.pack(fill="x")

    def append_log(self, level: str, message: str, timestamp: str | None = None):
        """ログエントリを追加する."""
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        entry = {"timestamp": timestamp, "level": level, "message": message}
        self.log_entries.append(entry)

        # フィルタチェック
        current_filter = self.filter_var.get()
        if current_filter != "すべて" and level != current_filter:
            return

        self._insert_log_line(entry)

    def _insert_log_line(self, entry: dict):
        """ログ行をテキストウィジェットに挿入する."""
        line = f"{entry['timestamp']} [{entry['level']}]  {entry['message']}\n"

        self.log_text.configure(state="normal")
        self.log_text.insert("end", line, entry["level"])
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

        # 最大行数を超えたら古い行を削除
        line_count = int(self.log_text.index("end-1c").split(".")[0])
        if line_count > self.max_lines:
            self.log_text.configure(state="normal")
            self.log_text.delete("1.0", "2.0")
            self.log_text.configure(state="disabled")

    def clear_log(self):
        """ログをクリアする."""
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")
        self.log_entries.clear()
        self.summary_label.config(text="待機中")

    def save_log_to_file(self):
        """ログをファイルに保存する."""
        filepath = filedialog.asksaveasfilename(
            title="ログを保存",
            defaultextension=".log",
            filetypes=[("ログファイル", "*.log"), ("テキストファイル", "*.txt")],
            initialfile=f"scraper_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
        )
        if not filepath:
            return

        with open(filepath, "w", encoding="utf-8") as f:
            for entry in self.log_entries:
                f.write(
                    f"{entry['timestamp']} [{entry['level']}]  {entry['message']}\n"
                )

    def update_summary(
        self,
        pages: int = 0,
        total: int = 0,
        errors: int = 0,
        elapsed: str = "",
        file_size: str = "",
    ):
        """実行サマリーを更新する."""
        parts = []
        parts.append(f"取得ページ数: {pages}")
        parts.append(f"抽出データ: {total}件")
        parts.append(f"エラー: {errors}件")
        if elapsed:
            parts.append(f"所要時間: {elapsed}")
        if file_size:
            parts.append(f"出力ファイルサイズ: {file_size}")
        self.summary_label.config(text="  |  ".join(parts))

    def _apply_filter(self, event=None):
        """ログフィルタを適用してテキストを再描画する."""
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")

        current_filter = self.filter_var.get()
        for entry in self.log_entries:
            if current_filter == "すべて" or entry["level"] == current_filter:
                self._insert_log_line(entry)
