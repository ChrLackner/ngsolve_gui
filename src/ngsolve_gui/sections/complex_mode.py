"""Complex mode section — visualization mode for complex-valued functions.

Only shown when the coefficient function is complex. Allows switching between
real/imag/abs/arg display and controlling phase animation.
"""

from ngapp.components import *


class ComplexSection(QExpansionItem):
    """Complex number visualization controls."""

    def __init__(self, comp):
        self.comp = comp
        if not comp.cf.is_complex:
            raise ValueError("Not a complex function")

        self.mode_select = QSelect(
            ui_label="Display Mode",
            ui_options=[
                {"label": "Real", "value": "real"},
                {"label": "Imaginary", "value": "imag"},
                {"label": "Absolute", "value": "abs"},
                {"label": "Phase (Arg)", "value": "arg"},
            ],
            ui_model_value=comp.complex_mode,
            ui_emit_value=True,
            ui_map_options=True,
            ui_dense=True,
        )

        self.animate = QCheckbox(
            "Animate Phase",
            ui_model_value=comp.complex_animate,
            ui_dense=True,
        )

        speed_label = Div("Animation Speed", ui_style="font-size: 0.8rem; color: #78909c; padding-top: 4px;")
        self.speed = QSlider(
            ui_model_value=comp.complex_speed,
            ui_min=0.1,
            ui_max=5.0,
            ui_step=0.1,
            ui_dense=True,
            ui_label=True,
            ui_style="padding: 0 4px;",
        )

        super().__init__(
            self.mode_select,
            self.animate,
            speed_label,
            self.speed,
            ui_icon="mdi-sine-wave",
            ui_label="Complex",
            ui_dense=True,
        )
