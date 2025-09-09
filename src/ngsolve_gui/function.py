from ngapp.components import *
from ngsolve_webgpu import *
from .clipping import ClippingSettings
import ngsolve as ngs
from webgpu.canvas import debounce


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


class DeformationSettings(QCard):
    def __init__(self, comp):
        self.comp = comp
        self._enable = QCheckbox(
            ui_label="Enable Deformation",
            ui_model_value=comp.settings.get("deformation_enabled", False),
        )
        self._enable.on_update_model_value(self.enable)
        self._deform_scale = QInput(
            ui_label="Deformation Scale",
            ui_type="number",
            ui_model_value=comp.settings.get("deformation_scale", 1.0),
        )
        self._deform_scale2 = QSlider(
            ui_model_value=comp.settings.get("deformation_scale2", 1.0),
            ui_min=0.0,
            ui_max=1.0,
            ui_step=0.01,
        )
        self._deform_scale.on_change(self.change_scale)
        self._deform_scale2.on_update_model_value(self.change_scale)
        super().__init__(
            QCardSection(
                Heading("Deformation Settings", 5),
                self._enable,
                self._deform_scale2,
                self._deform_scale,
            )
        )

    def enable(self, event):
        self.comp.settings.set("deformation_enabled", self._enable.ui_model_value)
        if hasattr(self.comp, "mdata"):
            scale = 0.0
            if self._enable.ui_model_value:
                try:
                    scale = float(self._deform_scale.ui_model_value) * float(
                        self._deform_scale2.ui_model_value
                    )
                except ValueError:
                    scale = 1.0
            self.comp.mdata.deformation_scale = scale
        self.comp.wgpu.scene.render()

    @debounce
    def change_scale(self, event):
        try:
            self.comp.settings.set(
                "deformation_scale", float(self._deform_scale.ui_model_value)
            )
            self.comp.settings.set(
                "deformation_scale2", float(self._deform_scale2.ui_model_value)
            )
            scale = float(self._deform_scale.ui_model_value) * float(
                self._deform_scale2.ui_model_value
            )
            self.comp.mdata.deformation_scale = scale
            self.comp.wgpu.scene.render()
        except ValueError:
            pass

class Options(QCard):
    def __init__(self, comp):
        self.comp = comp
        self.wireframe_visible = QCheckbox(
            ui_label="Wireframe Visible",
            ui_model_value=comp.settings.get("wireframe_visible", True),
        )
        reset_camera = QBtn(
                ui_icon="mdi-refresh",
                ui_label="Reset Camera",
                ui_flat=True,
                ui_color="primary",
                )
        reset_camera.on_click(self.reset_camera)
        self.wireframe_visible.on_update_model_value(self.toggle_wireframe)
        super().__init__(
            QCardSection(
                Heading("Options", 5),
                reset_camera,
                self.wireframe_visible,
            )
        )

    def toggle_wireframe(self, event):
        self.comp.wireframe.active = self.wireframe_visible.ui_model_value
        self.comp.wgpu.scene.render()

    def reset_camera(self, event):
        pmin, pmax = self.comp.wgpu.scene.bounding_box
        camera = self.comp.wgpu.scene.options.camera
        camera.reset(pmin, pmax)
        self.comp.wgpu.scene.render()

class VectorSettings(QCard):
    def __init__(self, comp):
        self.comp = comp
        options = ["Norm"] + [str(i) for i in range(1, comp.cf.dim + 1)]
        self.color_component = QSelect(
            ui_options=options, ui_model_value=options[0], ui_label="Color Component"
        )
        self.color_component.on_update_model_value(self.update_color_component)
        super().__init__(
            QCardSection(Heading("Vector Settings", 5), self.color_component)
        )

    def update_color_component(self, event):
        index = self.color_component.ui_options.index(
            self.color_component.ui_model_value
        )
        self.comp.elements2d.change_cf_dim(index - 1)
        self.comp.colorbar.set_needs_update()
        self.comp.wgpu.scene.render()


class Sidebar(QDrawer):
    def __init__(self, comp):
        self.comp = comp
        colorbar_menu = QMenu(ColorbarSettings(comp), ui_anchor="top right")
        items = [
            ClippingSettings(comp),
            QItem(
                QItemSection(QIcon(ui_name="mdi-palette-outline"), ui_avatar=True),
                QItemSection("Colorbar"),
                colorbar_menu,
                ui_clickable=True,
            ),
        ]
        if self.comp.deformation is not None or (
            self.comp.cf.dim == 1 and self.comp.mesh.dim < 3
        ):
            deformation_menu = QMenu(DeformationSettings(comp), ui_anchor="top right")
            items.append(
                QItem(
                    QItemSection(QIcon(ui_name="mdi-arrow-expand-all"), ui_avatar=True),
                    QItemSection("Deformation"),
                    deformation_menu,
                    ui_clickable=True,
                )
            )
        if comp.cf.dim > 1:
            vector_menu = QMenu(VectorSettings(comp), ui_anchor="top right")
            items.append(
                QItem(
                    QItemSection(
                        QIcon(ui_name="mdi-arrow-top-right-thin"), ui_avatar=True
                    ),
                    QItemSection("Vector Settings"),
                    vector_menu,
                    ui_clickable=True,
                )
            )
        option_menu = QMenu(Options(comp), ui_anchor="top right")
        items.append(
            QItem(
                QItemSection(QIcon(ui_name="mdi-cog-outline"), ui_avatar=True),
                QItemSection("Options"),
                option_menu,
                ui_clickable=True,
            )
        )
        qlist = QList(*items, ui_padding=True, ui_class="menu-list")
        super().__init__(qlist, ui_width=200, ui_bordered=True, ui_model_value=True)


class FunctionComponent(QLayout):
    def __init__(self, title, data, global_clipping, app_data, settings, global_camera):
        self.mdata= None
        self.title = title
        self.global_camera = global_camera
        self.cf = data["function"]
        self.mesh = data["mesh"]
        self.deformation = data.get("deformation", None)
        if self.deformation is None and self.cf.dim == 1 and self.mesh.dim < 3:
            self.deformation = ngs.CF((0, 0, self.cf))
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

    def draw(self):
        func_data = self.app_data.get_function_gpu_data(self.cf, self.mesh, order=self.settings.get("order", 3))
        mdata = func_data.mesh_data

        if self.deformation is not None:
            deform_data = self.app_data.get_function_gpu_data(self.deformation, self.mesh, order=3)
            mdata = copy.copy(deform_data.mesh_data)
            self.mdata = mdata
            deform_data.mesh_data = mdata
            mdata.deformation_data = deform_data
            mdata.deformation_scale = self.settings.get(
                "deformation_scale", 1.0
            ) * self.settings.get("deformation_scale2", 1.0)
            if not self.settings.get("deformation_enabled", False):
                mdata.deformation_scale = 0.0
            func_data.mesh_data = mdata
        self.wireframe = MeshWireframe2d(mdata, clipping=self.clipping)
        self.wireframe.active = self.settings.get("wireframe_visible", True)

        self.colormap = Colormap()
        self.clippingcf = ClippingCF(func_data, self.clipping, self.colormap)
        self.elements2d = CFRenderer(
            func_data, clipping=self.clipping, colormap=self.colormap
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
