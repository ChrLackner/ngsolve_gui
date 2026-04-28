from ngapp.components import *
from webgpu.canvas import debounce


class DeformationSection(QExpansionItem):
    def __init__(self, comp):
        self.comp = comp
        if comp.deformation is None and not (comp.cf.dim == 1 and comp.mesh.dim < 3):
            raise ValueError("Deformation not applicable")
        self._enable = QCheckbox(
            ui_label="Enable Deformation",
            ui_model_value=comp.settings.get("deformation_enabled", False),
        )
        self._enable.on_update_model_value(self.enable)
        self._deform_scale = QInput(
            ui_label="Deformation Scale",
            ui_type="number",
            ui_model_value=comp.settings.get("deformation_scale", 1.0),
            ui_dense=True,
        )
        self._deform_scale2 = QSlider(
            ui_model_value=comp.settings.get("deformation_scale2", 1.0),
            ui_min=0.0,
            ui_max=1.0,
            ui_step=0.01,
        )
        self._deform_scale.on_change(self.change_scale)
        self._deform_scale2.on_update_model_value(self.change_scale)

        super().__init__(
            self._enable,
            self._deform_scale2,
            self._deform_scale,
            ui_icon="mdi-arrow-expand-all",
            ui_label="Deformation",
        )

    def enable(self, event):
        self.comp.settings.set("deformation_enabled", self._enable.ui_model_value)
        if hasattr(self.comp, "mdata"):
            scale = 0.0
            if self._enable.ui_model_value:
                try:
                    scale = float(self._deform_scale.ui_model_value) * float(
                        self._deform_scale2.ui_model_value
                    )
                except ValueError:
                    scale = 1.0
            self.comp.mdata.deformation_scale = scale
        self.comp.wgpu.scene.render()

    @debounce
    def change_scale(self, event):
        try:
            self.comp.settings.set(
                "deformation_scale", float(self._deform_scale.ui_model_value)
            )
            self.comp.settings.set(
                "deformation_scale2", float(self._deform_scale2.ui_model_value)
            )
            scale = float(self._deform_scale.ui_model_value) * float(
                self._deform_scale2.ui_model_value
            )
            self.comp.mdata.deformation_scale = scale
            self.comp.wgpu.scene.render()
        except ValueError:
            pass
