from ngapp.components import *


class GeometrySelectionSection(QExpansionItem):
    def __init__(self, comp):
        self.comp = comp
        self._heading = Div(
            "No selection",
            ui_style="font-size: 0.85rem; color: #78909c; padding-bottom: 4px;",
        )
        _cb_style = "padding: 0 4px 0 0;"
        self._pick_mode_row = Row(
            Div("Pick:", ui_style="font-size: 0.8rem; color: #78909c; white-space: nowrap; margin-right: 4px; line-height: 32px;"),
            QCheckbox(ui_label="S", ui_model_value=comp.pick_solid, ui_dense=True, ui_style=_cb_style),
            QCheckbox(ui_label="F", ui_model_value=comp.pick_faces, ui_dense=True, ui_style=_cb_style),
            QCheckbox(ui_label="E", ui_model_value=comp.pick_edges, ui_dense=True, ui_style=_cb_style),
            QCheckbox(ui_label="V", ui_model_value=comp.pick_vertices, ui_dense=True, ui_style=_cb_style),
            ui_style="align-items: center; flex-wrap: nowrap;",
        )
        self.meshsize_input = QInput(
            ui_label="Mesh Size",
            ui_type="number",
            ui_debounce=500,
            ui_dense=True,
            ui_disable=True,
        )
        self.meshsize_input.on_update_model_value(comp.change_maxh)
        self.name_input = QInput(
            ui_label="Name",
            ui_type="text",
            ui_debounce=500,
            ui_dense=True,
            ui_disable=True,
        )
        self.name_input.on_update_model_value(comp.change_name)

        hide_btn = QBtn("Hide", ui_color="secondary", ui_flat=True, ui_dense=True)
        hide_btn.on_click(comp._hide_selected_shape)
        showall_btn = QBtn(
            "Show All", ui_color="secondary", ui_flat=True, ui_dense=True
        )
        showall_btn.on_click(lambda: comp._show_all_shapes())

        super().__init__(
            self._pick_mode_row,
            self._heading,
            self.meshsize_input,
            self.name_input,
            Row(hide_btn, showall_btn, ui_style="margin-top: 4px; gap: 8px;"),
            ui_icon="mdi-cursor-default-click",
            ui_label="Selection",
        )

        # Let the component notify us on selection changes
        comp._selection_section = self

    def _entity_name_maxh(self, kind, index):
        """Return (name, maxh) for an entity, using the component helper."""
        entity = self.comp._get_entity(kind, index)
        if entity is None:
            return ("", None)
        raw_maxh = entity.maxh
        return (entity.name or "", None if raw_maxh >= 1e99 else raw_maxh)

    def update_selection(self, kind, index):
        """Called by GeometryComponent when a single entity is selected."""
        label = {"face": "Face", "edge": "Edge", "vertex": "Vertex", "solid": "Solid"}.get(kind, kind)
        self._heading.ui_children = [f"{label} {index}"]
        name, maxh = self._entity_name_maxh(kind, index)
        self.meshsize_input.ui_model_value = maxh
        self.meshsize_input.ui_hint = ""
        self.name_input.ui_model_value = name
        self.name_input.ui_hint = ""
        self.meshsize_input.ui_disable = False
        self.name_input.ui_disable = False
        self.ui_model_value = True

    def update_multi_selection(self, items):
        """Called when multiple entities are selected."""
        self._heading.ui_children = [f"{len(items)} selected"]
        names = set()
        maxhs = set()
        for kind, idx in items:
            name, maxh = self._entity_name_maxh(kind, idx)
            names.add(name)
            maxhs.add(maxh)
        if len(names) == 1:
            self.name_input.ui_model_value = names.pop()
            self.name_input.ui_hint = ""
        else:
            self.name_input.ui_model_value = ""
            self.name_input.ui_hint = "Multiple values"
        if len(maxhs) == 1:
            self.meshsize_input.ui_model_value = maxhs.pop()
            self.meshsize_input.ui_hint = ""
        else:
            self.meshsize_input.ui_model_value = None
            self.meshsize_input.ui_hint = "Multiple values"
        self.meshsize_input.ui_disable = False
        self.name_input.ui_disable = False
        self.ui_model_value = True

    def clear_selection(self):
        """Reset the panel to no-selection state."""
        self._heading.ui_children = ["No selection"]
        self.meshsize_input.ui_model_value = None
        self.meshsize_input.ui_hint = ""
        self.name_input.ui_model_value = ""
        self.name_input.ui_hint = ""
        self.meshsize_input.ui_disable = True
        self.name_input.ui_disable = True
