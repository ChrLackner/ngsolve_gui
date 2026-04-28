from ngapp.components import *

from ngsolve_webgpu import *
import ngsolve as ngs
import netgen.occ as ngocc
from .webgpu_tab import WebgpuTab


class GeometryComponent(WebgpuTab):
    def __init__(self, name, data, app_data):
        self.geo = data["obj"]
        self.selected = None
        self._selection_section = None
        super().__init__(name, data, app_data)

    @property
    def settings(self):
        return self.app_data.get_settings(self.name)

    # -- Keybinding support ---------------------------------------------

    def get_keybindings(self):
        kb = super().get_keybindings()
        kb["modes"].append(("s", "Show", [
            ("e", self.toggle_edges, "Toggle edges"),
        ]))
        kb["modes"].append(("c", "Clipping", self._clipping_mode_bindings()))
        return kb

    def toggle_edges(self):
        edges = self.geo_renderer.edges
        edges.active = not edges.active
        self.settings.set("show_edges", edges.active)
        self.scene.render()

    def _create_meshing_geo(self):
        return ngocc.OCCGeometry(self.geo.shape)

    def _meshing_options(self):
        return {
            "maxh": self.settings.get("maxh", 1000),
            "segmentsperedge": self.settings.get("segments_per_edge", 0.2),
            "curvaturesafety": self.settings.get("curvaturesafety", 1.5),
            "closeedgefac": self.settings.get("closeedgefac", None),
        }

    def create_mesh(self):
        print("Generate mesh...")
        geo = self._create_meshing_geo()
        import netgen.meshing as ngm

        mesh = ngm.Mesh()
        try:
            geo.GenerateMesh(mesh=mesh, **self._meshing_options())
            mesh.Curve(5)
        except Exception as e:
            self.quasar.dialog(
                {
                    "title": "Error generating mesh",
                    "message": str(e),
                }
            )
        mesh = ngs.Mesh(mesh)
        from .mesh import MeshComponent
        self.app_data.add_tab("Mesh_" + self.title, MeshComponent, {"obj": mesh}, self.app_data)

    @property
    def clipping(self):
        return self.app_data.clipping

    def _show_all_shapes(self):
        colors = self.geo_renderer.faces.colors
        for i in range(len(colors) // 4):
            colors[i * 4 + 3] = 1.0
        self.geo_renderer.faces.set_colors(colors)
        colors = self.geo_renderer.edges.colors
        for i in range(len(colors) // 4):
            colors[i * 4 + 3] = 1.0
        self.geo_renderer.edges.set_colors(colors)
        self.wgpu.scene.render()

    def change_maxh(self, event):
        value = event.value
        try:
            if value is None or value == "":
                value = None
            else:
                value = float(value)
                if value <= 0:
                    raise ValueError("Max mesh size must be positive.")
            if self._selection_section:
                self._selection_section.meshsize_input.ui_error = False
            if self.selected[0] == "face":
                face = self.geo.faces[self.selected[1]]
                face.maxh = value if value is not None else 1e99
            elif self.selected[0] == "edge":
                edge = self.geo.edges[self.selected[1]]
                edge.maxh = value if value is not None else 1e99
        except ValueError as e:
            if self._selection_section:
                self._selection_section.meshsize_input.ui_error_message = str(e)
                self._selection_section.meshsize_input.ui_error = True

    def change_name(self, event):
        value = event.value
        try:
            if value == "":
                value = None
            if self.selected[0] == "face":
                face = self.geo.faces[self.selected[1]]
                face.name = value
            elif self.selected[0] == "edge":
                edge = self.geo.edges[self.selected[1]]
                edge.name = value
            if self._selection_section:
                self._selection_section.name_input.ui_error = False
        except ValueError as e:
            if self._selection_section:
                self._selection_section.name_input.ui_error_message = str(e)
                self._selection_section.name_input.ui_error = True

    def _hide_selected_shape(self, event=None):
        if self.selected[0] == "face":
            colors = self.geo_renderer.faces.colors
            colors[self.selected[1] * 4 + 3] = 0.0
            self.geo_renderer.faces.set_colors(colors)
        elif self.selected[0] == "edge":
            colors = self.geo_renderer.edges.colors
            colors[self.selected[1] * 4 + 3] = 0.0
            self.geo_renderer.edges.set_colors(colors)
        self.scene.render()

    def select_face(self, event):
        face_id = event.uint32[1]
        self.selected = ("face", face_id)
        if self._selection_section:
            self._selection_section.update_selection("face", face_id)

    def selected_edge(self, event):
        edge_id = event.uint32[1]
        self.selected = ("edge", edge_id)
        if self._selection_section:
            self._selection_section.update_selection("edge", edge_id)

    def draw(self):
        self.geo_renderer = GeometryRenderer(self.geo, clipping=self.clipping)
        self.geo_renderer.faces.on_select(self.select_face)
        self.geo_renderer.edges.on_select(self.selected_edge)
        self.geo_renderer.edges.active = self.settings.get("show_edges", True)
        scene = self.wgpu.draw([self.geo_renderer], camera=self.app_data.camera)
        self.clipping.center = 0.5 * (scene.bounding_box[1] + scene.bounding_box[0])

        def on_click(event):
            if event["button"] == 2:
                scene.select(event["canvasX"], event["canvasY"])

        scene.input_handler.on_click(on_click)


# Register with the component registry
from .registry import register_component
from .sections import GeometryOptionsSection, GeometrySelectionSection, ClippingSection

register_component("geometry",
    icon="mdi-cube",
    component_class=GeometryComponent,
    sections=[GeometryOptionsSection, GeometrySelectionSection, ClippingSection],
)
