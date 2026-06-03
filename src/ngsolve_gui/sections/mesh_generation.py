"""Mesh generation section — meshing parameters and Create Mesh action.

Shown only in geometry scenes. Contains the numeric inputs for controlling
mesh generation and the action button to trigger it.
"""

from ngapp.components import *


class MeshingInput(QInput):
    """A validated numeric input for meshing parameters."""

    def __init__(self, observable, label, **kwargs):
        self.observable = observable
        super().__init__(
            ui_label=label,
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


class MeshGenerationSection(QExpansionItem):
    """Meshing parameters and Create Mesh button for geometry scenes."""

    def __init__(self, comp):
        self.comp = comp

        self.maxh = MeshingInput(observable=comp.maxh, label="Max Mesh Size")
        self.segments = MeshingInput(observable=comp.segments_per_edge, label="Segments / Edge")
        self.curvature = MeshingInput(observable=comp.curvaturesafety, label="Curvature Safety")
        self.closeedge = MeshingInput(observable=comp.closeedgefac, label="Close Edge Fac.")

        self.create_btn = QBtn(
            ui_icon="mdi-vector-triangle",
            ui_label="Create Mesh",
            ui_color="primary",
            ui_flat=True,
            ui_no_caps=True,
            ui_class="q-mt-sm",
        )
        self.create_btn.on_click(self._create_mesh)

        super().__init__(
            self.maxh,
            self.segments,
            self.curvature,
            self.closeedge,
            self.create_btn,
            ui_icon="mdi-vector-triangle",
            ui_label="Meshing",
            ui_dense=True,
        )

    def _create_mesh(self, *args):
        self.create_btn.ui_loading = True
        try:
            self.comp.create_mesh()
        finally:
            self.create_btn.ui_loading = False
