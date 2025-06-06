from ngapp.components import *

from ngsolve_webgpu import *
import ngsolve as ngs


class Sidebar(QDrawer):
    def __init__(self, comp):
        self.geo_comp = comp
        create_mesh = QItem(QItemSection("Create Mesh"), ui_clickable=True)

        self.maxh = QInput(
            ui_label="Max Mesh Size",
            ui_model_value=comp.settings.get("maxh", 1000),
            ui_type="number",
        )

        def update_maxh(ev):
            try:
                value = float(ev.value)
                if value <= 0:
                    raise ValueError("Max mesh size must be positive.")
                comp.settings.set("maxh", value)
                self.maxh.ui_error = False
            except ValueError as e:
                self.maxh.ui_error_message = str(e)
                self.maxh.ui_error = True

        self.maxh.on_update_model_value(update_maxh)

        mparam = QCardSection(self.maxh)
        mparam_menu = QMenu(
            QCard(QCardSection(Heading("Meshing Parameters", 5)), mparam),
            ui_anchor="top right",
        )
        meshing_parameters = QItem(
            mparam_menu, QItemSection("Meshing Parameters"), ui_clickable=True
        )
        create_mesh.on_click(self.geo_comp.create_mesh)
        items = [create_mesh, meshing_parameters]
        qlist = QList(*items, ui_padding=True, ui_class="menu-list")
        super().__init__(qlist, ui_width=200, ui_bordered=True, ui_model_value=True)


class GeometryComponent(QLayout):
    def __init__(self, title, geometry, global_clipping, app_data, settings):
        self.title = title
        self.settings = settings
        self.app_data = app_data
        self.geo = geometry
        self.wgpu = WebgpuComponent()
        self.global_clipping = global_clipping
        self.sidebar = Sidebar(self)
        self.wgpu.ui_style = "width: 100%; height: calc(100vh - 140px);"
        self.draw()
        super().__init__(
            self.sidebar,
            QPageContainer(QPage(self.wgpu)),
            ui_container=True,
            ui_view="lhh LpR lff",
            ui_style="height: calc(100vh - 140px); width: 100%;",
        )

    def _create_meshing_geo(self):
        return self.geo

    def _meshing_options(self):
        return {"maxh": self.settings.get("maxh", 1000)}

    def create_mesh(self, *args):
        geo = self._create_meshing_geo()
        mesh = ngs.Mesh(geo.GenerateMesh(**self._meshing_options()))
        self.app_data.add_mesh("Mesh " + self.title, mesh)

    @property
    def clipping(self):
        return self.global_clipping

    def draw(self):
        self.geo_renderer = GeometryRenderer(self.geo, clipping=self.clipping)
        self.wgpu.draw([self.geo_renderer])
