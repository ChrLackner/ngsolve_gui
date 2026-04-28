from ngapp.components import *

from .styles import sidebar_style

_TYPE_GROUPS = {
    "geometry": ("Geometries", "mdi-cube"),
    "mesh": ("Meshes", "mdi-vector-triangle"),
    "function": ("Functions", "mdi-function-variant"),
    "plot": ("Plots", "mdi-chart-line"),
}


class Navigator(Div):
    def __init__(self, app_data, on_select):
        self.app_data = app_data
        self._on_select = on_select
        self._list = QList(ui_dense=True, ui_separator=True)
        super().__init__(
            self._list,
            ui_style=sidebar_style(
                border_side="right", extra="width: 200px; min-width: 200px;"
            ),
        )
        self.update()

    def _number_hint(self, idx):
        if idx <= 9:
            return QItemSection(
                Div(
                    str(idx),
                    ui_style="font-size: 0.65rem; color: #aaa; min-width: 14px; text-align: center;",
                ),
                ui_side=True,
                ui_style="min-width: 14px; padding-right: 0;",
            )
        return None

    def update(self):
        self._index_to_name = {}
        groups = {}
        for name, tab in self.app_data.get_tabs().items():
            tab_type = tab.get("type", "unknown")
            groups.setdefault(tab_type, []).append((name, tab))

        items = []
        idx = 1
        active = self.app_data.active_tab
        for type_key, (group_label, group_icon) in _TYPE_GROUPS.items():
            tabs_in_group = groups.get(type_key, [])
            if not tabs_in_group:
                continue
            header = QItemLabel(
                group_label,
                ui_header=True,
                ui_class="text-weight-bold text-grey-7",
                ui_style="font-size: 0.75rem; letter-spacing: 0.05em; text-transform: uppercase; padding: 12px 16px 4px;",
            )
            items.append(header)
            for tab_name, tab in tabs_in_group:
                is_active = tab_name == active
                self._index_to_name[idx] = tab_name
                children = [
                    c
                    for c in [
                        self._number_hint(idx),
                        QItemSection(
                            QIcon(
                                ui_name=tab.get("icon", group_icon),
                                ui_size="xs",
                                ui_color="primary" if is_active else "grey-7",
                            ),
                            ui_avatar=True,
                            ui_style="min-width: 32px;",
                        ),
                        QItemSection(
                            Div(
                                tab["title"],
                                ui_style="font-size: 0.85rem;"
                                + (" font-weight: 600;" if is_active else ""),
                            ),
                        ),
                        self._build_context_menu(tab_name),
                    ]
                    if c is not None
                ]
                item = QItem(
                    *children,
                    ui_clickable=True,
                    ui_active=is_active,
                    ui_active_class="bg-blue-1 text-primary",
                    ui_dense=True,
                    ui_style="border-radius: 6px; margin: 1px 6px; padding: 4px 8px;",
                )
                item.on_click(lambda e=None, n=tab_name: self._on_select(n))
                item.on("mousedown", lambda e, n=tab_name: self._on_middle_click(e, n))
                items.append(item)
                idx += 1

        for type_key, tab_list in groups.items():
            if type_key in _TYPE_GROUPS:
                continue
            for tab_name, tab in tab_list:
                is_active = tab_name == active
                self._index_to_name[idx] = tab_name
                children = [
                    c
                    for c in [
                        self._number_hint(idx),
                        QItemSection(
                            QIcon(ui_name=tab.get("icon", "mdi-help"), ui_size="xs"),
                            ui_avatar=True,
                            ui_style="min-width: 32px;",
                        ),
                        QItemSection(Div(tab["title"], ui_style="font-size: 0.85rem;")),
                        self._build_context_menu(tab_name),
                    ]
                    if c is not None
                ]
                item = QItem(
                    *children,
                    ui_clickable=True,
                    ui_active=is_active,
                    ui_active_class="bg-blue-1 text-primary",
                    ui_dense=True,
                    ui_style="border-radius: 6px; margin: 1px 6px; padding: 4px 8px;",
                )
                item.on_click(lambda e=None, n=tab_name: self._on_select(n))
                item.on("mousedown", lambda e, n=tab_name: self._on_middle_click(e, n))
                items.append(item)
                idx += 1

        self._list.ui_children = items

    def select_by_index(self, n):
        """Select the nth item (1-based). Returns True if valid."""
        name = self._index_to_name.get(n)
        if name:
            self._on_select(name)
            return True
        return False

    def _build_context_menu(self, tab_name):
        delete_item = QItem(
            QItemSection(
                QIcon(ui_name="mdi-delete", ui_size="xs"),
                ui_avatar=True,
                ui_style="min-width: 32px;",
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
                ui_style="min-width: 32px;",
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
            QList(delete_item, rename_item, ui_dense=True),
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
