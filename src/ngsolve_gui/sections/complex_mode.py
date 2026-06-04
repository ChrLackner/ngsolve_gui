"""Complex mode section — visualization mode for complex-valued functions.

Only shown when the coefficient function is complex. Allows switching between
real/imag/abs/arg display and controlling phase animation.
"""

from ngapp.components import *

from ..prop_widgets import Section, Toggle, field


class ComplexSection(Section):
    """Complex number visualization controls."""

    section_key = "complex"

    def __init__(self, comp):
        self.comp = comp
        if not comp.cf.is_complex:
            raise ValueError("Not a complex function")

        self.mode_select = QSelect(
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

        self.speed = QSlider(
            ui_model_value=comp.complex_speed,
            ui_min=0.1, ui_max=5.0, ui_step=0.1,
            ui_dense=True, ui_label=True,
        )

        super().__init__(
            field("Display mode", self.mode_select),
            Toggle("Animate phase", comp.complex_animate),
            field("Animation speed", self.speed),
            icon="mdi-sine-wave",
            title="Complex",
        )
