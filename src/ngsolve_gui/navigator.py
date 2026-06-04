from ngapp.components import *

from .cerbsim_style import (
    nav_panel,
    panel_header,
    panel_header_title,
    panel_scroll,
    nav_search,
    nav_group_row,
    nav_group_caret,
    nav_group_caret_collapsed,
    nav_group_name,
    nav_count_badge,
    nav_item,
    nav_item_active,
    nav_number_hint,
    nav_side,
    nav_empty,
    avatar_min,
    grow,
)

_TYPE_GROUPS = {
    "geometry": ("Geometries", "mdi-cube"),
    "mesh": ("Meshes", "mdi-vector-triangle"),
    "function": ("Functions", "mdi-function-variant"),
    "plot": ("Plots", "mdi-chart-line"),
}


class Navigator(Div):
    def __init__(self, app_data, on_select, on_load_file=None):
        self.app_data = app_data
        self._on_select = on_select
        self._on_load_file = on_load_file
        self._collapsed = {}   # group label -> bool
        self._query = ""
        self._index_to_name = {}

        load_btn = QBtn(
            QTooltip("Load file  ·  geometry / mesh / .py"),
            ui_flat=True, ui_dense=True, ui_round=True, ui_size="sm",
            ui_icon="mdi-plus", ui_color="grey-7",
        )
        if on_load_file is not None:
            load_btn.on_click(lambda *a: on_load_file())

        header = Div(
            Div("Navigator", ui_class=panel_header_title),
            load_btn,
            ui_class=panel_header,
        )

        self._search = QInput(
            ui_model_value="",
            ui_dense=True,
            ui_borderless=True,
            ui_clearable=True,
            ui_debounce=150,
            ui_label="Filter objects…",
            ui_class=str(grow),
        )
        self._search.on_update_model_value(self._on_search)
        search_box = Div(
            QIcon(ui_name="mdi-magnify", ui_size="16px"),
            self._search,
            ui_class=nav_search,
        )

        self._scroll = Div(ui_class=panel_scroll)

        super().__init__(
            header,
            search_box,
            self._scroll,
            ui_class=nav_panel,
        )
        self.update()

    # -- search ---------------------------------------------------------
    def _on_search(self, event):
        self._query = (event.value or "").strip().lower()
        self._render()

    # -- collapse -------------------------------------------------------
    def _toggle_group(self, label):
        self._collapsed[label] = not self._collapsed.get(label, False)
        self._render()

    # -- public ---------------------------------------------------------
    def update(self):
        self._render()

    def select_by_index(self, n):
        """Select the nth item (1-based). Returns True if valid."""
        name = self._index_to_name.get(n)
        if name:
            self._on_select(name)
            return True
        return False

    # -- rendering ------------------------------------------------------
    def _ordered_groups(self):
        """Yield (label, icon, [(name, tab), ...]) in canonical order."""
        groups = {}
        for name, tab in self.app_data.get_tabs().items():
            groups.setdefault(tab.get("type", "unknown"), []).append((name, tab))

        for type_key, (label, icon) in _TYPE_GROUPS.items():
            if groups.get(type_key):
                yield label, icon, groups[type_key]
        for type_key, tab_list in groups.items():
            if type_key in _TYPE_GROUPS:
                continue
            yield type_key.title(), "mdi-help", tab_list

    def _render(self):
        # Assign keyboard number hints (1-9) across ALL tabs, in display order,
        # independent of filtering/collapse so the shortcuts stay stable.
        self._index_to_name = {}
        idx = 1
        numbers = {}
        for _label, _icon, tabs in self._ordered_groups():
            for tab_name, _tab in tabs:
                if idx <= 9:
                    numbers[tab_name] = idx
                    self._index_to_name[idx] = tab_name
                idx += 1

        active = self.app_data.active_tab
        q = self._query
        children = []
        for label, icon, tabs in self._ordered_groups():
            matches = [
                (n, t) for n, t in tabs
                if not q or q in t["title"].lower()
            ]
            if q and not matches:
                continue
            collapsed = self._collapsed.get(label, False)
            children.append(self._group_header(label, icon, len(tabs), collapsed))
            if collapsed:
                continue
            if not matches:
                children.append(Div("empty", ui_class=nav_empty))
                continue
            for tab_name, tab in matches:
                children.append(
                    self._item(tab_name, tab, tab_name == active,
                               numbers.get(tab_name), icon)
                )
        children.append(Div(ui_style="height: 12px;"))
        self._scroll.ui_children = children

    def _group_header(self, label, icon, count, collapsed):
        caret_cls = str(nav_group_caret)
        if collapsed:
            caret_cls += " " + str(nav_group_caret_collapsed)
        row = Div(
            QIcon(ui_name="mdi-chevron-down", ui_size="16px", ui_class=caret_cls),
            QIcon(ui_name=icon, ui_size="15px"),
            Div(label, ui_class=nav_group_name),
            Div(str(count), ui_class=nav_count_badge),
            ui_class=nav_group_row,
        )
        row.on("click", lambda e=None, l=label: self._toggle_group(l))
        return row

    def _item(self, tab_name, tab, is_active, number, group_icon):
        sections = []
        sections.append(
            QItemSection(
                Div(str(number) if number else "", ui_class=nav_number_hint),
                ui_side=True,
                ui_class=nav_side,
            )
        )
        sections.append(
            QItemSection(
                QIcon(
                    ui_name=tab.get("icon", group_icon),
                    ui_size="xs",
                    ui_color="primary" if is_active else "grey-7",
                ),
                ui_avatar=True,
                ui_class=avatar_min,
            )
        )
        sections.append(QItemSection(Div(tab["title"])))
        sections.append(self._build_context_menu(tab_name))

        item = QItem(
            *sections,
            ui_clickable=True,
            ui_active=is_active,
            ui_active_class=str(nav_item_active),
            ui_dense=True,
            ui_class=nav_item,
        )
        item.on_click(lambda e=None, n=tab_name: self._on_select(n))
        item.on("mousedown", lambda e, n=tab_name: self._on_middle_click(e, n))
        return item

    # -- context menu / actions -----------------------------------------
    def _build_context_menu(self, tab_name):
        delete_item = QItem(
            QItemSection(
                QIcon(ui_name="mdi-delete", ui_size="xs"),
                ui_avatar=True,
                ui_class=avatar_min,
            ),
            QItemSection("Delete"),
            ui_clickable=True,
            ui_dense=True,
        )
        delete_item.on_click(lambda e=None, n=tab_name: self._delete_tab(n))

        rename_input = QInput(
            ui_model_value=self.app_data.get_tab(tab_name)["title"],
            ui_dense=True,
            ui_autofocus=True,
        )
        rename_btn = QBtn(
            ui_label="OK", ui_color="primary", ui_flat=True, ui_dense=True
        )

        rename_dialog = QDialog(
            QCard(
                QCardSection("Rename"),
                QCardSection(rename_input),
                QCardActions(rename_btn, ui_align="right"),
            ),
        )
        rename_btn.on_click(
            lambda e=None, n=tab_name, inp=rename_input, dlg=rename_dialog: self._rename_tab(
                n, inp, dlg
            )
        )

        rename_item = QItem(
            QItemSection(
                QIcon(ui_name="mdi-pencil", ui_size="xs"),
                ui_avatar=True,
                ui_class=avatar_min,
            ),
            QItemSection("Rename"),
            rename_dialog,
            ui_clickable=True,
            ui_dense=True,
        )
        rename_item.on_click(
            lambda e=None, dlg=rename_dialog: setattr(dlg, "ui_model_value", True)
        )

        return QMenu(
            QList(rename_item, delete_item, ui_dense=True),
            ui_context_menu=True,
        )

    def _delete_tab(self, tab_name):
        self.app_data.delete_tab(tab_name)
        self.update()
        if self.app_data.active_tab:
            self._on_select(self.app_data.active_tab)

    def _rename_tab(self, tab_name, input_comp, dialog):
        new_title = input_comp.ui_model_value
        if new_title and new_title.strip():
            tab = self.app_data.get_tab(tab_name)
            if tab:
                tab["title"] = new_title.strip()
                self.update()
        dialog.ui_model_value = False

    def _on_middle_click(self, event, tab_name):
        if event.value.get("button") == 1:
            self._delete_tab(tab_name)
