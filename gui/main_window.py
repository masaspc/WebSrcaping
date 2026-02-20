"""メインウィンドウ."""

import os
import platform
import queue
import subprocess
import sys
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk

from controller.profile_manager import ProfileManager
from controller.scraper_engine import ScraperEngine
from gui.profile_pane import ProfilePane
from gui.tabs.basic_settings import BasicSettingsTab
from gui.tabs.log_viewer import LogViewerTab
from gui.tabs.output_settings import OutputSettingsTab
from gui.tabs.selector_settings import SelectorSettingsTab


class MainWindow:
    """アプリケーションのメインウィンドウ."""

    def __init__(self, app_config: dict | None = None):
        self.app_config = app_config or {}
        app_settings = self.app_config.get("app", {})

        self.root = tk.Tk()
        self.root.title("Webスクレイピングツール")
        self.root.geometry(
            f"{app_settings.get('window_width', 1200)}x"
            f"{app_settings.get('window_height', 800)}"
        )
        self.root.minsize(900, 600)

        # High DPI対応 (Windows)
        if platform.system() == "Windows":
            try:
                import ctypes
                ctypes.windll.shcore.SetProcessDpiAwareness(1)
            except Exception:
                pass

        # テーマ設定
        style = ttk.Style()
        theme = app_settings.get("theme", "clam")
        if theme in style.theme_names():
            style.theme_use(theme)

        # コンポーネント初期化
        config_dir = app_settings.get("config_dir", "config")
        self.profile_manager = ProfileManager(config_dir=config_dir)
        self.scraper_engine = ScraperEngine()
        self.current_profile: str | None = None

        # スレッド間通信キュー
        self._queue: queue.Queue = queue.Queue()

        # UI構築
        self._create_menu_bar()
        self._create_main_layout()
        self._create_status_bar()

        # プロファイル読み込み
        self._load_profiles()

        # キュー監視開始
        self._poll_queue()

    def _create_menu_bar(self):
        """メニューバーを構築する."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # ファイルメニュー
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(
            label="プロファイルを保存", command=self._save_current_profile
        )
        file_menu.add_separator()
        file_menu.add_command(label="終了", command=self._on_close)
        menubar.add_cascade(label="ファイル", menu=file_menu)

        # プロファイルメニュー
        profile_menu = tk.Menu(menubar, tearoff=0)
        profile_menu.add_command(label="新規作成", command=self._new_profile_from_menu)
        profile_menu.add_command(label="すべて再読込", command=self._load_profiles)
        menubar.add_cascade(label="プロファイル", menu=profile_menu)

        # ヘルプメニュー
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="バージョン情報", command=self._show_about)
        menubar.add_cascade(label="ヘルプ", menu=help_menu)

    def _create_main_layout(self):
        """メインレイアウト（左ペイン + 右ペイン）を構築する."""
        # PanedWindow で左右分割
        paned = ttk.PanedWindow(self.root, orient="horizontal")
        paned.pack(fill="both", expand=True, padx=5, pady=5)

        # 左ペイン: プロファイルリスト
        self.profile_pane = ProfilePane(
            paned,
            on_select=self._on_profile_selected,
            on_new=self._on_profile_new,
            on_delete=self._on_profile_delete,
            on_duplicate=self._on_profile_duplicate,
        )
        paned.add(self.profile_pane, weight=0)

        # 右ペイン
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=1)
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(0, weight=1)

        # タブノートブック
        self.notebook = ttk.Notebook(right_frame)
        self.notebook.grid(row=0, column=0, sticky="nsew")

        self.basic_tab = BasicSettingsTab(self.notebook)
        self.selector_tab = SelectorSettingsTab(self.notebook)
        self.output_tab = OutputSettingsTab(self.notebook)
        self.log_tab = LogViewerTab(
            self.notebook,
            max_lines=self.app_config.get("app", {}).get("max_log_lines", 1000),
        )

        self.notebook.add(self.basic_tab, text="基本設定")
        self.notebook.add(self.selector_tab, text="セレクタ設定")
        self.notebook.add(self.output_tab, text="出力設定")
        self.notebook.add(self.log_tab, text="実行ログ")

        # ボタンバー
        btn_bar = ttk.Frame(right_frame)
        btn_bar.grid(row=1, column=0, sticky="ew", pady=(5, 0))

        self.run_btn = ttk.Button(
            btn_bar, text="▶ 実行", command=self._on_run_clicked
        )
        self.run_btn.pack(side="left", padx=(0, 5))

        self.stop_btn = ttk.Button(
            btn_bar, text="■ 停止", command=self._on_stop_clicked, state="disabled"
        )
        self.stop_btn.pack(side="left", padx=(0, 5))

        ttk.Button(
            btn_bar, text="出力フォルダを開く", command=self._open_output_dir
        ).pack(side="left", padx=(0, 5))

        ttk.Button(
            btn_bar, text="保存", command=self._save_current_profile
        ).pack(side="right")

    def _create_status_bar(self):
        """ステータスバーを構築する."""
        status_frame = ttk.Frame(self.root, relief="sunken")
        status_frame.pack(fill="x", side="bottom", padx=5, pady=(0, 5))

        self.status_label = ttk.Label(status_frame, text="Ready")
        self.status_label.pack(side="left", padx=5)

        self.last_run_label = ttk.Label(status_frame, text="")
        self.last_run_label.pack(side="left", padx=20)

        self.profile_count_label = ttk.Label(status_frame, text="")
        self.profile_count_label.pack(side="right", padx=5)

        # プログレスバー
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(
            status_frame, variable=self.progress_var, maximum=100, length=200
        )
        self.progress_bar.pack(side="right", padx=10)

    def _load_profiles(self):
        """全プロファイルを読み込み、リストを更新する."""
        self.profile_manager.load_all()
        names = self.profile_manager.list_profiles()
        self.profile_pane.set_profiles(names)
        self.profile_count_label.config(text=f"プロファイル: {len(names)}件")

    def _on_profile_selected(self, name: str):
        """プロファイル選択イベント."""
        # 現在のプロファイルを自動保存
        if self.current_profile:
            self._save_current_profile(silent=True)

        try:
            profile = self.profile_manager.load(name)
            self.current_profile = name
            self.basic_tab.load_from_profile(profile)
            self.selector_tab.load_from_profile(profile)
            self.output_tab.load_from_profile(profile)
            self.update_status(f"プロファイル「{name}」を読み込みました")
        except Exception as e:
            messagebox.showerror("エラー", f"プロファイルの読み込みに失敗しました:\n{e}")

    def _on_profile_new(self, name: str):
        """新規プロファイル作成."""
        try:
            self.profile_manager.create_new(name)
            self._load_profiles()
            self.profile_pane.select_by_name(name)
            self._on_profile_selected(name)
        except Exception as e:
            messagebox.showerror("エラー", f"プロファイルの作成に失敗しました:\n{e}")

    def _on_profile_delete(self, name: str):
        """プロファイル削除."""
        try:
            self.profile_manager.delete(name)
            self.current_profile = None
            self._load_profiles()
        except Exception as e:
            messagebox.showerror("エラー", f"プロファイルの削除に失敗しました:\n{e}")

    def _on_profile_duplicate(self, name: str, new_name: str):
        """プロファイル複製."""
        try:
            self.profile_manager.duplicate(name, new_name)
            self._load_profiles()
            self.profile_pane.select_by_name(new_name)
            self._on_profile_selected(new_name)
        except Exception as e:
            messagebox.showerror("エラー", f"プロファイルの複製に失敗しました:\n{e}")

    def _save_current_profile(self, silent: bool = False):
        """現在のプロファイルを保存する."""
        if not self.current_profile:
            if not silent:
                messagebox.showwarning("警告", "プロファイルが選択されていません")
            return

        profile = {}
        profile.update(self.basic_tab.save_to_profile())
        profile.update(self.selector_tab.save_to_profile())
        profile.update(self.output_tab.save_to_profile())

        try:
            self.profile_manager.save(self.current_profile, profile)
            if not silent:
                self.update_status(f"プロファイル「{self.current_profile}」を保存しました")
        except Exception as e:
            if not silent:
                messagebox.showerror("エラー", f"保存に失敗しました:\n{e}")

    def _new_profile_from_menu(self):
        """メニューから新規プロファイル作成."""
        from tkinter import simpledialog

        name = simpledialog.askstring(
            "新規プロファイル",
            "プロファイル名を入力してください:",
            parent=self.root,
        )
        if name and name.strip():
            self._on_profile_new(name.strip())

    def _on_run_clicked(self):
        """実行ボタンのクリックイベント."""
        if not self.current_profile:
            messagebox.showwarning("警告", "プロファイルを選択してください")
            return

        # 現在の設定を保存してからバリデーション
        self._save_current_profile(silent=True)

        profile = self.profile_manager.load(self.current_profile)
        errors = self.profile_manager.validate(profile)
        if errors:
            messagebox.showerror(
                "バリデーションエラー",
                "以下のエラーを修正してください:\n\n" + "\n".join(f"・{e}" for e in errors),
            )
            return

        # UI状態更新
        self.run_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.log_tab.clear_log()
        self.progress_var.set(0)
        self.notebook.select(self.log_tab)

        # スクレイピング開始
        self.scraper_engine.run(
            profile,
            progress_callback=self._on_progress,
            log_callback=self._on_log,
        )
        self.update_status("実行中...")

    def _on_stop_clicked(self):
        """停止ボタンのクリックイベント."""
        self.scraper_engine.stop()

    def _on_progress(self, status: str, **kwargs):
        """進捗コールバック（ワーカースレッドから呼ばれる）."""
        self._queue.put(("progress", status, kwargs))

    def _on_log(self, entry: dict):
        """ログコールバック（ワーカースレッドから呼ばれる）."""
        self._queue.put(("log", entry))

    def _poll_queue(self):
        """キューからメッセージを取り出してUIを更新する."""
        try:
            while True:
                msg = self._queue.get_nowait()
                msg_type = msg[0]

                if msg_type == "log":
                    entry = msg[1]
                    self.log_tab.append_log(
                        entry.get("level", "INFO"),
                        entry.get("message", ""),
                        entry.get("timestamp"),
                    )

                elif msg_type == "progress":
                    status = msg[1]
                    data = msg[2]

                    if status == "fetching":
                        page = data.get("page", 0)
                        max_pages = data.get("max_pages", 1)
                        if max_pages > 0:
                            self.progress_var.set((page / max_pages) * 100)

                    elif status == "completed":
                        self.progress_var.set(100)
                        self.run_btn.config(state="normal")
                        self.stop_btn.config(state="disabled")
                        total = data.get("total", 0)
                        pages = data.get("pages", 0)
                        errors = data.get("errors", 0)
                        self.log_tab.update_summary(
                            pages=pages, total=total, errors=errors
                        )
                        now = datetime.now().strftime("%Y-%m-%d %H:%M")
                        self.last_run_label.config(text=f"最終実行: {now}")
                        self.update_status(f"完了: {total}件のデータを取得")

                    elif status == "error":
                        self.run_btn.config(state="normal")
                        self.stop_btn.config(state="disabled")
                        self.update_status("エラーにより停止")

                    elif status == "robots_blocked":
                        self.run_btn.config(state="normal")
                        self.stop_btn.config(state="disabled")
                        self.update_status("robots.txtにより拒否")

        except queue.Empty:
            pass
        finally:
            self.root.after(100, self._poll_queue)

    def _open_output_dir(self):
        """出力フォルダをファイルマネージャで開く."""
        output_dir = self.output_tab.dir_entry.get().strip()
        if not output_dir:
            output_dir = self.app_config.get("app", {}).get(
                "default_output_dir", "output"
            )

        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        system = platform.system()
        if system == "Windows":
            os.startfile(output_dir)
        elif system == "Darwin":
            subprocess.Popen(["open", output_dir])
        else:
            subprocess.Popen(["xdg-open", output_dir])

    def update_status(self, msg: str):
        """ステータスバーのメッセージを更新する."""
        self.status_label.config(text=msg)

    def _show_about(self):
        """バージョン情報ダイアログを表示する."""
        messagebox.showinfo(
            "バージョン情報",
            "Webスクレイピングツール\n"
            "バージョン: 1.0\n\n"
            "Python + tkinter による汎用Webスクレイピングツール",
        )

    def _on_close(self):
        """ウィンドウ閉じるイベント."""
        if self.scraper_engine.is_running:
            if messagebox.askyesno("確認", "スクレイピング実行中です。終了しますか？"):
                self.scraper_engine.stop()
            else:
                return
        if self.current_profile:
            self._save_current_profile(silent=True)
        self.root.destroy()

    def run(self):
        """メインループを開始する."""
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.mainloop()
