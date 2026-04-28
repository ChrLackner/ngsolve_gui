from ngapp.components import *


class GeometrySelectionSection(QExpansionItem):
    def __init__(self, comp):
        self.comp = comp
        self._heading = Div(
            "No selection",
            ui_style="font-size: 0.85rem; color: #78909c; padding-bottom: 4px;",
        )
        self.meshsize_input = QInput(
            ui_label="Mesh Size",
            ui_type="number",
            ui_debounce=500,
            ui_dense=True,
        )
        self.meshsize_input.on_update_model_value(comp.change_maxh)
        self.name_input = QInput(
            ui_label="Name",
            ui_type="text",
            ui_debounce=500,
            ui_dense=True,
        )
        self.name_input.on_update_model_value(comp.change_name)

        hide_btn = QBtn("Hide", ui_color="secondary", ui_flat=True, ui_dense=True)
        hide_btn.on_click(comp._hide_selected_shape)
        showall_btn = QBtn(
            "Show All", ui_color="secondary", ui_flat=True, ui_dense=True
        )
        showall_btn.on_click(lambda: comp._show_all_shapes())

        super().__init__(
            self._heading,
            self.meshsize_input,
            self.name_input,
            Row(hide_btn, showall_btn, ui_style="margin-top: 4px; gap: 8px;"),
            ui_icon="mdi-cursor-default-click",
            ui_label="Selection",
        )

        # Let the component notify us on selection changes
        comp._selection_section = self

    def update_selection(self, kind, item_id):
        """Called by GeometryComponent when a face/edge is selected."""
        geo = self.comp.geo
        if kind == "face":
            face = geo.faces[item_id]
            self._heading.ui_children = [f"Face {item_id}"]
            self.meshsize_input.ui_model_value = (
                None if face.maxh == 1e99 else face.maxh
            )
            self.name_input.ui_model_value = face.name
        elif kind == "edge":
            edge = geo.edges[item_id]
            self._heading.ui_children = [f"Edge {item_id}"]
            self.meshsize_input.ui_model_value = (
                None if edge.maxh == 1e99 else edge.maxh
            )
            self.name_input.ui_model_value = edge.name
        # Auto-expand when something is selected
        self.ui_model_value = True
