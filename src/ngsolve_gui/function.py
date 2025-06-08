from ngapp.components import *
from ngsolve_webgpu import *
from .clipping import ClippingSettings


class Sidebar(QDrawer):
    def __init__(self, comp):
        self.comp = comp
        clipping_menu = QMenu(ClippingSettings(comp), ui_anchor="top right")
        items = [
            QItem(
                QItemSection(QIcon(ui_name="mdi-cube-off-outline"), ui_avatar=True),
                QItemSection("Clipping"),
                clipping_menu,
                ui_clickable=True,
            )
        ]
        qlist = QList(*items, ui_padding=True, ui_class="menu-list")
        super().__init__(qlist, ui_width=200, ui_bordered=True, ui_model_value=True)


class FunctionComponent(QLayout):
    def __init__(self, title, data, global_clipping, app_data, settings, global_camera):
        self.title = title
        self.global_camera = global_camera
        self.cf = data["function"]
        self.mesh = data["mesh"]
        self.global_clipping = global_clipping
        self.app_data = app_data
        self.settings = settings
        self.wgpu = WebgpuComponent()
        self.wgpu.ui_style = "width: 100%;height: calc(100vh - 140px);"
        self.draw()
        self.sidebar = Sidebar(self)
        super().__init__(
            self.sidebar,
            QPageContainer(QPage(self.wgpu)),
            ui_container=True,
            ui_view="lhh LpR lff",
            ui_style="width: 100%; height: calc(100vh - 140px);",
        )

    @property
    def clipping(self):
        return self.global_clipping

    def update(self, title, data, settings):
        self.title = title
        if self.cf == data["function"] and self.mesh == data["mesh"]:
            return
        self.cf = data["function"]
        self.mesh = data["mesh"]
        self.settings = settings
        self.draw()

    def draw(self):
        self.mdata = MeshData(self.mesh)
        self.wireframe = MeshWireframe2d(self.mdata, clipping=self.clipping)
        self.wireframe.active = self.settings.get("wireframe_visible", True)
        self.func_data = FunctionData(
            self.mdata, self.cf, order=self.settings.get("order", 3)
        )
        self.elements2d = CFRenderer(self.func_data, clipping=self.clipping)
        self.elements2d.active = self.settings.get("elements2d_visible", True)

        render_objects = [
            obj
            for obj in [
                self.elements2d,
                self.wireframe,
            ]
            if obj is not None
        ]
        self.wgpu.draw(render_objects, camera=self.global_camera)
