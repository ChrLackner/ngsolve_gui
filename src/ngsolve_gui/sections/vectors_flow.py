"""Combined Vectors & Field Lines section for vector-valued functions.

Compact unified section. Only shown for vector CFs (dim > 1).
"""

from ngapp.components import *

from ..cerbsim_style import label, field_label, nowrap, gap_xs, grow, input_compact

_ROW = "items-center no-wrap " + str(gap_xs)


class VectorsFlowSection(QExpansionItem):
    """Vector arrows and field line settings combined."""

    def __init__(self, comp):
        self.comp = comp
        if comp.cf.dim <= 1:
            raise ValueError("Not applicable for scalar functions")

        items = []

        # Row 1: Color dropdown + Grid size with +/-
        options = ["Norm"] + [str(i) for i in range(1, comp.cf.dim + 1)]
        self.color_component = QSelect(
            ui_options=options, ui_model_value=options[0],
            ui_label="Color", ui_dense=True, ui_class=input_compact,
        )
        self.color_component.on_update_model_value(self._update_color_component)

        self.grid_size = QInput(
            ui_label="Grid", ui_type="number",
            ui_model_value=comp.vector_grid_size.value,
            ui_dense=True, ui_debounce=500, ui_class=input_compact,
        )
        comp.vector_grid_size.on_change(
            lambda val, _old: setattr(self.grid_size, "ui_model_value", val)
        )
        minus_btn = QBtn(ui_icon="mdi-minus", ui_flat=True, ui_dense=True, ui_round=True, ui_size="xs")
        plus_btn = QBtn(ui_icon="mdi-plus", ui_flat=True, ui_dense=True, ui_round=True, ui_size="xs")
        minus_btn.on_click(lambda e=None: self._step_grid(-50))
        plus_btn.on_click(lambda e=None: self._step_grid(50))
        self.grid_size.on_update_model_value(self._update_grid_size)

        items.append(Row(
            self.color_component, self.grid_size, minus_btn, plus_btn,
            ui_class=_ROW,
        ))

        # Row 2: Scale by magnitude checkbox + Scale slider
        self.scale_by_value = QCheckbox(
            "Scale by mag.", ui_model_value=comp.vector_scale_by_value, ui_dense=True,
        )
        self.vector_scale = QSlider(
            ui_model_value=comp.vector_scale,
            ui_min=0.1, ui_max=5.0, ui_step=0.1,
            ui_dense=True, ui_label=True,
            ui_class=grow,
        )
        items.append(Row(
            self.scale_by_value,
            Div("Scale", ui_class=field_label + " " + nowrap + " col-auto q-pl-xs"),
            self.vector_scale,
            ui_class=_ROW,
        ))

        # Field Lines (only if applicable)
        if comp.cf.dim == comp.mesh.dim:
            items.append(Div("Field Lines", ui_class=label))
            self.num_lines = QInput(ui_label="Lines", ui_type="number", ui_model_value=comp.fieldlines_num_lines, ui_dense=True, ui_class=grow)
            self.length = QInput(ui_label="Length", ui_type="number", ui_model_value=comp.fieldlines_length, ui_dense=True, ui_class=grow)
            self.thickness = QInput(ui_label="Thick.", ui_type="number", ui_model_value=comp.fieldlines_thickness, ui_dense=True, ui_class=grow)
            direction_map_reverse = {0: "Both", 1: "Forward", -1: "Backward"}
            self.direction = QSelect(
                ui_options=["Both", "Forward", "Backward"],
                ui_model_value=direction_map_reverse.get(comp.fieldlines_direction.value, "Both"),
                ui_label="Dir", ui_dense=True, ui_class=grow,
            )
            self.direction.on_update_model_value(self._update_direction)
            self.recalc_btn = QBtn(
                ui_label="Recalculate", ui_color="primary", ui_outline=True,
                ui_dense=True, ui_no_caps=True, ui_size="sm",
                ui_class="col-auto",
            )
            self.recalc_btn.on_click(self._recalculate)

            items.append(Row(self.num_lines, self.length, self.thickness, ui_class=_ROW))
            items.append(Row(self.direction, self.recalc_btn, ui_class=_ROW))

        super().__init__(
            *items,
            ui_icon="mdi-arrow-top-right-thin",
            ui_label="Vectors & Flow",
            ui_dense=True,
        )

    def _step_grid(self, delta):
        try:
            val = int(float(self.grid_size.ui_model_value or 200))
        except (ValueError, TypeError):
            val = 200
        self.comp.vector_grid_size.value = max(1, val + delta)

    def _update_grid_size(self, event):
        try:
            v = int(float(event.value))
            if v >= 1:
                self.comp.vector_grid_size.value = v
        except (ValueError, TypeError):
            pass

    def _update_color_component(self, event):
        index = self.color_component.ui_options.index(self.color_component.ui_model_value)
        comp = self.comp
        if comp.elements2d is not None:
            comp.elements2d.set_component(index - 1)
        if comp.clippingcf is not None:
            comp.clippingcf.set_component(index - 1)
        comp.colorbar.set_needs_update()
        comp.wgpu.scene.render()

    def _update_direction(self, event):
        direction_map = {"Both": 0, "Forward": 1, "Backward": -1}
        try:
            self.comp.fieldlines_direction.value = direction_map[event.value]
        except KeyError:
            pass

    def _recalculate(self, event):
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
