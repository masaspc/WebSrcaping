"""プロファイルリストペイン."""

import tkinter as tk
from tkinter import messagebox, simpledialog, ttk


class ProfilePane(ttk.Frame):
    """左ペインのプロファイルリスト管理ウィジェット."""

    def __init__(self, parent, on_select=None, on_new=None, on_delete=None, on_duplicate=None):
        super().__init__(parent, padding=5)
        self.on_select = on_select
        self.on_new = on_new
        self.on_delete = on_delete
        self.on_duplicate = on_duplicate
        self._create_widgets()

    def _create_widgets(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # ラベル
        ttk.Label(self, text="プロファイル", font=("", 10, "bold")).grid(
            row=0, column=0, sticky="w", pady=(0, 5)
        )

        # リストボックス
        list_frame = ttk.Frame(self)
        list_frame.grid(row=1, column=0, sticky="nsew")
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        self.listbox = tk.Listbox(
            list_frame,
            selectmode="browse",
            font=("", 10),
            activestyle="none",
        )
        self.listbox.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(
            list_frame, orient="vertical", command=self.listbox.yview
        )
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.listbox.configure(yscrollcommand=scrollbar.set)

        self.listbox.bind("<<ListboxSelect>>", self._on_listbox_select)

        # ボタン
        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=2, column=0, sticky="ew", pady=(5, 0))

        ttk.Button(btn_frame, text="+ 新規", command=self._on_new_clicked).pack(
            fill="x", pady=(0, 2)
        )
        ttk.Button(btn_frame, text="- 削除", command=self._on_delete_clicked).pack(
            fill="x", pady=(0, 2)
        )
        ttk.Button(btn_frame, text="複製", command=self._on_duplicate_clicked).pack(
            fill="x"
        )

    def set_profiles(self, names: list[str]):
        """プロファイルリストを設定する."""
        self.listbox.delete(0, tk.END)
        for name in names:
            self.listbox.insert(tk.END, name)

    def get_selected(self) -> str | None:
        """選択中のプロファイル名を返す."""
        selection = self.listbox.curselection()
        if not selection:
            return None
        return self.listbox.get(selection[0])

    def select_by_name(self, name: str):
        """指定名のプロファイルを選択状態にする."""
        for i in range(self.listbox.size()):
            if self.listbox.get(i) == name:
                self.listbox.selection_clear(0, tk.END)
                self.listbox.selection_set(i)
                self.listbox.see(i)
                break

    def _on_listbox_select(self, event):
        """リストボックス選択時のイベント."""
        name = self.get_selected()
        if name and self.on_select:
            self.on_select(name)

    def _on_new_clicked(self):
        """新規プロファイル作成."""
        name = simpledialog.askstring(
            "新規プロファイル",
            "プロファイル名を入力してください:",
            parent=self,
        )
        if name and name.strip():
            if self.on_new:
                self.on_new(name.strip())

    def _on_delete_clicked(self):
        """プロファイル削除."""
        name = self.get_selected()
        if not name:
            messagebox.showwarning("選択エラー", "削除するプロファイルを選択してください")
            return
        if messagebox.askyesno("確認", f"プロファイル「{name}」を削除しますか？"):
            if self.on_delete:
                self.on_delete(name)

    def _on_duplicate_clicked(self):
        """プロファイル複製."""
        name = self.get_selected()
        if not name:
            messagebox.showwarning("選択エラー", "複製するプロファイルを選択してください")
            return
        new_name = simpledialog.askstring(
            "プロファイル複製",
            "新しいプロファイル名を入力してください:",
            parent=self,
            initialvalue=f"{name}_コピー",
        )
        if new_name and new_name.strip():
            if self.on_duplicate:
                self.on_duplicate(name, new_name.strip())
