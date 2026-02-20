"""出力設定タブ."""

import tkinter as tk
from datetime import datetime
from tkinter import filedialog, ttk

from core.utils import sanitize_filename


class OutputSettingsTab(ttk.Frame):
    """Excel出力に関する設定を行うタブ."""

    def __init__(self, parent):
        super().__init__(parent, padding=10)
        self._create_widgets()

    def _create_widgets(self):
        self.columnconfigure(0, weight=1)
        row = 0

        # --- 出力先 ---
        dir_frame = ttk.LabelFrame(self, text="出力先", padding=10)
        dir_frame.grid(row=row, column=0, sticky="ew", pady=(0, 10))
        dir_frame.columnconfigure(0, weight=1)

        ttk.Label(dir_frame, text="フォルダ:").grid(row=0, column=0, sticky="w")
        dir_inner = ttk.Frame(dir_frame)
        dir_inner.grid(row=1, column=0, sticky="ew")
        dir_inner.columnconfigure(0, weight=1)

        self.dir_entry = ttk.Entry(dir_inner, width=60)
        self.dir_entry.grid(row=0, column=0, sticky="ew")
        ttk.Button(dir_inner, text="参照", command=self._browse_dir).grid(
            row=0, column=1, padx=(5, 0)
        )

        row += 1

        # --- ファイル名テンプレート ---
        tmpl_frame = ttk.LabelFrame(self, text="ファイル名テンプレート", padding=10)
        tmpl_frame.grid(row=row, column=0, sticky="ew", pady=(0, 10))
        tmpl_frame.columnconfigure(0, weight=1)

        self.template_entry = ttk.Entry(tmpl_frame, width=50)
        self.template_entry.insert(0, "{profile_name}_{date}")
        self.template_entry.grid(row=0, column=0, sticky="ew")
        self.template_entry.bind("<KeyRelease>", self._update_preview)

        self.preview_label = ttk.Label(tmpl_frame, text="", foreground="gray")
        self.preview_label.grid(row=1, column=0, sticky="w", pady=(5, 0))

        ttk.Label(
            tmpl_frame,
            text="利用可能変数: {profile_name} {date} {datetime} {site}",
            foreground="gray",
        ).grid(row=2, column=0, sticky="w", pady=(2, 0))

        self._update_preview()

        row += 1

        # --- 書き込みモード ---
        mode_frame = ttk.LabelFrame(self, text="書き込みモード", padding=10)
        mode_frame.grid(row=row, column=0, sticky="ew", pady=(0, 10))

        self.write_mode_var = tk.StringVar(value="new")
        ttk.Radiobutton(
            mode_frame,
            text="新規作成（毎回新しいファイル）",
            variable=self.write_mode_var,
            value="new",
        ).grid(row=0, column=0, sticky="w")
        ttk.Radiobutton(
            mode_frame,
            text="追記（既存ファイルにデータを追加）",
            variable=self.write_mode_var,
            value="append",
        ).grid(row=1, column=0, sticky="w")
        ttk.Radiobutton(
            mode_frame,
            text="上書き（既存ファイルのデータを置換）",
            variable=self.write_mode_var,
            value="overwrite",
        ).grid(row=2, column=0, sticky="w")

        row += 1

        # --- 追加列 ---
        col_frame = ttk.LabelFrame(self, text="追加列", padding=10)
        col_frame.grid(row=row, column=0, sticky="ew", pady=(0, 10))

        self.add_timestamp_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            col_frame, text="取得日時列を追加", variable=self.add_timestamp_var
        ).grid(row=0, column=0, sticky="w")

        self.add_source_url_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            col_frame, text="ソースURL列を追加", variable=self.add_source_url_var
        ).grid(row=1, column=0, sticky="w")

        self.add_run_id_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            col_frame, text="実行IDを追加（バッチ識別用）", variable=self.add_run_id_var
        ).grid(row=2, column=0, sticky="w")

        row += 1

        # --- Excelフォーマット ---
        fmt_frame = ttk.LabelFrame(self, text="Excelフォーマット", padding=10)
        fmt_frame.grid(row=row, column=0, sticky="ew", pady=(0, 10))

        self.format_header_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            fmt_frame,
            text="ヘッダー行に書式設定（太字・背景色）",
            variable=self.format_header_var,
        ).grid(row=0, column=0, sticky="w")

        self.auto_width_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            fmt_frame, text="列幅を自動調整", variable=self.auto_width_var
        ).grid(row=1, column=0, sticky="w")

        self.add_log_sheet_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            fmt_frame,
            text="データシートとは別にログシートを追加",
            variable=self.add_log_sheet_var,
        ).grid(row=2, column=0, sticky="w")

    def _browse_dir(self):
        """出力フォルダを選択するダイアログを開く."""
        directory = filedialog.askdirectory(title="出力フォルダを選択")
        if directory:
            self.dir_entry.delete(0, tk.END)
            self.dir_entry.insert(0, directory)

    def _update_preview(self, event=None):
        """ファイル名プレビューを更新する."""
        template = self.template_entry.get()
        try:
            preview = template.format(
                profile_name="ニュース収集",
                date=datetime.now().strftime("%Y-%m-%d"),
                datetime=datetime.now().strftime("%Y%m%d_%H%M%S"),
                site="example",
            )
            self.preview_label.config(text=f"プレビュー: {preview}.xlsx")
        except (KeyError, ValueError):
            self.preview_label.config(text="プレビュー: （テンプレートエラー）")

    def load_from_profile(self, profile: dict):
        """プロファイルからフォームに値をロードする."""
        output = profile.get("output", {})

        self.dir_entry.delete(0, tk.END)
        self.dir_entry.insert(0, output.get("directory", "output"))

        self.template_entry.delete(0, tk.END)
        self.template_entry.insert(
            0, output.get("filename_template", "{profile_name}_{date}")
        )
        self._update_preview()

        self.write_mode_var.set(output.get("write_mode", "new"))
        self.add_timestamp_var.set(output.get("add_timestamp", True))
        self.add_source_url_var.set(output.get("add_source_url", True))
        self.add_run_id_var.set(output.get("add_run_id", False))
        self.format_header_var.set(output.get("format_header", True))
        self.auto_width_var.set(output.get("auto_column_width", True))
        self.add_log_sheet_var.set(output.get("add_log_sheet", False))

    def save_to_profile(self) -> dict:
        """フォームの値をプロファイル辞書として返す."""
        return {
            "output": {
                "directory": self.dir_entry.get().strip(),
                "filename_template": self.template_entry.get().strip(),
                "write_mode": self.write_mode_var.get(),
                "add_timestamp": self.add_timestamp_var.get(),
                "add_source_url": self.add_source_url_var.get(),
                "add_run_id": self.add_run_id_var.get(),
                "format_header": self.format_header_var.get(),
                "auto_column_width": self.auto_width_var.get(),
                "add_log_sheet": self.add_log_sheet_var.get(),
            }
        }
