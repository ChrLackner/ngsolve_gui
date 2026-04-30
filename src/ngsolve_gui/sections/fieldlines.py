from ngapp.components import *


class FieldLinesSection(QExpansionItem):
    def __init__(self, comp):
        self.comp = comp
        if comp.cf.dim != comp.mesh.dim:
            raise ValueError("Field lines not applicable")
        self.show_fieldlines = QCheckbox(
            ui_label="Show Field Lines",
            ui_model_value=comp.field_lines_visible,
        )

        self.num_lines = QInput(
            ui_label="Num Lines",
            ui_type="number",
            ui_model_value=comp.fieldlines_num_lines,
            ui_dense=True,
        )

        self.length = QInput(
            ui_label="Length",
            ui_type="number",
            ui_model_value=comp.fieldlines_length,
            ui_dense=True,
        )

        self.thickness = QInput(
            ui_label="Thickness",
            ui_type="number",
            ui_model_value=comp.fieldlines_thickness,
            ui_dense=True,
        )

        direction_options = ["Both", "Forward", "Backward"]
        direction_map_reverse = {0: "Both", 1: "Forward", -1: "Backward"}
        self.direction = QSelect(
            ui_options=direction_options,
            ui_model_value=direction_map_reverse.get(
                comp.fieldlines_direction.value, "Both"
            ),
            ui_label="Direction",
            ui_dense=True,
        )
        self.direction.on_update_model_value(self._update_direction)

        self.recalc_btn = QBtn(ui_label="Recalculate", ui_color="primary", ui_flat=True)
        self.recalc_btn.on_click(self.recalculate)

        super().__init__(
            self.show_fieldlines,
            self.num_lines,
            self.length,
            self.thickness,
            self.direction,
            self.recalc_btn,
            ui_icon="mdi-chart-timeline-variant",
            ui_label="Field Lines",
        )

    def _update_direction(self, event):
        direction_map = {"Both": 0, "Forward": 1, "Backward": -1}
        try:
            self.comp.fieldlines_direction.value = direction_map[event.value]
        except KeyError:
            pass

    def recalculate(self, event):
        comp = self.comp
        if comp.fieldlines is not None:
            comp.fieldlines.fieldline_options.update({
                "num_lines": comp.fieldlines_num_lines.value,
                "length": comp.fieldlines_length.value,
                "thickness": comp.fieldlines_thickness.value,
                "direction": comp.fieldlines_direction.value,
            })
            comp.fieldlines.set_needs_update()
            comp.wgpu.scene.render()
