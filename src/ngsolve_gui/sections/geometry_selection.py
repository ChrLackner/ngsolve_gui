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

    def update_selection(self, kind, index):
        """Called by GeometryComponent when a face/edge/vertex/solid is selected."""
        geo = self.comp.geo
        if kind == "face":
            face = geo.faces[index]
            self._heading.ui_children = [f"Face {index}"]
            self.meshsize_input.ui_model_value = (
                None if face.maxh >= 1e99 else face.maxh
            )
            self.name_input.ui_model_value = face.name
            self.meshsize_input.ui_disable = False
            self.name_input.ui_disable = False
        elif kind == "edge":
            edge = geo.edges[index]
            self._heading.ui_children = [f"Edge {index}"]
            self.meshsize_input.ui_model_value = (
                None if edge.maxh >= 1e99 else edge.maxh
            )
            self.name_input.ui_model_value = edge.name
            self.meshsize_input.ui_disable = False
            self.name_input.ui_disable = False
        elif kind == "vertex":
            self._heading.ui_children = [f"Vertex {index}"]
            self.meshsize_input.ui_model_value = None
            self.name_input.ui_model_value = ""
            self.meshsize_input.ui_disable = True
            self.name_input.ui_disable = True
        elif kind == "solid":
            solid_name = ""
            try:
                solid_name = list(self.comp.geo.shape.solids)[index].name or ""
            except Exception:
                pass
            heading = f"Solid {index}"
            if solid_name:
                heading += f"  ({solid_name})"
            self._heading.ui_children = [heading]
            self.meshsize_input.ui_model_value = None
            self.name_input.ui_model_value = ""
            self.meshsize_input.ui_disable = True
            self.name_input.ui_disable = True
        # Auto-expand when something is selected
        self.ui_model_value = True

    def clear_selection(self):
        """Reset the panel to no-selection state."""
        self._heading.ui_children = ["No selection"]
        self.meshsize_input.ui_model_value = None
        self.name_input.ui_model_value = ""
        self.meshsize_input.ui_disable = True
        self.name_input.ui_disable = True
