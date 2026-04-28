from ngapp.components import *


class FieldLinesSection(QExpansionItem):
    def __init__(self, comp):
        self.comp = comp
        if comp.cf.dim != comp.mesh.dim:
            raise ValueError("Field lines not applicable")
        self.show_fieldlines = QCheckbox(
            ui_label="Show Field Lines",
            ui_model_value=comp.settings.get("field_lines", False),
        )
        self.show_fieldlines.on_update_model_value(self.update_show)

        self.num_lines = QInput(
            ui_label="Num Lines",
            ui_type="number",
            ui_model_value=comp.settings.get("fieldlines_num_lines", 100),
            ui_dense=True,
        )
        self.num_lines.on_change(self.update_option)

        self.length = QInput(
            ui_label="Length",
            ui_type="number",
            ui_model_value=comp.settings.get("fieldlines_length", 0.5),
            ui_dense=True,
        )
        self.length.on_change(self.update_option)

        self.thickness = QInput(
            ui_label="Thickness",
            ui_type="number",
            ui_model_value=comp.settings.get("fieldlines_thickness", 0.0015),
            ui_dense=True,
        )
        self.thickness.on_change(self.update_option)

        direction_options = ["Both", "Forward", "Backward"]
        self.direction = QSelect(
            ui_options=direction_options,
            ui_model_value=direction_options[
                comp.settings.get("fieldlines_direction", 0)
            ],
            ui_label="Direction",
            ui_dense=True,
        )
        self.direction.on_update_model_value(self.update_option)

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

    def update_show(self, event):
        self.comp.settings.set("field_lines", self.show_fieldlines.ui_model_value)
        if self.comp.fieldlines is not None:
            self.comp.fieldlines.active = self.show_fieldlines.ui_model_value
        self.comp.wgpu.scene.render()

    def _get_options(self):
        direction_map = {"Both": 0, "Forward": 1, "Backward": -1}
        return {
            "num_lines": int(float(self.num_lines.ui_model_value)),
            "length": float(self.length.ui_model_value),
            "thickness": float(self.thickness.ui_model_value),
            "direction": direction_map[self.direction.ui_model_value],
        }

    def update_option(self, event):
        try:
            opts = self._get_options()
        except (ValueError, KeyError):
            return
        self.comp.settings.set("fieldlines_num_lines", opts["num_lines"])
        self.comp.settings.set("fieldlines_length", opts["length"])
        self.comp.settings.set("fieldlines_thickness", opts["thickness"])
        self.comp.settings.set("fieldlines_direction", opts["direction"])

    def recalculate(self, event):
        try:
            opts = self._get_options()
        except (ValueError, KeyError):
            return
        if self.comp.fieldlines is not None:
            self.comp.fieldlines.fieldline_options.update(opts)
            self.comp.fieldlines.set_needs_update()
            self.comp.wgpu.scene.render()
