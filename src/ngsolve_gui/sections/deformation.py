from ngapp.components import *
from webgpu.canvas import debounce


class DeformationSection(QExpansionItem):
    def __init__(self, comp):
        self.comp = comp
        if comp.deformation is None and not (comp.cf.dim == 1 and comp.mesh.dim < 3):
            raise ValueError("Deformation not applicable")
        self._enable = QCheckbox(
            ui_label="Enable Deformation",
            ui_model_value=comp.deformation_enabled.value,
        )
        bind(comp.deformation_enabled, self._enable)

        self._deform_scale = QInput(
            ui_label="Deformation Scale",
            ui_type="number",
            ui_model_value=comp.deformation_scale.value,
            ui_dense=True,
        )
        self._deform_scale2 = QSlider(
            ui_model_value=comp.deformation_scale2.value,
            ui_min=0.0,
            ui_max=1.0,
            ui_step=0.01,
        )

        # Observable → widget sync
        comp.deformation_scale.on_change(
            lambda val, _old: setattr(self._deform_scale, "ui_model_value", val)
        )
        comp.deformation_scale2.on_change(
            lambda val, _old: setattr(self._deform_scale2, "ui_model_value", val)
        )

        # Widget → observable (with debounce and float conversion)
        self._deform_scale.on_change(self._on_scale_change)
        self._deform_scale2.on_update_model_value(self._on_scale2_change)

        super().__init__(
            self._enable,
            self._deform_scale2,
            self._deform_scale,
            ui_icon="mdi-arrow-expand-all",
            ui_label="Deformation",
        )

    @debounce
    def _on_scale_change(self, event):
        try:
            self.comp.deformation_scale.value = float(self._deform_scale.ui_model_value)
        except ValueError:
            pass

    def _on_scale2_change(self, event):
        try:
            self.comp.deformation_scale2.value = float(self._deform_scale2.ui_model_value)
        except ValueError:
            pass
