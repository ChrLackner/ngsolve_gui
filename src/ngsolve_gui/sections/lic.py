"""LIC section — Line Integral Convolution on the clipping plane.

LIC paints the (3D vector) field's flow as a dense streamline texture on the
cutting plane — a 3D-only, vector-only clipping-plane overlay, sibling to the
clipping function and clipping vectors. The header switch is bound to
``lic_visible``; the body holds the convolution parameters.

Only applicable when ``comp.lic`` exists (3D vector field on a 3D mesh).
"""

from ngapp.components import *

from ..prop_widgets import Section, Chip, chip_row, field


class LicSection(Section):
    section_key = "lic"

    def __init__(self, comp):
        self.comp = comp
        if getattr(comp, "lic", None) is None:
            raise ValueError("LIC not applicable (needs a 3D vector field)")

        # Sliders two-way bind to the Observables; the component's on_change
        # handlers push the change to the GPU renderer.
        kernel_length = QSlider(
            ui_model_value=comp.lic_kernel_length, ui_min=5, ui_max=80, ui_step=1,
            ui_dense=True, ui_label=True,
        )
        thickness = QSlider(
            ui_model_value=comp.lic_thickness, ui_min=1, ui_max=30, ui_step=1,
            ui_dense=True, ui_label=True,
        )
        contrast = QSlider(
            ui_model_value=comp.lic_contrast, ui_min=0.0, ui_max=1.0, ui_step=0.05,
            ui_dense=True, ui_label=True,
        )
        self.resolution = QSelect(
            ui_options=["256","512", "1024", "2048", "4096"],
            ui_model_value=str(comp.lic_resolution.value),
            ui_dense=True, ui_filled=True,
        )
        self.resolution.on_update_model_value(self._update_resolution)

        super().__init__(
            field("Kernel length", kernel_length),
            field("Line width", thickness),
            field("Contrast", contrast),
            chip_row(
                Chip("Oriented", "mdi-arrow-right-thin", comp.lic_oriented),
                Chip("Animate", "mdi-play", comp.lic_animate),
            ),
            field("Resolution", self.resolution),
            icon="mdi-blur",
            title="LIC",
            switchable=True,
            observable=comp.lic_visible,
            info="Line Integral Convolution: paints the vector field's flow as a "
                 "dense streamline texture on the clipping plane.",
        )

    def _update_resolution(self, event):
        try:
            self.comp.lic_resolution.value = int(event.value)
        except (ValueError, TypeError):
            pass
