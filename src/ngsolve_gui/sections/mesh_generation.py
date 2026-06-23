"""Mesh generation section — meshing parameters and Create Mesh action.

Shown only in geometry scenes. Contains the numeric inputs for controlling
mesh generation and the action button to trigger it.
"""

from ngapp.components import *

from ..prop_widgets import Section, field
from ..cerbsim_style import row2


class MeshingInput(QInput):
    """A validated numeric input for meshing parameters."""

    def __init__(self, observable, **kwargs):
        self.observable = observable
        super().__init__(
            ui_model_value=observable,
            ui_type="number",
            ui_dense=True,
            **kwargs,
        )
        self.observable.on_change(self._validate)
        self.ui_error = False
        self.ui_error_message = ""

    def _validate(self, value, _old):
        if value is not None and value != "" and float(value) <= 0:
            self.ui_error = True
            self.ui_error_message = "Must be positive"
        else:
            self.ui_error = False
            self.ui_error_message = ""


class MeshGenerationSection(Section):
    """Meshing parameters and Create Mesh button for geometry scenes."""

    section_key = "meshing"

    def __init__(self, comp):
        self.comp = comp

        self.maxh = MeshingInput(comp.maxh)
        self.segments = MeshingInput(comp.segments_per_edge)
        self.curvature = MeshingInput(comp.curvaturesafety)
        self.closeedge = MeshingInput(comp.closeedgefac)

        self.create_btn = QBtn(
            ui_icon="mdi-vector-triangle",
            ui_label="Generate mesh",
            ui_color="primary",
            ui_no_caps=True,
            ui_class="full-width q-mt-xs",
        )
        self.create_btn.on_click(self._create_mesh)

        super().__init__(
            Div(
                field("Max mesh size", self.maxh),
                field("Segments / edge", self.segments),
                ui_class=row2,
            ),
            Div(
                field("Curvature safety", self.curvature),
                field("Close-edge fac.", self.closeedge),
                ui_class=row2,
            ),
            self.create_btn,
            icon="mdi-vector-triangle",
            title="Meshing",
            info="Generate a tetrahedral mesh from this geometry.",
        )

    def _create_mesh(self, *args):
        self.create_btn.ui_loading = True

        def _done():
            self.create_btn.ui_loading = False

        try:
            self.comp.create_mesh(on_done=_done)
        except Exception:
            self.create_btn.ui_loading = False
            raise
