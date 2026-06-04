from ngapp.components import *

from ..prop_widgets import Section, Segmented, field


class DeformationSection(Section):
    section_key = "deformation"

    def __init__(self, comp):
        self.comp = comp
        if comp.deformation is None and not (comp.cf.dim == 1 and comp.mesh.dim < 3):
            raise ValueError("Deformation not applicable")

        self._deform_scale2 = QSlider(
            ui_model_value=comp.deformation_scale2,
            ui_min=0.0, ui_max=1.0, ui_step=0.01, ui_dense=True, ui_label=True,
        )
        presets = Segmented(
            [("0.5", "0.5×"), ("1", "1×"), ("2", "2×"), ("5", "5×")],
            "1", self._set_scale,
        )

        super().__init__(
            field("Scale", self._deform_scale2),
            presets,
            icon="mdi-arrow-expand-all",
            title="Deformation",
            switchable=True,
            observable=comp.deformation_enabled,
            info="Warp the mesh by the displacement field to see how it deforms.",
        )

    def _set_scale(self, val):
        try:
            self.comp.deformation_scale.value = float(val)
        except (ValueError, TypeError):
            pass
