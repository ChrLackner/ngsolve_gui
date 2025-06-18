from ngapp.components import *
from ngsolve_webgpu import *
from .clipping import ClippingSettings


class ColorbarSettings(QCard):
    def __init__(self, comp):
        self.comp = comp
        self.minval = QInput(
            ui_label="Min Value",
            ui_type="number",
            ui_dense=True,
            ui_model_value=0.0,
            ui_style="width: 100px;",
        )
        self.maxval = QInput(
            ui_label="Max Value",
            ui_type="number",
            ui_dense=True,
            ui_model_value=1.0,
            ui_style="padding-left: 20px; width: 100px;",
        )
        self.minval.on_change(self.update_min)
        self.maxval.on_change(self.update_max)
        self.autoscale = QCheckbox(ui_label="Autoscale", ui_model_value=True)
        self.autoscale.on_update_model_value(self.update_autoscale)
        super().__init__(
            QCardSection(
                Heading("Colorbar", 5), self.autoscale, Row(self.minval, self.maxval)
            )
        )
        self.on_mounted(self._update)

    def update_autoscale(self, event):
        if self.autoscale.ui_model_value:
            self.comp.colormap.autoscale = True
            self.comp.wgpu.scene.redraw(blocking=True)
            self.minval.ui_model_value = self.comp.colormap.minval
            self.maxval.ui_model_value = self.comp.colormap.maxval
        else:
            self.comp.colormap.autoscale = False

    def update_min(self, event):
        try:
            self.comp.colormap.set_min(float(self.minval.ui_model_value))
            self.autoscale.ui_model_value = False
            self.comp.colorbar.set_needs_update()
            self.comp.wgpu.scene.render()
        except ValueError:
            pass

    def update_max(self, event):
        try:
            self.comp.colormap.set_max(float(self.maxval.ui_model_value))
            self.autoscale.ui_model_value = False
            self.comp.colorbar.set_needs_update()
            self.comp.wgpu.scene.render()
        except ValueError:
            pass

    def _update(self):
        self.autoscale.ui_model_value = self.comp.colormap.autoscale
        self.minval.ui_model_value = self.comp.colormap.minval
        self.maxval.ui_model_value = self.comp.colormap.maxval


class Sidebar(QDrawer):
    def __init__(self, comp):
        self.comp = comp
        clipping_menu = QMenu(ClippingSettings(comp), ui_anchor="top right")
        colorbar_menu = QMenu(ColorbarSettings(comp), ui_anchor="top right")
        items = [
            QItem(
                QItemSection(QIcon(ui_name="mdi-cube-off-outline"), ui_avatar=True),
                QItemSection("Clipping"),
                clipping_menu,
                ui_clickable=True,
            ),
            QItem(
                QItemSection(QIcon(ui_name="mdi-palette-outline"), ui_avatar=True),
                QItemSection("Colorbar"),
                colorbar_menu,
                ui_clickable=True,
            ),
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
        self.func_data = None
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
        self.colormap = Colormap()
        self.elements2d = CFRenderer(
            self.func_data, clipping=self.clipping, colormap=self.colormap
        )
        self.elements2d.active = self.settings.get("elements2d_visible", True)
        self.colorbar = Colorbar(self.colormap)
        self.colorbar.width = 0.8
        self.colorbar.position = (-0.5, 0.9)

        render_objects = [
            obj
            for obj in [
                self.elements2d,
                self.wireframe,
                self.colorbar,
            ]
            if obj is not None
        ]
        self.wgpu.draw(render_objects, camera=self.global_camera)

        def set_min_max():
            self.min_max = (self.colormap.minval, self.colormap.maxval)

        self.wgpu.on_mounted(set_min_max)
