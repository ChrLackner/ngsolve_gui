"""Vectors & Flow section for vector-valued functions.

A segmented control switches between Arrow glyph settings and Streamline
(field-line) settings, matching the designer layout. Only shown for vector CFs.
"""

from ngapp.components import *

from ..prop_widgets import Section, Chip, Segmented, field
from ..cerbsim_style import gap_xs, gap_sm, grow, row2

_COL = "column " + str(gap_sm)


class VectorsFlowSection(Section):
    """Arrow glyphs and streamlines for a vector field."""

    section_key = "vectors"

    def __init__(self, comp):
        self.comp = comp
        if comp.cf.dim <= 1:
            raise ValueError("Not applicable for scalar functions")

        has_streamlines = comp.cf.dim == comp.mesh.dim

        # -- Arrows controls --
        options = ["Norm"] + [str(i) for i in range(1, comp.cf.dim + 1)]
        self.color_component = QSelect(
            ui_options=options, ui_model_value=options[0], ui_dense=True, ui_filled=True,
        )
        self.color_component.on_update_model_value(self._update_color_component)

        self.grid_size = QInput(
            ui_type="number", ui_model_value=comp.vector_grid_size.value,
            ui_dense=True, ui_filled=True, ui_debounce=500,
        )
        comp.vector_grid_size.on_change(
            lambda val, _old: setattr(self.grid_size, "ui_model_value", val)
        )
        self.grid_size.on_update_model_value(self._update_grid_size)

        self.vector_scale = QSlider(
            ui_model_value=comp.vector_scale, ui_min=0.1, ui_max=5.0, ui_step=0.1,
            ui_dense=True, ui_label=True, ui_class=grow,
        )
        self.scale_by_value = Chip("Scale by magnitude", "mdi-ruler", comp.vector_scale_by_value)

        self._arrows = Div(
            Div(field("Color by", self.color_component),
                field("Density", self.grid_size), ui_class=row2),
            field("Arrow scale", self.vector_scale),
            self.scale_by_value,
            ui_class=_COL,
        )

        items = []
        if has_streamlines:
            # -- Streamline (field-line) controls --
            self.num_lines = QInput(ui_type="number", ui_model_value=comp.fieldlines_num_lines, ui_dense=True, ui_filled=True)
            self.length = QInput(ui_type="number", ui_model_value=comp.fieldlines_length, ui_dense=True, ui_filled=True)
            self.thickness = QInput(ui_type="number", ui_model_value=comp.fieldlines_thickness, ui_dense=True, ui_filled=True)
            direction_map_reverse = {0: "Both", 1: "Forward", -1: "Backward"}
            self.direction = QSelect(
                ui_options=["Both", "Forward", "Backward"],
                ui_model_value=direction_map_reverse.get(comp.fieldlines_direction.value, "Both"),
                ui_dense=True, ui_filled=True,
            )
            self.direction.on_update_model_value(self._update_direction)
            self.recalc_btn = QBtn(
                ui_label="Recalculate", ui_icon="mdi-refresh", ui_color="primary",
                ui_outline=True, ui_dense=True, ui_no_caps=True, ui_size="sm",
                ui_class="full-width",
            )
            self.recalc_btn.on_click(self._recalculate)
            self._streams = Div(
                Row(field("Lines", self.num_lines), field("Length", self.length),
                    field("Thick.", self.thickness), ui_class="items-end no-wrap " + str(gap_xs)),
                field("Direction", self.direction),
                self.recalc_btn,
                ui_class=_COL,
            )
            self._streams.ui_hidden = True

            mode = Segmented([("arrows", "Arrows"), ("streamlines", "Streamlines")],
                             "arrows", self._set_mode)
            items = [mode, self._arrows, self._streams]
        else:
            items = [self._arrows]

        self._has_streamlines = has_streamlines
        self._mode = "arrows"

        super().__init__(
            *items,
            icon="mdi-arrow-top-right-thin",
            title="Vectors & Flow",
            switchable=True,
            info="Show the vector field as arrow glyphs, or as streamlines for a "
                 "flow field. The header toggle activates the selected mode.",
        )

        # The section toggle drives the active mode's renderer; keep it in sync
        # with the underlying observables (also toggled by the display chips).
        self._sync_open()
        comp.surface_vectors_visible.on_change(lambda v, _o: self._sync_open())
        comp.field_lines_visible.on_change(lambda v, _o: self._sync_open())

    # -- switchable behaviour (mode-aware activation) ---------------------
    def _active_obs(self):
        if self._mode == "streamlines":
            return self.comp.field_lines_visible
        return self.comp.surface_vectors_visible

    def _sync_open(self):
        self._set_open(bool(self._active_obs().value))

    def _on_head_click(self):
        obs = self._active_obs()
        obs.value = not obs.value  # → on_change → _sync_open → _render

    def _set_mode(self, val):
        was_on = self._open
        old_obs = self._active_obs()
        self._mode = val
        self._arrows.ui_hidden = val != "arrows"
        if self._has_streamlines:
            self._streams.ui_hidden = val != "streamlines"
        new_obs = self._active_obs()
        # Moving modes while active swaps which renderer is shown.
        if was_on and old_obs is not new_obs:
            old_obs.value = False
            new_obs.value = True
        self._sync_open()

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
