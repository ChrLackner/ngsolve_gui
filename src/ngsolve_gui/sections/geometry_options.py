from ngapp.components import *


class MeshingInput(QInput):
    def __init__(self, comp, key, label, model_value, type="number", **kwargs):
        self.comp = comp
        self.key = key
        super().__init__(
            ui_label=label, ui_model_value=model_value, ui_type=type, **kwargs
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
            self.comp.settings.set(self.key, value)
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
            ui_model_value=comp.settings.get("show_edges", True),
        )
        self.show_edges.on_update_model_value(self.update_show_edges)

        self.create_mesh_btn = QBtn(
            ui_label="Create Mesh",
            ui_color="primary",
            ui_flat=True,
        )
        self.create_mesh_btn.on_click(self._create_mesh)

        self.maxh = MeshingInput(
            label="Max Mesh Size",
            key="maxh",
            model_value=comp.settings.get("maxh", 1000),
            comp=comp,
            ui_dense=True,
        )
        self.segmentsperedge = MeshingInput(
            label="Segments per Edge",
            key="segmentsperedge",
            model_value=comp.settings.get("segments_per_edge", 0.2),
            comp=comp,
            ui_dense=True,
        )
        self.curvaturefactor = MeshingInput(
            label="Curvature Factor",
            key="curvaturesafety",
            model_value=comp.settings.get("curvaturesafety", 1.5),
            comp=comp,
            ui_dense=True,
        )
        self.closeedgefac = MeshingInput(
            label="Close Edge Factor",
            key="closeedgefac",
            model_value=comp.settings.get("closeedgefac", None),
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

    def update_show_edges(self, event):
        self.comp.settings.set("show_edges", event.value)
        self.comp.geo_renderer.edges.active = event.value
        self.comp.scene.render()
