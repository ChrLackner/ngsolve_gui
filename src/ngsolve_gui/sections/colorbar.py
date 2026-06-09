"""Colormap section — color scale settings for function visualization.

Compact layout: autoscale + min/max in one row, always editable.
Editing min/max automatically disables autoscale.
Observable formatter handles scientific notation display automatically.
Advanced settings (colormap choice, discrete, ncolors) behind nested expander.
"""

from ngapp.components import *

from ..prop_widgets import Section, Toggle, Chip, chip_row, field, MoreDisclosure, ColormapBar
from ..cerbsim_style import gap_xs, input_compact, row2


class ColorbarSection(Section):
    section_key = "colormap"

    def __init__(self, comp):
        self.comp = comp

        # -- Colormap gradient swatch + Auto + Min/Max --
        self.bar = ColormapBar(comp)

        self.color_component = None
        component_field = None
        if getattr(comp.cf, "dim", 1) > 1:
            opts = ["|u|"] + [str(i) for i in range(1, comp.cf.dim + 1)]
            self.color_component = QSelect(
                ui_options=opts, ui_model_value=opts[0], ui_dense=True, ui_filled=True,
            )
            self.color_component.on_update_model_value(self._update_color_component)
            component_field = field("Color by", self.color_component)
        # The observables have a formatter, so QInput shows e.g. "7.957e-06"
        self.minval = QInput(
            ui_type="number", ui_dense=True, ui_filled=True, ui_model_value=comp.colormap_min,
        )
        self.maxval = QInput(
            ui_type="number", ui_dense=True, ui_filled=True, ui_model_value=comp.colormap_max,
        )
        range_row = Div(
            field("Min", self.minval), field("Max", self.maxval), ui_class=row2,
        )

        # -- Advanced (colormap choice, discrete, ncolors) --
        self.colormap_select = QSelect(
            ui_options=[
                "rainbow", "turbo", "viridis", "plasma", "cet_l20",
                "matlab:jet", "matplotlib:coolwarm",
            ],
            ui_model_value=comp.colormap_name,
            ui_dense=True, ui_filled=True,
        )
        self.discrete = Chip("Discrete", "mdi-grid", comp.colormap_discrete)
        self.ncolors = QInput(
            ui_type="number", ui_model_value=comp.ncolors_colormap, ui_dense=True,
            ui_filled=True, ui_class=input_compact,
        )
        self.ncolors.on_change(self._update_ncolors)
        discrete_row = Row(
            self.discrete, field("N colors", self.ncolors),
            ui_class="items-end " + gap_xs,
        )
        advanced = MoreDisclosure(
            field("Colormap", self.colormap_select),
            discrete_row,
            label_more="Advanced", label_less="Advanced",
        )

        # Min/max user edits → disable autoscale
        self.minval.on_change(self._update_min)
        self.maxval.on_change(self._update_max)

        body = [self.bar]
        if component_field is not None:
            body.append(component_field)
        body += [
            Toggle("Autoscale to data", comp.colormap_autoscale),
            range_row,
            advanced,
        ]
        super().__init__(
            *body,
            icon="mdi-palette",
            title="Colormap",
            opened=True,
        )
        self.on_mounted(self._update)

    def _update_color_component(self, event):
        idx = self.color_component.ui_options.index(self.color_component.ui_model_value)
        comp = self.comp
        if comp.elements2d is not None:
            comp.elements2d.set_component(idx - 1)   # idx 0 (|u|) → -1 = magnitude
        if comp.clippingcf is not None:
            comp.clippingcf.set_component(idx - 1)
        comp.colorbar.set_needs_update()
        comp.wgpu.scene.render()

    def _update_ncolors(self, event):
        try:
            ncolors = max(1, min(32, self.comp.ncolors_colormap.value))
            self.comp.colormap.set_n_colors(ncolors)
            self.comp.wgpu.scene.render()
        except (ValueError, TypeError):
            pass

    def _update_min(self, event):
        try:
            val = float(event.value)
            self.comp.colormap_min.value = val
            self.comp.colormap.set_min(val)
            self.comp.colormap_autoscale.value = False
            self.comp.wgpu.scene.render()
        except (ValueError, TypeError):
            pass

    def _update_max(self, event):
        try:
            val = float(event.value)
            self.comp.colormap_max.value = val
            self.comp.colormap.set_max(val)
            self.comp.colormap_autoscale.value = False
            self.comp.wgpu.scene.render()
        except (ValueError, TypeError):
            pass

    def _update(self):
        # Sync observables to the live colormap state (no-op when already equal,
        # so this won't re-trigger autoscale on mount).
        self.comp.colormap_autoscale.value = self.comp.colormap.autoscale
        self.comp.colormap_discrete.value = bool(self.comp.colormap.discrete)
        self.minval.ui_model_value = self.comp.colormap_min.display_value
        self.maxval.ui_model_value = self.comp.colormap_max.display_value
