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
            ui_model_value=comp.colormap_name.value,
            ui_dense=True,
        )
        self.discrete = QCheckbox(
            ui_label="Discrete",
            ui_model_value=comp.colormap_discrete.value,
        )
        self.ncolors = QInput(
            ui_label="Number of Colors",
            ui_type="number",
            ui_model_value=comp.ncolors_colormap.value,
            ui_dense=True,
        )
        self.minval = QInput(
            ui_label="Min Value",
            ui_type="number",
            ui_dense=True,
            ui_model_value=comp.colormap_min.value,
        )
        self.maxval = QInput(
            ui_label="Max Value",
            ui_type="number",
            ui_dense=True,
            ui_model_value=comp.colormap_max.value,
        )
        self.autoscale = QCheckbox(
            ui_label="Autoscale",
            ui_model_value=comp.colormap_autoscale.value,
        )

        # Two-way bindings
        bind(comp.colormap_autoscale, self.autoscale)
        bind(comp.colormap_discrete, self.discrete)
        bind(comp.colormap_name, self.colormap_select)

        # Min/max use on_change event (not on_update_model_value) and need float conversion
        comp.colormap_min.on_change(
            lambda val, _old: setattr(self.minval, "ui_model_value", val)
        )
        comp.colormap_max.on_change(
            lambda val, _old: setattr(self.maxval, "ui_model_value", val)
        )
        self.minval.on_change(self._update_min)
        self.maxval.on_change(self._update_max)

        # Ncolors needs int conversion
        comp.ncolors_colormap.on_change(
            lambda val, _old: setattr(self.ncolors, "ui_model_value", val)
        )
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
            ncolors = int(self.ncolors.ui_model_value)
            ncolors = max(1, min(32, ncolors))
            self.comp.ncolors_colormap.value = ncolors
            self.comp.colormap.set_n_colors(ncolors)
            self.comp.wgpu.scene.render()
        except ValueError:
            pass

    def _update_min(self, event):
        try:
            val = float(self.minval.ui_model_value)
            self.comp.colormap.set_min(val)
            self.comp.colormap_min.value = val
            self.comp.colormap_autoscale.value = False
            self.comp.wgpu.scene.render()
        except ValueError:
            pass

    def _update_max(self, event):
        try:
            val = float(self.maxval.ui_model_value)
            self.comp.colormap.set_max(val)
            self.comp.colormap_max.value = val
            self.comp.colormap_autoscale.value = False
            self.comp.wgpu.scene.render()
        except ValueError:
            pass

    def _update(self):
        self.autoscale.ui_model_value = self.comp.colormap.autoscale
        self.minval.ui_model_value = float(self.comp.colormap.minval)
        self.maxval.ui_model_value = float(self.comp.colormap.maxval)
        self.discrete.ui_model_value = bool(self.comp.colormap.discrete)
