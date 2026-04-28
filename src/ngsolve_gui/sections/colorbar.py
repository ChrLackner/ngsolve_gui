from ngapp.components import *


class ColorbarSection(QExpansionItem):
    def __init__(self, comp):
        self.comp = comp
        autoscale, discrete, minval, maxval = comp.settings.get(
            "colormap", (True, False, 0.0, 1.0)
        )
        ncolors = comp.settings.get("ncolors_colormap", 8)
        color_map_name = comp.settings.get("colormap_name", "matlab:jet")
        self.colormap = QSelect(
            ui_label="Colormap",
            ui_options=[
                "viridis",
                "plasma",
                "cet_l20",
                "matlab:jet",
                "matplotlib:coolwarm",
            ],
            ui_model_value=color_map_name,
            ui_dense=True,
        )
        self.discrete = QCheckbox(
            ui_label="Discrete",
            ui_model_value=discrete,
        )
        self.ncolors = QInput(
            ui_label="Number of Colors",
            ui_type="number",
            ui_model_value=ncolors,
            ui_dense=True,
        )
        self.ncolors.on_change(self.update_ncolors)
        self.discrete.on_update_model_value(self.update_discrete)
        self.colormap.on_update_model_value(self.update_colormap)
        self.minval = QInput(
            ui_label="Min Value",
            ui_type="number",
            ui_dense=True,
            ui_model_value=minval,
        )
        self.maxval = QInput(
            ui_label="Max Value",
            ui_type="number",
            ui_dense=True,
            ui_model_value=maxval,
        )
        self.minval.on_change(self.update_min)
        self.maxval.on_change(self.update_max)
        self.autoscale = QCheckbox(ui_label="Autoscale", ui_model_value=autoscale)
        self.autoscale.on_update_model_value(self.update_autoscale)

        super().__init__(
            self.autoscale,
            self.discrete,
            Row(self.minval, self.maxval),
            Row(self.colormap, self.ncolors),
            ui_icon="mdi-palette-outline",
            ui_label="Colorbar",
        )
        self.on_mounted(self._update)

    def update_colormap(self, event):
        self.comp.colormap.set_colormap(self.colormap.ui_model_value)
        self.comp.redraw()
        self.comp.wgpu.scene.render()

    def update_ncolors(self, event):
        try:
            ncolors = int(self.ncolors.ui_model_value)
            if ncolors < 1:
                ncolors = 1
            if ncolors > 32:
                ncolors = 32
            self.comp.colormap.set_n_colors(ncolors)
            self.comp.wgpu.scene.render()
            self.comp.settings.set("ncolors_colormap", ncolors)
        except ValueError:
            pass

    def update_autoscale(self, event):
        if getattr(self, "_updating_fields", False):
            return
        if self.autoscale.ui_model_value:
            self.comp.colormap.autoscale = True
            self.comp.wgpu.scene.redraw(blocking=True)
            # Update fields without triggering callbacks
            self._updating_fields = True
            self.minval.ui_model_value = float(self.comp.colormap.minval)
            self.maxval.ui_model_value = float(self.comp.colormap.maxval)
            self._updating_fields = False
        else:
            self.comp.colormap.autoscale = False
        self.update_settings()

    def update_settings(self):
        self.comp.settings.set(
            "colormap",
            (
                self.comp.colormap.autoscale,
                self.comp.colormap.discrete,
                self.comp.colormap.minval,
                self.comp.colormap.maxval,
            ),
        )

    def update_min(self, event):
        if getattr(self, "_updating_fields", False):
            return
        try:
            self.comp.colormap.set_min(float(self.minval.ui_model_value))
            self.autoscale.ui_model_value = False
            self.comp.wgpu.scene.render()
            self.update_settings()
        except ValueError:
            pass

    def update_max(self, event):
        if getattr(self, "_updating_fields", False):
            return
        try:
            self.comp.colormap.set_max(float(self.maxval.ui_model_value))
            self.autoscale.ui_model_value = False
            self.comp.wgpu.scene.render()
            self.update_settings()
        except ValueError:
            pass

    def update_discrete(self, event):
        self.comp.colormap.set_discrete(self.discrete.ui_model_value)
        self.comp.wgpu.scene.render()
        self.update_settings()

    def _update(self):
        self._updating_fields = True
        self.autoscale.ui_model_value = self.comp.colormap.autoscale
        self.minval.ui_model_value = float(self.comp.colormap.minval)
        self.maxval.ui_model_value = float(self.comp.colormap.maxval)
        self.discrete.ui_model_value = bool(self.comp.colormap.discrete)
        self._updating_fields = False
