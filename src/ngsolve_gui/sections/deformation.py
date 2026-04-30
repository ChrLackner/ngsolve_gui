from ngapp.components import *


class DeformationSection(QExpansionItem):
    def __init__(self, comp):
        self.comp = comp
        if comp.deformation is None and not (comp.cf.dim == 1 and comp.mesh.dim < 3):
            raise ValueError("Deformation not applicable")
        self._enable = QCheckbox(
            ui_label="Enable Deformation",
            ui_model_value=comp.deformation_enabled,
        )

        self._deform_scale = QInput(
            ui_label="Deformation Scale",
            ui_type="number",
            ui_model_value=comp.deformation_scale,
            ui_dense=True,
        )
        self._deform_scale2 = QSlider(
            ui_model_value=comp.deformation_scale2,
            ui_min=0.0,
            ui_max=1.0,
            ui_step=0.01,
        )

        super().__init__(
            self._enable,
            self._deform_scale2,
            self._deform_scale,
            ui_icon="mdi-arrow-expand-all",
            ui_label="Deformation",
        )
