from ngapp.components import *
from webgpu import Scene


class WebgpuTab(QLayout):
    def __init__(self, name, data, app_data):
        self.name = name
        self.data = data
        self.app_data = app_data
        self.wgpu = WebgpuComponent()
        self.wgpu.ui_style = "width: 100%;height: calc(100vh - 140px);"
        self.icon = "mdi-vector-triangle"

        self.reset_camera_btn = QBtn(
            QTooltip("Reset Camera"),
            ui_icon="mdi-refresh",
            ui_color="secondary",
            ui_style="position: absolute; top: 10px; right: 10px;",
            ui_fab=True,
            ui_flat=True,
        )

        self.reset_camera_btn.on_click(self.reset_camera)
        self.sidebar = self.create_sidebar()

        super().__init__(
            self.sidebar,
            QPageContainer(QPage(self.wgpu, self.reset_camera_btn)),
            ui_container=True,
            ui_view="lhh LpR lff",
            ui_style="height: calc(100vh - 140px); width: 100%;",
        )

        self.draw()
        self.reset_camera()
        self.clipping.center = 0.5 * (
            self.scene.bounding_box[1] + self.scene.bounding_box[0]
        )
        if "clipping" in data:
            clipping = data["clipping"]
            if bool(clipping):
                self.clipping.mode = self.clipping.Mode.PLANE
            if isinstance(clipping, dict):
                if "normal" in clipping:
                    self.clipping.normal = clipping["normal"]
                if "center" in clipping:
                    self.clipping.center = clipping["center"]


        self.scene.input_handler.on_dblclick(self._on_dblclick, ctrl=True)
        self.scene.input_handler.on_drag(self._on_mousemove, ctrl=True)
        self.scene.input_handler.on_wheel(self._on_wheel, ctrl=True)

    def _on_dblclick(self, ev):
        scene = self.scene
        x = ev["canvasX"]
        y = ev["canvasY"]

        p = scene.get_position(x, y)
        clipping = self.clipping
        clipping.set_x_value(float(p[0]))
        clipping.set_y_value(float(p[1]))
        clipping.set_z_value(float(p[2]))
        clipping.set_offset(0)
        self.scene.render()

    def _on_mousemove(self, ev):
        clipping = self.clipping
        if ev["button"] == 2:
            offset = clipping.offset
            offset += ev["movementY"] * 0.00002
            clipping.set_offset(offset)
            self.scene.render()
        if ev["button"] == 0:
            import numpy.linalg

            transform = self.scene.options.camera.transform.copy()
            inv_normal_mat = transform._mat.copy()[:3, :3].T
            normal_mat = numpy.linalg.inv(inv_normal_mat)

            transform._mat = numpy.identity(4)
            transform._mat[:3, :3] = normal_mat
            s = 0.3
            transform.rotate(s * ev["movementY"], s * ev["movementX"])
            n = inv_normal_mat @ (transform._mat[:3, :3] @ clipping.normal)

            clipping.set_nx_value(float(n[0]))
            clipping.set_ny_value(float(n[1]))
            clipping.set_nz_value(float(n[2]))

            self.scene.render()

    def _on_wheel(self, ev):
        clipping = self.clipping
        offset = clipping.offset
        offset += ev["deltaY"] * 0.0008
        clipping.set_offset(offset)
        self.scene.render()

    @property
    def scene(self) -> Scene:
        return self.wgpu.scene

    def reset_camera(self):
        if self.scene is not None:
            pmin, pmax = self.scene.bounding_box
            camera = self.scene.options.camera
            camera.reset(pmin, pmax)
            self.scene.render()

    def create_sidebar(self):
        return Div()

    @property
    def settings(self):
        return self.app_data.get_settings(self.name)

    @property
    def clipping(self):
        return self.app_data.clipping

    @property
    def camera(self):
        return self.app_data.camera

    @property
    def title(self):
        return self.app_data.get_tab(self.name)["title"]

    def draw(self):
        raise NotImplementedError("draw method must be implemented in subclass")

    def set_component(self, comp):
        self.ui_children = [comp]
