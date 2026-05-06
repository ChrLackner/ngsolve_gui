from ngapp.components import *


class ColorbarSection(QExpansionItem):
    def __init__(self, comp):
        self.comp = comp
        self.colormap_select = QSelect(
            ui_label="Colormap",
            ui_options=[
                "viridis",
                "plasma",
                "cet_l20",
                "matlab:jet",
                "matplotlib:coolwarm",
            ],
            ui_model_value=comp.colormap_name,
            ui_dense=True,
        )
        self.discrete = QCheckbox(
            ui_label="Discrete",
            ui_model_value=comp.colormap_discrete,
        )
        self.ncolors = QInput(
            ui_label="Number of Colors",
            ui_type="number",
            ui_model_value=comp.ncolors_colormap,
            ui_dense=True,
        )
        self.minval = QInput(
            ui_label="Min Value",
            ui_type="number",
            ui_dense=True,
            ui_model_value=comp.colormap_min,
        )
        self.maxval = QInput(
            ui_label="Max Value",
            ui_type="number",
            ui_dense=True,
            ui_model_value=comp.colormap_max,
        )
        self.autoscale = QCheckbox(
            ui_label="Autoscale",
            ui_model_value=comp.colormap_autoscale,
        )

        # Min/max manual edits disable autoscale
        self.minval.on_change(self._update_min)
        self.maxval.on_change(self._update_max)

        # Ncolors needs to update the colormap object
        self.ncolors.on_change(self._update_ncolors)

        super().__init__(
            self.autoscale,
            self.discrete,
            Row(self.minval, self.maxval),
            Row(self.colormap_select, self.ncolors),
            ui_icon="mdi-palette-outline",
            ui_label="Colorbar",
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
        self.minval.ui_model_value = float(self.comp.colormap.minval)
        self.maxval.ui_model_value = float(self.comp.colormap.maxval)
        self.discrete.ui_model_value = bool(self.comp.colormap.discrete)
