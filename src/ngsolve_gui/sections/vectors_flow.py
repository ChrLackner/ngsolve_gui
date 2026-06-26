"""Vectors & Flow section for vector-valued functions.

Arrow glyphs can be drawn on the surface and/or on the clipping plane (3D);
those targets are toggle buttons in the section header so they can be switched
without opening the section. The body holds the arrow settings plus a grouped
"Flow" card bundling the streamlines (field-line) and LIC (line integral
convolution) sub-features. Only shown for vector CFs.
"""

from ngapp.components import *

from .. import cerbsim_style as cb
from ..prop_widgets import Section, Chip, Toggle, SubToggleBlock, chip_row, field
from ..cerbsim_style import gap_xs, gap_sm, gap_md, grow

_COL = "column " + str(gap_sm)


class VectorsFlowSection(Section):
    """Arrow glyphs (surface / clip plane) and streamlines for a vector field."""

    section_key = "vectors"

    def __init__(self, comp):
        self.comp = comp
        if comp.cf.dim <= 1:
            raise ValueError("Not applicable for scalar functions")

        has_streamlines = comp.cf.dim == comp.mesh.dim
        has_clip = comp.clipping_vectors is not None

        # -- Header target toggles: where to draw the arrows (surface / clip). --
        head_actions = [
            Chip("Surface", "mdi-grid", comp.surface_vectors_visible, small=True)
        ]
        if has_clip:
            head_actions.append(
                Chip("Clip", "mdi-box-cutter", comp.clipping_vectors_visible, small=True)
            )

        # -- Arrow settings (shared by both arrow targets) --
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
        # "Scale by magnitude" temporarily removed from the UI (not yet correct);
        # the field defaults to off (comp.vector_scale_by_value).

        body = [
            field("Density", self.grid_size),
            field("Arrow scale", self.vector_scale),
        ]

        # -- Flow features: streamlines + LIC. Each sits in its own faint inset
        #    card (the shared card style signals they belong together) separated
        #    by a plain gap, and each toggle collapses its settings when off. --
        if has_streamlines:
            body.append(Div(self._build_streamlines(comp), ui_class=cb.flow_group))
        if getattr(comp, "lic", None) is not None:
            body.append(Div(self._build_lic(comp), ui_class=cb.flow_group))

        super().__init__(
            *body,
            icon="mdi-arrow-top-right-thin",
            title="Vectors & Flow",
            head_actions=head_actions,
            info="Draw the vector field as arrows on the surface and/or the "
                 "clipping plane (toggles in the header), or as streamlines.",
        )

    def _build_streamlines(self, comp):
        """Streamlines (field-line) sub-feature for the grouped flow card."""
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
        return SubToggleBlock(
            "Streamlines", comp.field_lines_visible,
            Row(field("Lines", self.num_lines), field("Length", self.length),
                field("Thick.", self.thickness), ui_class="items-end no-wrap " + str(gap_xs)),
            field("Direction", self.direction),
            self.recalc_btn,
        )

    def _build_lic(self, comp):
        """Line Integral Convolution sub-feature for the grouped flow card.

        Paints the field's flow as a dense streamline texture — on the clipping
        plane (3D) or the surface itself (2D). Sliders two-way bind to the
        Observables; the component's on_change handlers push to the GPU renderer."""
        kernel_length = QSlider(
            ui_model_value=comp.lic_kernel_length, ui_min=5, ui_max=80, ui_step=1,
            ui_dense=True, ui_label=True,
        )
        contrast = QSlider(
            ui_model_value=comp.lic_contrast, ui_min=0.0, ui_max=1.0, ui_step=0.05,
            ui_dense=True, ui_label=True,
        )
        # Line width is the droplet size, only meaningful in oriented mode — so it
        # sits next to the Oriented toggle and is disabled while oriented is off.
        oriented = Chip("Oriented", "mdi-arrow-right-thin", comp.lic_oriented, small=True)
        thickness = QSlider(
            ui_model_value=comp.lic_thickness, ui_min=1, ui_max=10, ui_step=1,
            ui_dense=True, ui_label=True, ui_class=grow,
        )
        thickness.ui_disable = not comp.lic_oriented.value
        comp.lic_oriented.on_change(
            lambda v, _o: setattr(thickness, "ui_disable", not bool(v))
        )
        return SubToggleBlock(
            "Line integral convolution", comp.lic_visible,
            field("Kernel length", kernel_length),
            field("Line width",
                  Row(thickness, oriented,
                      ui_class="items-center no-wrap " + str(gap_md))),
            field("Contrast", contrast),
            chip_row(
                Chip("Supersampling", "mdi-quality-high", comp.lic_supersample, small=True),
            ),
        )

    def _update_grid_size(self, event):
        try:
            v = int(float(event.value))
            if v >= 1:
                self.comp.vector_grid_size.value = v
        except (ValueError, TypeError):
            pass

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
