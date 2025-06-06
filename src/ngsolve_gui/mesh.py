from ngapp.components import *

from ngsolve_webgpu.mesh import *
from webgpu.labels import Labels


class Sidebar(QDrawer):
    def __init__(self, comp):
        self.geo_comp = comp
        wireframe = QCheckbox(
            "Wireframe", ui_model_value=comp.settings.get("wireframe_visible", True)
        )
        element2d = QCheckbox(
            "Elements 2D", ui_model_value=comp.settings.get("elements2d_visible", True)
        )
        elements3d = QCheckbox(
            "Elements 3D", ui_model_value=comp.settings.get("elements3d_visible", False)
        )
        elements3d.on_update_model_value(comp.set_elements3d_visible)
        shrink = QSlider(
            "Shrink",
            ui_model_value=comp.settings.get("shrink", 1.0),
            ui_min=0.0,
            ui_max=1.0,
            ui_step=0.01,
        )
        shrink.on_update_model_value(comp.set_shrink)
        wireframe.on_update_model_value(comp.set_wireframe_visible)
        element2d.on_update_model_value(comp.set_elements2d_visible)
        view_options = Div(
            wireframe, element2d, elements3d, Row(Col(Label("Shrink")), Col(shrink))
        )

        view_card = QMenu(
            QCard(
                QCardSection(Heading("View Options", 5)),
                QCardSection(view_options),
                ui_flat=True,
            ),
            ui_anchor="top right",
        )

        items = [
            QItem(
                QItemSection(QIcon(ui_name="mdi-eye"), ui_avatar=True),
                QItemSection("View"),
                view_card,
                ui_clickable=True,
            )
        ]
        qlist = QList(*items, ui_padding=True, ui_class="menu-list")
        super().__init__(qlist, ui_width=200, ui_bordered=True, ui_model_value=True)


class MeshComponent(QLayout):
    def __init__(self, title, mesh, global_clipping, app_data, settings):
        self.title = title
        self.app_data = app_data
        self.settings = settings
        self.mesh = mesh
        self.wgpu = WebgpuComponent()
        self.global_clipping = global_clipping
        self.sidebar = Sidebar(self)
        self.elements3d = None
        self.wgpu.ui_style = "width: 100%;height: calc(100vh - 140px);"
        self.draw()
        super().__init__(
            self.sidebar,
            QPageContainer(QPage(self.wgpu)),
            ui_container=True,
            ui_view="lhh LpR lff",
            ui_style="height: calc(100vh - 140px); width: 100%;",
        )

    def update(self, title, mesh, settings):
        self.title = title
        if self.mesh == mesh:
            return
        self.mesh = mesh
        self.settings = settings
        self.draw()

    @property
    def clipping(self):
        return self.global_clipping

    def set_wireframe_visible(self, event):
        self.wireframe.active = event.value
        self.settings.set("wireframe_visible", event.value)
        self.wgpu.scene.render()

    def set_elements2d_visible(self, event):
        self.elements2d.active = event.value
        self.settings.set("elements2d_visible", event.value)
        self.wgpu.scene.render()

    def set_elements3d_visible(self, event):
        self.settings.set("elements3d_visible", event.value)
        if self.elements3d is None:
            self.draw()
        self.elements3d.active = event.value
        self.wgpu.scene.render()

    def set_shrink(self, event):
        self.mdata.shrink = event.value
        self.settings.set("shrink", event.value)
        if self.elements3d is not None:
            self.elements3d.shrink = event.value
        self.wgpu.scene.render()

    def draw(self):
        self.mdata = MeshData(self.mesh)
        self.wireframe = MeshWireframe2d(self.mdata, clipping=self.clipping)
        self.wireframe.active = self.settings.get("wireframe_visible", True)
        self.elements2d = MeshElements2d(self.mdata, clipping=self.clipping)
        self.elements2d.active = self.settings.get("elements2d_visible", True)
        if self.settings.get("elements3d_visible", False):
            self.elements3d = MeshElements3d(self.mdata, clipping=self.clipping)
            self.elements3d.shrink = self.settings.get("shrink", 1.0)
        self.mesh_info = Labels(
            [
                f"El: {self.mesh.ne} F: {self.mesh.nface} E: {self.mesh.nedge} V: {self.mesh.nv}"
            ],
            [(-0.99, -0.99)],
            font_size=14,
        )

        render_objects = [
            obj
            for obj in [
                self.elements2d,
                self.wireframe,
                self.elements3d,
                self.mesh_info,
            ]
            if obj is not None
        ]

        self.wgpu.draw(render_objects)
