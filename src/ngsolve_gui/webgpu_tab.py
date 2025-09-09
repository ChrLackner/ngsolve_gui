from ngapp.components import *
from webgpu import Scene


class WebgpuTab(QLayout):
    def __init__(self, name, app_data):
        self.name = name
        self.wgpu = WebgpuComponent()
        self.wgpu.ui_style = "width: 100%;height: calc(100vh - 140px);"
        self.app_data = app_data
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
