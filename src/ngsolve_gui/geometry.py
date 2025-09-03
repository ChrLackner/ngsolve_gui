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

        hide_btn = QBtn("Hide", ui_color="secondary",
                        ui_style="margin-right: 10px")
        hide_btn.on_click(self._hide_selected_shape)
        showall_btn = QBtn("Show All", ui_color="secondary")
        def show_all(event):
            colors = self.geo_renderer.faces.colors
            for i in range(len(colors) // 4):
                colors[i * 4 + 3] = 1.0
            self.geo_renderer.faces.set_colors(colors)
            colors = self.geo_renderer.edges.colors
            for i in range(len(colors) // 4):
                colors[i * 4 + 3] = 1.0
            self.geo_renderer.edges.set_colors(colors)
            self.wgpu.scene.render()
        showall_btn.on_click(show_all)
        self.selection_text = Div(Row(self.meshsize_input),
                                  Row(self.name_input),
                                  Row(hide_btn, showall_btn,
                                      ui_style="margin-top: 10px;"))
        self.selection_menu = QMenu(
            QCard(QCardSection(self.heading_selection_menu,
                               self.selection_text)),
            # ui_touch_position=True,
            # ui_target=self.wgpu._js_component,
            ui_anchor="top left",
            ui_no_parent_event=True,
        )
        reset_camera_btn = QBtn(
            QTooltip("Reset Camera"),
            ui_icon="mdi-refresh",
            ui_color="secondary",
            ui_style="position: absolute; top: 10px; right: 10px;",
            ui_fab=True, ui_flat=True)
        def reset_camera(event):
            if self.wgpu.scene is not None:
                pmin, pmax = self.geo.shape.bounding_box
                npmin = np.array([pmin[0], pmin[1], pmin[2]])
                npmax = np.array([pmax[0], pmax[1], pmax[2]])
                camera = self.wgpu.scene.options.camera
                camera.reset(npmin, npmax)
                self.wgpu.scene.render()
        reset_camera_btn.on_click(reset_camera)

        self.global_camera = global_camera
        self.sidebar = Sidebar(self)
        self.draw()
        self.error_dialog = QDialog()
        super().__init__(
            self.sidebar,
            QPageContainer(QPage(self.wgpu,
                                 self.selection_menu,
                                 self.error_dialog,
                                 reset_camera_btn)),
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
        import netgen.meshing as ngm
        mesh = ngm.Mesh()
        try:
            geo.GenerateMesh(mesh=mesh, **self._meshing_options())
        except Exception as e:
            btn_close = QBtn("Close")
            btn_close.on_click(self.error_dialog.ui_hide)
            self.error_dialog.ui_children = [
                QCard(QCardSection(Heading("Error generating mesh", 5)),
                      QCardSection(str(e)),
                      QCardActions(btn_close))]
            self.error_dialog.ui_show()
        mesh = ngs.Mesh(mesh)
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

    def _hide_selected_shape(self, event):
        if self.selected[0] == "face":
            colors = self.geo_renderer.faces.colors
            colors[self.selected[1] * 4 + 3] = 0.0  # Set alpha to 0
            self.geo_renderer.faces.set_colors(colors)
        elif self.selected[0] == "edge":
            colors = self.geo_renderer.edges.colors
            colors[self.selected[1] * 4 + 3] = 0.0
            self.geo_renderer.edges.set_colors(colors)
        self.scene.render()

    def select_face(self, event):
        face_id = event.uint32[1]
        self.selected = ("face", face_id)
        self.selection_menu.ui_offset = [-event.x, -event.y]
        self.heading_selection_menu.ui_children = ["Face selected: " + str(face_id)]
        face = self.geo.faces[face_id]
        self.meshsize_input.ui_model_value = None if face.maxh==1e99 else face.maxh
        self.name_input.ui_model_value = face.name
        self.selection_menu.ui_show()

    def selected_edge(self, event):
        edge_id = event.uint32[1]
        self.heading_selection_menu.ui_children = ["Edge selected: " + str(edge_id)]
        edge = self.geo.edges[edge_id]
        self.meshsize_input.ui_model_value = None if edge.maxh==1e99 else edge.maxh
        self.name_input.ui_model_value = edge.name
        self.selection_menu.ui_show()

    def draw(self):
        self.geo_renderer = GeometryRenderer(self.geo, clipping=self.clipping)
        self.geo_renderer.faces.on_select(self.select_face)
        self.geo_renderer.edges.on_select(self.selected_edge)
        scene = self.wgpu.draw([self.geo_renderer], camera=self.global_camera)
        self.scene = scene
        self.clipping.center = 0.5 * (scene.bounding_box[1] + scene.bounding_box[0])
        def on_click(event):
            if self.selection_menu.ui_model_value:
                self.selection_menu.ui_hide()
            if event["button"] == 2:
                scene.select(event["canvasX"], event["canvasY"])
        scene.input_handler.on_click(on_click)
