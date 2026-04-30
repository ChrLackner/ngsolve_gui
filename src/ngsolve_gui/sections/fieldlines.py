from ngapp.components import *


class FieldLinesSection(QExpansionItem):
    def __init__(self, comp):
        self.comp = comp
        if comp.cf.dim != comp.mesh.dim:
            raise ValueError("Field lines not applicable")
        self.show_fieldlines = QCheckbox(
            ui_label="Show Field Lines",
            ui_model_value=comp.field_lines_visible.value,
        )
        bind(comp.field_lines_visible, self.show_fieldlines)

        self.num_lines = QInput(
            ui_label="Num Lines",
            ui_type="number",
            ui_model_value=comp.fieldlines_num_lines.value,
            ui_dense=True,
        )
        self.num_lines.on_change(self._update_option)

        self.length = QInput(
            ui_label="Length",
            ui_type="number",
            ui_model_value=comp.fieldlines_length.value,
            ui_dense=True,
        )
        self.length.on_change(self._update_option)

        self.thickness = QInput(
            ui_label="Thickness",
            ui_type="number",
            ui_model_value=comp.fieldlines_thickness.value,
            ui_dense=True,
        )
        self.thickness.on_change(self._update_option)

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
        self.direction.on_update_model_value(self._update_option)

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

    def _get_options(self):
        direction_map = {"Both": 0, "Forward": 1, "Backward": -1}
        return {
            "num_lines": int(float(self.num_lines.ui_model_value)),
            "length": float(self.length.ui_model_value),
            "thickness": float(self.thickness.ui_model_value),
            "direction": direction_map[self.direction.ui_model_value],
        }

    def _update_option(self, event):
        try:
            opts = self._get_options()
        except (ValueError, KeyError):
            return
        self.comp.fieldlines_num_lines.value = opts["num_lines"]
        self.comp.fieldlines_length.value = opts["length"]
        self.comp.fieldlines_thickness.value = opts["thickness"]
        self.comp.fieldlines_direction.value = opts["direction"]

    def recalculate(self, event):
        try:
            opts = self._get_options()
        except (ValueError, KeyError):
            return
        if self.comp.fieldlines is not None:
            self.comp.fieldlines.fieldline_options.update(opts)
            self.comp.fieldlines.set_needs_update()
            self.comp.wgpu.scene.render()
