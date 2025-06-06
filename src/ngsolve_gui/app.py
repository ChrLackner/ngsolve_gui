from ngapp.app import App
from ngapp.components import *

from .app_data import AppData
from .file_loader import load_file
from .mesh import MeshComponent
from .geometry import GeometryComponent
from ngsolve_webgpu import Clipping


class NGSolveGui(App):
    def __init__(self, filename=None):
        self.appdata = AppData()
        super().__init__()
        load_file(filename, self.appdata)
        upload_file = QBtn(QTooltip("Load File"), ui_flat=True, ui_icon="mdi-plus")
        upload_file.on_click(self._load_file)
        self.tabs = QTabs(ui_dense=True)
        bar = QBar(
            upload_file,
            QSpace(),
            self.tabs,
            QSpace(),
            ui_style="height: 60px",
            ui_class="bg-secondary text-black",
        )
        self.tab_panel = QTabPanels()
        self.tabs.on_update_model_value(lambda e: self._click_tab(e.value))
        self.global_clipping = Clipping()
        self.tab_components = {}
        self.component = Div(bar, self.tab_panel, id="main_component")

        self.component.on_load(self.__on_load)
        self.component.on_before_save(self.__on_before_save)

    def _load_file(self):
        from tkinter import Tk, filedialog
        import os

        root = Tk()
        root.withdraw()
        file_path = filedialog.askopenfilename(
            title="Select a file",
            initialdir=os.path.expanduser("~"),
            filetypes=[
                ("All Files", "*.*"),
                ("Mesh Files", "*.vol *.vol.gz"),
                ("Geometry Files", "*.step *.iges *.stp"),
            ],
        )
        root.destroy()
        load_file(file_path, self.appdata)

    def __on_before_save(self):
        self.component.storage.set("appdata", self.appdata._data, use_pickle=True)

    def __on_load(self):
        data = self.component.storage.get("appdata")
        if data is not None:
            self.appdata._data.update(data)
        self._update()
        print("set update")
        self.appdata._update = self._update

    def _click_tab(self, tabname):
        self.appdata.active_tab = tabname
        self.tab_panel.ui_model_value = tabname

    def _ctab(self, e, tabname):
        if e.value["button"] == 1:
            print("delete ", tabname)
            self.appdata.delete_tab(tabname)

    def _update(self):
        tabs = []
        tab_type = {"mesh": MeshComponent, "geometry": GeometryComponent}
        panels = []
        for name, tab in self.appdata.get_tabs().items():
            title = tab["title"]
            t = QTab(ui_name=name, ui_icon=tab["icon"], ui_label=title)
            t.on("mousedown", lambda e, t=t: self._ctab(e, t.ui_name))
            tabs.append(t)
            have_tab = False
            settings = self.appdata.get_settings(name)
            if name in self.tab_components:
                comp = self.tab_components[name].ui_children[0]
                if isinstance(comp, tab_type[tab["type"]]):
                    have_tab = True
                    comp.update(title, tab["data"], settings)
            if not have_tab:
                comp = tab_type[tab["type"]](
                    title,
                    tab["data"],
                    global_clipping=self.global_clipping,
                    app_data=self.appdata,
                    settings=settings,
                )

            panels.append(QTabPanel(comp, ui_name=name))

        self.tabs.ui_children = tabs
        self.tabs.ui_model_value = self.appdata.active_tab
        self.tab_panel.ui_children = panels
        self.tab_panel.ui_model_value = self.appdata.active_tab
