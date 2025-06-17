from ngapp.components import *

import ngsolve as ngs
from ngsolve_webgpu.mesh import *
from webgpu.labels import Labels
from webgpu.canvas import debounce

from .clipping import ClippingSettings
from .region_colors import RegionColors


class ViewOptions(QCard):
    def __init__(self, comp):
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
        super().__init__(
            QCardSection(Heading("View Options", 5)),
            QCardSection(view_options),
            ui_flat=True,
        )


class ColorOptions(QCard):
    def __init__(self, comp):
        self.comp = comp
        colors = [fd.color for fd in comp.mesh.ngmesh.FaceDescriptors()]
        colors = [(c[0], c[1], c[2], c[3]) for c in colors]
        names = [fd.bcname for fd in comp.mesh.ngmesh.FaceDescriptors()]
        face_colors = RegionColors("Face Colors", colors, names)
        face_colors_card = QCard(
            QCardSection(face_colors), ui_flat=True, ui_bordered=True
        )
        dnames = list(set(comp.mesh.GetMaterials()))
        dcolors = [(1.0, 0.0, 0.0, 1.0) for _ in range(len(dnames))]
        domain_colors = RegionColors("Domain Colors", dcolors, dnames)
        self.dcolors = {
            name: [int(255 * ci) for ci in dcol] for name, dcol in zip(dnames, dcolors)
        }
        domain_colors_card = QCard(
            QCardSection(domain_colors), ui_flat=True, ui_bordered=True
        )
        super().__init__(
            QCardSection(Heading("Colors", 4), face_colors_card, domain_colors_card)
        )
        face_colors.on_change_color(self.change_color)
        domain_colors.on_change_color(self.change_d_color)

    def change_color(self, name, color):
        colors = []
        for fd in self.comp.mesh.ngmesh.FaceDescriptors():
            try:
                index = name.index(fd.bcname)
            except ValueError:
                index = -1
            if index >= 0:
                fd.color = color[index]
            colors.append(
                [
                    int(fd.color[0] * 255),
                    int(fd.color[1] * 255),
                    int(fd.color[2] * 255),
                    int(fd.color[3] * 255),
                ]
            )
        self.comp.elements2d.colormap.set_colormap(colors)
        self.comp.elements2d.set_needs_update()
        self.comp.wgpu.scene.render()

    def change_d_color(self, name, color):
        colors = []
        for i, d in enumerate(set(self.comp.mesh.GetMaterials())):
            try:
                index = name.index(d)
            except ValueError:
                index = -1
            c = color[index]
            self.dcolors[name[index]] = [
                int(c[0] * 255),
                int(c[1] * 255),
                int(c[2] * 255),
                int(c[3] * 255),
            ]
        self.comp.elements3d.colormap.set_colormap(list(self.dcolors.values()))
        self.comp.elements3d.set_needs_update()
        self.comp.wgpu.scene.render()


class Sidebar(QDrawer):
    def __init__(self, comp):
        self.geo_comp = comp

        self.view_menu = QMenu(ViewOptions(comp), ui_anchor="top right")
        clipping_menu = QMenu(ClippingSettings(comp), ui_anchor="top right")
        color_menu = QMenu(ColorOptions(comp), ui_anchor="top right")
        items = [
            QItem(
                QItemSection(QIcon(ui_name="mdi-eye"), ui_avatar=True),
                QItemSection("View"),
                self.view_menu,
                ui_clickable=True,
            ),
            QItem(
                QItemSection(QIcon(ui_name="mdi-cube-off-outline"), ui_avatar=True),
                QItemSection("Clipping"),
                clipping_menu,
                ui_clickable=True,
            ),
            QItem(
                QItemSection(QIcon(ui_name="mdi-palette"), ui_avatar=True),
                QItemSection("Colors"),
                color_menu,
                ui_clickable=True,
            ),
        ]
        qlist = QList(*items, ui_padding=True, ui_class="menu-list")
        super().__init__(qlist, ui_width=200, ui_bordered=True, ui_model_value=True)
        # self.add_keybinding("v", self.view_menu.ui_toggle)


class MeshComponent(QLayout):
    def __init__(self, title, mesh, global_clipping, app_data, settings, global_camera):
        self.title = title
        self.app_data = app_data
        self.settings = settings
        self.global_camera = global_camera
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
                f"VOL: {self.mesh.GetNE(ngs.VOL)} BND: {self.mesh.GetNE(ngs.BND)} CD2: {self.mesh.GetNE(ngs.BBND)} CD3: {self.mesh.GetNE(ngs.BBBND)}"
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
        self.wgpu.draw(render_objects, camera=self.global_camera)
