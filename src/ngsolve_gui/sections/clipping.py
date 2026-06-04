"""Clipping section — cutting plane controls. Compact layout."""

from ngapp.components import *
import math

from ..prop_widgets import Section, Chip, chip_row
from ..cerbsim_style import label, axis_label, gap_xs, gap_sm, input_compact


class ClippingSection(Section):
    section_key = "clipping"

    def __init__(self, comp):
        self.comp = comp
        if hasattr(comp, "mesh") and comp.mesh.dim < 3:
            raise ValueError("Clipping not applicable for 2D")

        clip = comp.clipping

        # Toggle row
        toggle_row = chip_row(
            Chip("Enable", "mdi-box-cutter", comp.clipping_enabled),
            Chip("Global", "mdi-earth", comp.use_global_clipping),
        )

        # Normal direction — 3 compact slider rows
        self.dx = QSlider(ui_model_value=clip.normal[0], ui_min=-1, ui_max=1, ui_step=0.1, ui_dense=True)
        self.dy = QSlider(ui_model_value=clip.normal[1], ui_min=-1, ui_max=1, ui_step=0.1, ui_dense=True)
        self.dz = QSlider(ui_model_value=clip.normal[2], ui_min=-1, ui_max=1, ui_step=0.1, ui_dense=True)
        self.dx.on_update_model_value(self._set_nx)
        self.dy.on_update_model_value(self._set_ny)
        self.dz.on_update_model_value(self._set_nz)
        self.dx.on("dblclick", lambda e: (setattr(self.dx, "ui_model_value", 0), self._set_nx(0)))
        self.dy.on("dblclick", lambda e: (setattr(self.dy, "ui_model_value", 0), self._set_ny(0)))
        self.dz.on("dblclick", lambda e: (setattr(self.dz, "ui_model_value", 0), self._set_nz(0)))

        dir_block = Div(
            Row(Div("x", ui_class=axis_label), self.dx, ui_class="items-center no-wrap " + gap_xs),
            Row(Div("y", ui_class=axis_label), self.dy, ui_class="items-center no-wrap " + gap_xs),
            Row(Div("z", ui_class=axis_label), self.dz, ui_class="items-center no-wrap " + gap_xs),
        )

        # Center — 3 tight inputs with prefix labels instead of floating labels
        self.cx = QInput(ui_model_value=clip.center[0], ui_debounce=300, ui_dense=True, ui_borderless=True,
                         ui_class=input_compact)
        self.cy = QInput(ui_model_value=clip.center[1], ui_debounce=300, ui_dense=True, ui_borderless=True,
                         ui_class=input_compact)
        self.cz = QInput(ui_model_value=clip.center[2], ui_debounce=300, ui_dense=True, ui_borderless=True,
                         ui_class=input_compact)
        self.cx.on_update_model_value(self._set_cx)
        self.cy.on_update_model_value(self._set_cy)
        self.cz.on_update_model_value(self._set_cz)
        center_row = Row(
            Div("x", ui_class=axis_label), self.cx,
            Div("y", ui_class=axis_label), self.cy,
            Div("z", ui_class=axis_label), self.cz,
            ui_class="items-center no-wrap " + gap_xs,
        )

        # Offset
        self.offset = QSlider(ui_min=-1, ui_max=1, ui_step=0.01, ui_model_value=0.0, ui_dense=True, ui_label=True)
        self.offset.on("dblclick", lambda e: self._set_offset(0))
        self.offset.on_update_model_value(self._set_offset)

        super().__init__(
            toggle_row,
            Div("Normal", ui_class=label), dir_block,
            Div("Center", ui_class=label), center_row,
            Div("Offset", ui_class=label), self.offset,
            icon="mdi-box-cutter",
            title="Clipping",
        )
        self.on_mounted(self._update_fields)

    def _factor(self):
        try:
            bb = self.comp.wgpu.scene.bounding_box
        except Exception:
            bb = ((0, 0, 0), (1, 1, 1))
        d = [bb[1][i] - bb[0][i] for i in range(3)]
        return math.sqrt(sum(x * x for x in d)) / 2.0

    def _update_fields(self):
        c = self.comp.clipping
        self.offset.ui_model_value = c.offset / self._factor()
        self.cx.ui_model_value = c.center[0]
        self.cy.ui_model_value = c.center[1]
        self.cz.ui_model_value = c.center[2]
        self.dx.ui_model_value = c.normal[0]
        self.dy.ui_model_value = c.normal[1]
        self.dz.ui_model_value = c.normal[2]

    def _set_offset(self, ev):
        v = ev if isinstance(ev, (int, float)) else ev.value
        if isinstance(ev, (int, float)):
            self.offset.ui_model_value = v
        self.comp.clipping.set_offset(float(v) * self._factor())
        self.comp.wgpu.scene.render()

    def _set_cx(self, ev):
        try: self.comp.clipping.set_x_value(float(ev.value)); self.comp.wgpu.scene.render()
        except (ValueError, TypeError, AttributeError): pass

    def _set_cy(self, ev):
        try: self.comp.clipping.set_y_value(float(ev.value)); self.comp.wgpu.scene.render()
        except (ValueError, TypeError, AttributeError): pass

    def _set_cz(self, ev):
        try: self.comp.clipping.set_z_value(float(ev.value)); self.comp.wgpu.scene.render()
        except (ValueError, TypeError, AttributeError): pass

    def _set_nx(self, ev):
        try:
            v = float(ev) if isinstance(ev, (int, float)) else float(ev.value)
            self.comp.clipping.set_nx_value(v); self.comp.wgpu.scene.render()
        except (ValueError, TypeError, AttributeError): pass

    def _set_ny(self, ev):
        try:
            v = float(ev) if isinstance(ev, (int, float)) else float(ev.value)
            self.comp.clipping.set_ny_value(v); self.comp.wgpu.scene.render()
        except (ValueError, TypeError, AttributeError): pass

    def _set_nz(self, ev):
        try:
            v = float(ev) if isinstance(ev, (int, float)) else float(ev.value)
            self.comp.clipping.set_nz_value(v); self.comp.wgpu.scene.render()
        except (ValueError, TypeError, AttributeError): pass
