import os

from ngapp.app import App
from ngapp.components import *

from .app_data import AppData
from .file_loader import load_file
from .mesh import MeshComponent
from .geometry import GeometryComponent
from .function import FunctionComponent
from ngsolve_webgpu import Clipping
from webgpu.camera import Camera

_colors = {
    "primary": "#164d7d",  # ngsolve blue
    "secondary": "#93B1D4",  # light slate blue
    "accent": "#14B8A6",  # teal
    "dark": "#0F172A",  # dark slate gray
    "positive": "#16A34A",  # green
    "negative": "#DC2626",  # red
    "info": "#0EA5E9",  # sky blue
    "warning": "#F59E0B",  # amber
}

_tab_type = {
    "mesh": MeshComponent,
    "geometry": GeometryComponent,
    "function": FunctionComponent,
}


class Panel(Div):
    def __init__(self, app_data):
        self.app_data = app_data
        self.global_clipping = Clipping()
        self.global_camera = None
        super().__init__()
        self.set_tab()

    def set_tab(self):
        name = self.app_data.active_tab
        if name is None:
            self.ui_children = []
            return
        tab = self.app_data.get_tab(name)
        settings = self.app_data.get_settings(name)
        new_camera = False
        if self.global_camera is None:
            self.global_camera = Camera()
            new_camera = True
        comp = _tab_type[tab["type"]](
            tab["title"],
            tab["data"],
            global_clipping=self.global_clipping,
            app_data=self.app_data,
            settings=settings,
            global_camera=self.global_camera,
        )
        self.ui_children = [comp]
        if new_camera:
            try:
                pmin, pmax = comp.wgpu.scene.bounding_box
                self.global_camera.transform._center = 0.5 * (pmin + pmax)
                self.global_camera.transform._scale = 2 / np.linalg.norm(pmax - pmin)

                if not (pmin[2] == 0 and pmax[2] == 0):
                    self.global_camera.transform.rotate(270, 0)
                    self.global_camera.transform.rotate(0, -20)
                    self.global_camera.transform.rotate(20, 0)
            except Exception as e:
                self.global_camera = None


class NGSolveGui(App):
    def __init__(self, filename=None, local_path=None):
        self._local_path = local_path if local_path else os.path.expanduser("~")
        self.app_data = AppData()
        super().__init__()
        self.set_colors(**_colors)
        upload_file = QBtn(QTooltip("Load File"), ui_flat=True, ui_icon="mdi-plus")
        upload_file.on_click(self._load_file)
        self.tabs = QTabs(ui_dense=True)
        close_btn = QBtn(QTooltip("Quit"), ui_flat=True, ui_icon="mdi-close")
        close_btn.on_click(self.quit)
        ngs_logo = Div(
            QImg(
                ui_src=self.load_asset("logo_withname_retina.png"),
                ui_height="40px",
                ui_fit="scale-down",
            ),
            ui_style="width: 200px;",
        )
        bar = QBar(
            ngs_logo,
            upload_file,
            QSpace(),
            self.tabs,
            QSpace(),
            close_btn,
            ui_style="height: 60px",
            ui_class="bg-primary text-grey-4",
        )

        self.tab_panel = Panel(self.app_data)
        self.tabs.on_update_model_value(lambda e: self._click_tab(e.value))
        self.tab_components = {}
        self.component = Div(bar, self.tab_panel, id="main_component")
        self.component.on_load(self.__on_load)
        self.component.on_before_save(self.__on_before_save)
        load_file(filename, self.app_data)
        # self.component.add_keybinding("q", self.quit)

    def _load_file(self):
        from tkinter import Tk, filedialog

        root = Tk()
        root.withdraw()
        file_path = filedialog.askopenfilename(
            title="Select a file",
            initialdir=self._local_path,
            filetypes=[
                ("All Files", "*.*"),
                ("Mesh Files", "*.vol *.vol.gz"),
                ("Geometry Files", "*.step *.iges *.stp"),
            ],
        )
        root.destroy()
        if file_path:
            self._local_path = os.path.dirname(file_path)
        load_file(file_path, self.app_data)

    def __on_before_save(self):
        self.component.storage.set("app_data", self.app_data._data, use_pickle=True)

    def __on_load(self):
        data = self.component.storage.get("app_data")
        if data is not None:
            self.app_data._data.update(data)
        self._update()
        self.app_data._update = self._update

    def _click_tab(self, tabname):
        self.app_data.active_tab = tabname
        self.tab_panel.set_tab()

    def _ctab(self, e, tabname):
        if e.value["button"] == 1:
            self.app_data.delete_tab(tabname)

    def _update(self):
        tabs = []
        for name, tab in self.app_data.get_tabs().items():
            title = tab["title"]
            t = QTab(ui_name=name, ui_icon=tab["icon"], ui_label=title)
            t.on("mousedown", lambda e, t=t: self._ctab(e, t.ui_name))
            tabs.append(t)

        self.tabs.ui_children = tabs
        self.tabs.ui_model_value = self.app_data.active_tab
        self.tab_panel.set_tab()
