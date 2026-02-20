"""セレクタ設定タブ."""

import tkinter as tk
from tkinter import ttk


class SelectorSettingsTab(ttk.Frame):
    """CSSセレクタとフィールド定義を設定するタブ."""

    def __init__(self, parent):
        super().__init__(parent, padding=10)
        self.fields: list[dict] = []
        self._create_widgets()

    def _create_widgets(self):
        self.columnconfigure(0, weight=1)

        row = 0

        # --- コンテナセレクタ ---
        container_frame = ttk.LabelFrame(
            self, text="繰り返し要素のコンテナ", padding=10
        )
        container_frame.grid(row=row, column=0, sticky="ew", pady=(0, 10))
        container_frame.columnconfigure(0, weight=1)

        ttk.Label(container_frame, text="CSSセレクタ:").grid(
            row=0, column=0, sticky="w"
        )
        self.container_entry = ttk.Entry(container_frame, width=60)
        self.container_entry.grid(row=1, column=0, sticky="ew", pady=(2, 0))

        row += 1

        # --- フィールド一覧 ---
        fields_frame = ttk.LabelFrame(self, text="抽出フィールド", padding=10)
        fields_frame.grid(row=row, column=0, sticky="nsew", pady=(0, 10))
        fields_frame.columnconfigure(0, weight=1)
        fields_frame.rowconfigure(0, weight=1)
        self.rowconfigure(row, weight=1)

        # Treeview
        columns = ("name", "selector", "attribute")
        self.fields_tree = ttk.Treeview(
            fields_frame,
            columns=columns,
            show="headings",
            height=6,
            selectmode="browse",
        )
        self.fields_tree.heading("name", text="フィールド名")
        self.fields_tree.heading("selector", text="セレクタ")
        self.fields_tree.heading("attribute", text="属性")
        self.fields_tree.column("name", width=120)
        self.fields_tree.column("selector", width=200)
        self.fields_tree.column("attribute", width=80)

        scrollbar = ttk.Scrollbar(
            fields_frame, orient="vertical", command=self.fields_tree.yview
        )
        self.fields_tree.configure(yscrollcommand=scrollbar.set)

        self.fields_tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        self.fields_tree.bind("<<TreeviewSelect>>", self._on_field_selected)

        # ボタン
        btn_frame = ttk.Frame(fields_frame)
        btn_frame.grid(row=1, column=0, columnspan=2, sticky="w", pady=(5, 0))

        ttk.Button(btn_frame, text="+ フィールド追加", command=self._add_field).pack(
            side="left", padx=(0, 5)
        )
        ttk.Button(btn_frame, text="- 削除", command=self._remove_field).pack(
            side="left", padx=(0, 5)
        )
        ttk.Button(btn_frame, text="上へ", command=lambda: self._move_field(-1)).pack(
            side="left", padx=(0, 5)
        )
        ttk.Button(btn_frame, text="下へ", command=lambda: self._move_field(1)).pack(
            side="left"
        )

        row += 1

        # --- フィールド編集 ---
        edit_frame = ttk.LabelFrame(self, text="フィールド編集", padding=10)
        edit_frame.grid(row=row, column=0, sticky="ew", pady=(0, 10))
        edit_frame.columnconfigure(1, weight=1)

        ttk.Label(edit_frame, text="フィールド名:").grid(row=0, column=0, sticky="w")
        self.field_name_entry = ttk.Entry(edit_frame, width=30)
        self.field_name_entry.grid(row=0, column=1, sticky="w", padx=5)

        ttk.Label(edit_frame, text="セレクタ:").grid(
            row=1, column=0, sticky="w", pady=(5, 0)
        )
        self.field_selector_entry = ttk.Entry(edit_frame, width=40)
        self.field_selector_entry.grid(
            row=1, column=1, sticky="ew", padx=5, pady=(5, 0)
        )

        ttk.Label(edit_frame, text="取得属性:").grid(
            row=2, column=0, sticky="w", pady=(5, 0)
        )
        self.field_attr_var = tk.StringVar(value="text")
        ttk.Combobox(
            edit_frame,
            textvariable=self.field_attr_var,
            values=["text", "href", "src", "data-*", "カスタム"],
            width=15,
        ).grid(row=2, column=1, sticky="w", padx=5, pady=(5, 0))

        self.resolve_url_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            edit_frame,
            text="相対URLを絶対URLに変換",
            variable=self.resolve_url_var,
        ).grid(row=3, column=0, columnspan=2, sticky="w", pady=(5, 0))

        ttk.Label(edit_frame, text="正規表現フィルタ:").grid(
            row=4, column=0, sticky="w", pady=(5, 0)
        )
        self.field_regex_entry = ttk.Entry(edit_frame, width=40)
        self.field_regex_entry.grid(
            row=4, column=1, sticky="ew", padx=5, pady=(5, 0)
        )

        ttk.Button(edit_frame, text="適用", command=self._apply_field_edit).grid(
            row=5, column=1, sticky="w", padx=5, pady=(10, 0)
        )

        row += 1

        # --- ページネーション ---
        page_frame = ttk.LabelFrame(self, text="ページネーション", padding=10)
        page_frame.grid(row=row, column=0, sticky="ew", pady=(0, 10))

        self.pagination_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            page_frame,
            text="ページネーション有効",
            variable=self.pagination_var,
        ).grid(row=0, column=0, columnspan=2, sticky="w")

        ttk.Label(page_frame, text="方式:").grid(
            row=1, column=0, sticky="w", pady=(5, 0)
        )
        self.page_type_var = tk.StringVar(value="次ページボタン")
        ttk.Combobox(
            page_frame,
            textvariable=self.page_type_var,
            values=["次ページボタン", "ページ番号"],
            state="readonly",
            width=15,
        ).grid(row=1, column=1, sticky="w", padx=5, pady=(5, 0))

        ttk.Label(page_frame, text="セレクタ:").grid(
            row=2, column=0, sticky="w", pady=(5, 0)
        )
        self.page_selector_entry = ttk.Entry(page_frame, width=40)
        self.page_selector_entry.grid(
            row=2, column=1, sticky="w", padx=5, pady=(5, 0)
        )

        ttk.Label(page_frame, text="最大ページ数:").grid(
            row=3, column=0, sticky="w", pady=(5, 0)
        )
        self.max_pages_var = tk.StringVar(value="10")
        ttk.Entry(page_frame, textvariable=self.max_pages_var, width=8).grid(
            row=3, column=1, sticky="w", padx=5, pady=(5, 0)
        )

    def _add_field(self):
        """新しいフィールドを追加する."""
        idx = len(self.fields) + 1
        field = {
            "name": f"フィールド{idx}",
            "selector": "",
            "attribute": "text",
            "resolve_url": False,
            "regex": "",
        }
        self.fields.append(field)
        self.fields_tree.insert(
            "", "end", values=(field["name"], field["selector"], field["attribute"])
        )

    def _remove_field(self):
        """選択中のフィールドを削除する."""
        selection = self.fields_tree.selection()
        if not selection:
            return
        idx = self.fields_tree.index(selection[0])
        self.fields_tree.delete(selection[0])
        if 0 <= idx < len(self.fields):
            self.fields.pop(idx)

    def _move_field(self, direction: int):
        """選択中のフィールドを上下に移動する."""
        selection = self.fields_tree.selection()
        if not selection:
            return
        idx = self.fields_tree.index(selection[0])
        new_idx = idx + direction
        if new_idx < 0 or new_idx >= len(self.fields):
            return
        self.fields[idx], self.fields[new_idx] = (
            self.fields[new_idx],
            self.fields[idx],
        )
        self._refresh_tree()
        # 移動先を選択
        children = self.fields_tree.get_children()
        if 0 <= new_idx < len(children):
            self.fields_tree.selection_set(children[new_idx])

    def _on_field_selected(self, event):
        """フィールド選択時に編集フォームに値をロードする."""
        selection = self.fields_tree.selection()
        if not selection:
            return
        idx = self.fields_tree.index(selection[0])
        if idx >= len(self.fields):
            return
        field = self.fields[idx]

        self.field_name_entry.delete(0, tk.END)
        self.field_name_entry.insert(0, field.get("name", ""))
        self.field_selector_entry.delete(0, tk.END)
        self.field_selector_entry.insert(0, field.get("selector", ""))
        self.field_attr_var.set(field.get("attribute", "text"))
        self.resolve_url_var.set(field.get("resolve_url", False))
        self.field_regex_entry.delete(0, tk.END)
        self.field_regex_entry.insert(0, field.get("regex", ""))

    def _apply_field_edit(self):
        """編集フォームの値を選択中のフィールドに適用する."""
        selection = self.fields_tree.selection()
        if not selection:
            return
        idx = self.fields_tree.index(selection[0])
        if idx >= len(self.fields):
            return

        self.fields[idx] = {
            "name": self.field_name_entry.get().strip(),
            "selector": self.field_selector_entry.get().strip(),
            "attribute": self.field_attr_var.get(),
            "resolve_url": self.resolve_url_var.get(),
            "regex": self.field_regex_entry.get().strip(),
        }
        self._refresh_tree()
        children = self.fields_tree.get_children()
        if 0 <= idx < len(children):
            self.fields_tree.selection_set(children[idx])

    def _refresh_tree(self):
        """Treeviewを現在のfieldsリストで更新する."""
        self.fields_tree.delete(*self.fields_tree.get_children())
        for field in self.fields:
            self.fields_tree.insert(
                "",
                "end",
                values=(
                    field.get("name", ""),
                    field.get("selector", ""),
                    field.get("attribute", ""),
                ),
            )

    def load_from_profile(self, profile: dict):
        """プロファイルからフォームに値をロードする."""
        selectors = profile.get("selectors", {})

        self.container_entry.delete(0, tk.END)
        self.container_entry.insert(0, selectors.get("container", ""))

        self.fields = []
        for field in selectors.get("fields", []):
            self.fields.append(dict(field))
        self._refresh_tree()

        pagination = profile.get("pagination", {})
        self.pagination_var.set(pagination.get("enabled", False))
        page_type = pagination.get("type", "next_button")
        type_map = {"next_button": "次ページボタン", "page_number": "ページ番号"}
        self.page_type_var.set(type_map.get(page_type, "次ページボタン"))
        self.page_selector_entry.delete(0, tk.END)
        self.page_selector_entry.insert(0, pagination.get("selector", ""))
        self.max_pages_var.set(str(pagination.get("max_pages", 10)))

    def save_to_profile(self) -> dict:
        """フォームの値をプロファイル辞書として返す."""
        page_type = self.page_type_var.get()
        type_map = {"次ページボタン": "next_button", "ページ番号": "page_number"}

        try:
            max_pages = int(self.max_pages_var.get())
        except ValueError:
            max_pages = 10

        return {
            "selectors": {
                "container": self.container_entry.get().strip(),
                "fields": list(self.fields),
            },
            "pagination": {
                "enabled": self.pagination_var.get(),
                "type": type_map.get(page_type, "next_button"),
                "selector": self.page_selector_entry.get().strip(),
                "max_pages": max_pages,
            },
        }
