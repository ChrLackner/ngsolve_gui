from ngapp.components import *


class MeshingInput(QInput):
    def __init__(self, comp, observable, label, type="number", **kwargs):
        self.comp = comp
        self.observable = observable
        super().__init__(
            ui_label=label, ui_model_value=observable.value, ui_type=type, **kwargs
        )
        self.on_update_model_value(self.update_value)
        self.ui_error = False
        self.ui_error_message = ""

    def update_value(self, event):
        try:
            value = event.value
            if value is None or value == "":
                value = None
            else:
                value = float(value)
                if value <= 0:
                    raise ValueError("Value must be positive.")
            self.ui_error = False
            self.observable.value = value
        except ValueError as e:
            self.set_error(str(e))

    def set_error(self, message):
        self.ui_error = True
        self.ui_error_message = message

    def clear_error(self):
        self.ui_error = False
        self.ui_error_message = ""


class GeometryOptionsSection(QExpansionItem):
    def __init__(self, comp):
        self.comp = comp

        self.show_edges = QCheckbox(
            ui_label="Show Edges",
            ui_model_value=comp.show_edges.value,
        )
        bind(comp.show_edges, self.show_edges)

        self.create_mesh_btn = QBtn(
            ui_label="Create Mesh",
            ui_color="primary",
            ui_flat=True,
        )
        self.create_mesh_btn.on_click(self._create_mesh)

        self.maxh = MeshingInput(
            label="Max Mesh Size",
            observable=comp.maxh,
            comp=comp,
            ui_dense=True,
        )
        self.segmentsperedge = MeshingInput(
            label="Segments per Edge",
            observable=comp.segments_per_edge,
            comp=comp,
            ui_dense=True,
        )
        self.curvaturefactor = MeshingInput(
            label="Curvature Factor",
            observable=comp.curvaturesafety,
            comp=comp,
            ui_dense=True,
        )
        self.closeedgefac = MeshingInput(
            label="Close Edge Factor",
            observable=comp.closeedgefac,
            comp=comp,
            ui_dense=True,
        )

        super().__init__(
            self.show_edges,
            self.create_mesh_btn,
            Heading("Meshing Parameters", 6),
            self.maxh,
            self.segmentsperedge,
            self.curvaturefactor,
            self.closeedgefac,
            ui_icon="mdi-cube-outline",
            ui_label="Geometry Options",
        )

    def _create_mesh(self):
        self.create_mesh_btn.ui_loading = True
        try:
            self.comp.create_mesh()
        finally:
            self.create_mesh_btn.ui_loading = False

