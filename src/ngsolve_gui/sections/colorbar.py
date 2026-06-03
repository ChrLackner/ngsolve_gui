"""Colormap section — color scale settings for function visualization.

Compact layout: autoscale + min/max in one row, always editable.
Editing min/max automatically disables autoscale.
Observable formatter handles scientific notation display automatically.
Advanced settings (colormap choice, discrete, ncolors) behind nested expander.
"""

from ngapp.components import *

from ..cerbsim_style import gap_xs, input_compact, subexpander_header


class ColorbarSection(QExpansionItem):
    def __init__(self, comp):
        self.comp = comp

        # -- Auto + Min + Max in one row --
        # The observables have a formatter, so QInput shows e.g. "7.957e-06"
        self.autoscale = QCheckbox(
            "Auto", ui_model_value=comp.colormap_autoscale, ui_dense=True,
        )
        self.minval = QInput(
            ui_type="number", ui_dense=True,
            ui_model_value=comp.colormap_min,
            ui_stack_label=True, ui_label="Min",
        )
        self.maxval = QInput(
            ui_type="number", ui_dense=True,
            ui_model_value=comp.colormap_max,
            ui_stack_label=True, ui_label="Max",
        )
        range_row = Row(
            self.autoscale, self.minval, self.maxval,
            ui_class="items-center no-wrap " + gap_xs,
        )

        # -- Advanced (colormap choice, discrete, ncolors) --
        self.colormap_select = QSelect(
            ui_label="Colormap",
            ui_options=[
                "rainbow", "turbo", "viridis", "plasma", "cet_l20",
                "matlab:jet", "matplotlib:coolwarm",
            ],
            ui_model_value=comp.colormap_name,
            ui_dense=True,
        )
        self.discrete = QCheckbox(
            "Discrete", ui_model_value=comp.colormap_discrete, ui_dense=True,
        )
        self.ncolors = QInput(
            ui_label="N colors", ui_type="number",
            ui_model_value=comp.ncolors_colormap, ui_dense=True,
            ui_class=input_compact,
        )
        self.ncolors.on_change(self._update_ncolors)
        discrete_row = Row(
            self.discrete, self.ncolors,
            ui_class="items-center " + gap_xs,
        )
        advanced = QExpansionItem(
            self.colormap_select,
            discrete_row,
            ui_label="Advanced",
            ui_dense=True,
            ui_dense_toggle=True,
            ui_header_class=str(subexpander_header),
        )

        # Min/max user edits → disable autoscale
        self.minval.on_change(self._update_min)
        self.maxval.on_change(self._update_max)

        super().__init__(
            range_row,
            advanced,
            ui_icon="mdi-palette",
            ui_label="Colormap",
            ui_default_opened=True,
            ui_dense=True,
        )
        self.on_mounted(self._update)

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
        self.autoscale.ui_model_value = self.comp.colormap.autoscale
        self.minval.ui_model_value = self.comp.colormap_min.display_value
        self.maxval.ui_model_value = self.comp.colormap_max.display_value
        self.discrete.ui_model_value = bool(self.comp.colormap.discrete)
