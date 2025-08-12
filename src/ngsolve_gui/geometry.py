from ngapp.components import *

from ngsolve_webgpu import *
import ngsolve as ngs
import netgen.occ as ngocc

from .clipping import ClippingSettings

class MeshingInput(QInput):
    def __init__(self, comp, key, label, model_value, type="number"):
        self.comp = comp
        self.key = key
        super().__init__(ui_label=label,
                         ui_model_value=model_value,
                         ui_type=type)
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

class Sidebar(QDrawer):
    def __init__(self, comp):
        self.geo_comp = comp
        create_mesh = QItem(QItemSection("Create Mesh"), ui_clickable=True)

        clipping_menu = ClippingSettings(comp)

        self.maxh = MeshingInput(label="Max Mesh Size",
                                 key="maxh",
                                 model_value=comp.settings.get("maxh", 1000),
                                 comp=comp)
        self.segmentsperedge = MeshingInput(
                label="Segments per Edge",
                key="segmentsperedge",
                model_value=comp.settings.get("segments_per_edge", 0.2),
                comp=comp,
                )
        self.curvaturefactor = MeshingInput(
                label="Curvature Factor",
                key="curvaturesafety",
                model_value=comp.settings.get("curvaturesafety", 1.5),
                comp=comp,
                )
        self.closeedgefac = MeshingInput(
            label="Close Edge Factor",
            key="closeedgefac",
            model_value=comp.settings.get("closeedgefac", None),
            comp=comp)
            

        mparam = QCardSection(Row(self.maxh), Row(self.segmentsperedge),
                              Row(self.curvaturefactor), Row(self.closeedgefac))
        mparam_menu = QMenu(
            QCard(QCardSection(Heading("Meshing Parameters", 5)), mparam),
            ui_anchor="top right",
        )
        meshing_parameters = QItem(
            mparam_menu, QItemSection("Meshing Parameters"), ui_clickable=True
        )
        create_mesh.on_click(self.geo_comp.create_mesh)
        items = [create_mesh, clipping_menu, meshing_parameters]
        qlist = QList(*items, ui_padding=True, ui_class="menu-list")
        super().__init__(qlist, ui_width=200, ui_bordered=True, ui_model_value=True)


class GeometryComponent(QLayout):
    def __init__(
        self, title, geometry, global_clipping, app_data, settings, global_camera
    ):
        self.title = title
        self.settings = settings
        self.app_data = app_data
        self.geo = geometry
        self.wgpu = WebgpuComponent()
        self.wgpu.ui_style = "width: 100%;height: calc(100vh - 140px);"
        self.global_clipping = global_clipping
        self.heading_selection_menu = Heading("Selection", 7)
        self.meshsize_input = QInput(ui_label="Mesh Size", ui_type="number",
                                     ui_debounce=500)
        self.meshsize_input.on_update_model_value(self.change_maxh)
        self.name_input = QInput(ui_label="Name", ui_type="text",
                                 ui_debounce=500)
        self.name_input.on_update_model_value(self.change_name)

        hide_btn = QBtn("Hide", ui_color="secondary")
        hide_btn.on_click(self._hide_selected_shape)
        self.selection_text = Div(Row(self.meshsize_input),
                                  Row(self.name_input),
                                  Row(hide_btn, ui_style="margin-top: 10px;"))
        self.selection_menu = QMenu(
            QCard(QCardSection(self.heading_selection_menu,
                               self.selection_text)),
            # ui_touch_position=True,
            # ui_target=self.wgpu._js_component,
            ui_anchor="top left",
            ui_no_parent_event=True,
        )
        self.global_camera = global_camera
        self.sidebar = Sidebar(self)
        self.draw()
        self.error_dialog = QDialog()
        super().__init__(
            self.sidebar,
            QPageContainer(QPage(self.wgpu,
                                 self.selection_menu,
                                 self.error_dialog)),
            ui_container=True,
            ui_view="lhh LpR lff",
            ui_style="height: calc(100vh - 140px); width: 100%;",
        )

    def _create_meshing_geo(self):
        return ngocc.OCCGeometry(self.geo.shape)

    def _meshing_options(self):
        return {"maxh": self.settings.get("maxh", 1000),
                "segmentsperedge": self.settings.get("segments_per_edge", 0.2),
                "curvaturesafety": self.settings.get("curvaturesafety", 1.5),
                "closeedgefac": self.settings.get("closeedgefac", None)}

    def create_mesh(self, *args):
        print("Generate mesh...")
        geo = self._create_meshing_geo()
        mesh = ngs.Mesh(geo.GenerateMesh(**self._meshing_options()))
        self.app_data.add_mesh("Mesh " + self.title, mesh)

    @property
    def clipping(self):
        return self.global_clipping

    def change_maxh(self, event):
        value = event.value
        try:
            if value is None or value == "":
                value = None
            else:
                value = float(value)
                if value <= 0:
                    raise ValueError("Max mesh size must be positive.")
            self.meshsize_input.ui_error = False
            if self.selected[0] == "face":
                face = self.geo.faces[self.selected[1]]
                face.maxh = value if value is not None else 1e99
            elif self.selected[0] == "edge":
                edge = self.geo.edges[self.selected[1]]
                edge.maxh = value if value is not None else 1e99
        except ValueError as e:
            self.meshsize_input.ui_error_message = str(e)
            self.meshsize_input.ui_error = True

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
            self.name_input.ui_error = False
        except ValueError as e:
            self.name_input.ui_error_message = str(e)
            self.name_input.ui_error = True

    def select_face(self, event):
        self.selected = ("face", event.uint32[0])
        self.selection_menu.ui_offset = [-event.x, -event.y]
        self.heading_selection_menu.ui_children = ["Face selected: " + str(event.uint32[0])]
        face = self.geo.faces[event.uint32[0]]
        self.meshsize_input.ui_model_value = None if face.maxh==1e99 else face.maxh
        self.name_input.ui_model_value = face.name
        self.selection_menu.ui_show()

    def selected_edge(self, event):
        self.heading_selection_menu.ui_children = ["Edge selected: " + str(event.uint32[0])]
        edge = self.geo.edges[event.uint32[0]]
        self.meshsize_input.ui_model_value = None if edge.maxh==1e99 else edge.maxh
        self.name_input.ui_model_value = edge.name
        self.selection_menu.ui_show()

    def draw(self):
        self.geo_renderer = GeometryRenderer(self.geo, clipping=self.clipping)
        self.geo_renderer.faces.on_select(self.select_face)
        self.geo_renderer.edges.on_select(self.selected_edge)
        scene = self.wgpu.draw([self.geo_renderer], camera=self.global_camera)
        self.clipping.center = 0.5 * (scene.bounding_box[1] + scene.bounding_box[0])
        def on_click(event):
            if event["button"] == 0:
                scene.select(event["canvasX"], event["canvasY"])
        scene.input_handler.on_click(on_click)
