import os

from ngapp.app import App
from ngapp.components import *

from .app_data import AppData
from .file_loader import load_file
from .keybindings import KeybindingManager
from .navigator import Navigator
from .property_panel import PropertyPanel
from .styles import sidebar_style


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


class Panel(Div):
    def __init__(self, app_data):
        self.app_data = app_data
        self.comp = None
        super().__init__(ui_style="width: 100%; height: 100%;")
        self.set_tab()

    def set_tab(self):
        name = self.app_data.active_tab
        if name is None:
            self.ui_children = []
            return
        tab = self.app_data.get_tab(name)
        if tab is None:
            self.ui_children = []
            return
        if "component" in tab:
            self.comp = comp = tab["component"]
        else:
            cls = self._resolve_class(tab["type"])
            self.comp = comp = cls(
                tab["name"],
                tab["data"],
                app_data=self.app_data,
            )
            tab["component"] = comp
        self.ui_children = [comp]

    def _resolve_class(self, type_key):
        from .registry import get_component_info
        info = get_component_info(type_key)
        if info is None:
            raise ValueError(f"Unknown component type: {type_key}")
        return info["cls"]


class Settings(QMenu):
    def __init__(self, app):
        self.app = app
        val = self.app.usersettings.get("nthreads", 0)
        nthreads = QInput(QTooltip("Set number of threads used by NGSolve, 0 for all available cores. Only takes effect after restarting the application."),
            ui_label="Number of Threads", ui_type="number", ui_model_value=val)
        nthreads.on_update_model_value(self.app.usersettings.update("nthreads"))
        super().__init__(QCard(
            QCardSection("Settings"),
            QCardSection(
                nthreads)))


class NGSolveGui(App):
    def __init__(self, filename=None, local_path=None):
        self._local_path = local_path if local_path else os.path.expanduser("~")
        self.app_data = AppData()
        try:
            nthreads = int(self.usersettings.get("nthreads", 0))
            if nthreads > 0:
                import ngsolve as ngs
                ngs.SetNumThreads(nthreads)
                os.environ["MKL_NUM_THREADS"] = str(nthreads)
        except:
            pass

        # Toolbar buttons
        upload_file = QBtn(QTooltip("Load File"), ui_flat=True, ui_icon="mdi-plus")
        upload_file.on_click(self._load_file)
        savebtn = QBtn(QTooltip("Save Project"), ui_flat=True, ui_icon="mdi-content-save")
        savebtn.on_click(self.save_local)
        loadbtn = QBtn(QTooltip("Load Project"), ui_flat=True, ui_icon="mdi-folder-open")
        loadbtn.on_click(self.load_local)

        # Panel toggle buttons
        self._nav_btn = QBtn(QTooltip("Toggle Navigator"), ui_flat=True, ui_icon="mdi-page-layout-sidebar-left")
        self._nav_btn.on_click(self._toggle_navigator)
        self._prop_btn = QBtn(QTooltip("Toggle Properties"), ui_flat=True, ui_icon="mdi-page-layout-sidebar-right")
        self._prop_btn.on_click(self._toggle_property_panel)

        settings_btn = QBtn(Settings(self), QTooltip("User Settings"), ui_flat=True, ui_icon="mdi-cog")
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
            savebtn,
            loadbtn,
            QSpace(),
            self._nav_btn,
            self._prop_btn,
            settings_btn,
            close_btn,
            ui_style="height: 60px",
            ui_class="bg-primary text-grey-4",
        )

        # Three-column layout using flex
        self.navigator = Navigator(self.app_data, self._click_tab)
        self.property_panel = PropertyPanel()
        self.tab_panel = Panel(self.app_data)

        self._nav_visible = self.usersettings.get("nav_visible", True)
        self._prop_visible = self.usersettings.get("prop_visible", True)
        self._apply_panel_visibility()

        # Keybinding manager
        self.kb = KeybindingManager(self, after_action=self._sync_property_panel)

        page = Div(
            self.navigator,
            Div(self.tab_panel, ui_style="flex: 1; height: 100%; overflow: hidden;"),
            self.property_panel,
            ui_style="display: flex; flex-direction: row; height: calc(100vh - 60px); width: 100%;",
        )

        super().__init__(bar, page, self.kb.indicator, self.kb.help_overlay)

        self.set_colors(**_colors)
        self.on_load(self.__on_load)
        self.on_mounted(self._disable_contextmenu)

        # -- Global keybindings (always active) --
        kb = self.kb
        kb.add("h", kb.toggle_help, "Show keyboard shortcuts", "General")
        kb.add("ctrl+b", self._toggle_navigator, "Toggle navigator", "Panels")
        kb.add("ctrl+alt+b", self._toggle_property_panel, "Toggle property panel", "Panels")
        for i in range(1, 10):
            kb.add(str(i), lambda n=i: self.navigator.select_by_index(n), f"Select item {i}", "Navigation")
        self.add_keybinding("escape", lambda e: self.kb.on_escape())
        self.on_before_save(self.__on_before_save)
        if isinstance(filename, str):
            load_file(filename, self)
        elif isinstance(filename, list):
            for f in filename:
                load_file(f, self)

    def _disable_contextmenu(self):
        import webgpu.platform as pl
        pl.js.document.addEventListener(
            "contextmenu", pl.create_event_handler(lambda e: None, prevent_default=True)
        )

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
        load_file(file_path, self)

    def __on_before_save(self):
        self.storage.set("app_data", self.app_data.get_save_data(), use_pickle=True)

    def __on_load(self):
        data = self.storage.get("app_data")
        if data is not None:
            self.app_data._data.update(data)
        self._update()
        self.app_data._update = self._update

    def _click_tab(self, tabname):
        self.app_data.active_tab = tabname
        self.tab_panel.set_tab()
        self.navigator.update()
        comp = self.tab_panel.comp
        tab = self.app_data.get_tab(tabname)
        type_key = tab.get("type", "") if tab else ""
        self.property_panel.set_component(comp, type_key)
        self.kb.set_component(comp)

    def _toggle_navigator(self):
        self._nav_visible = not self._nav_visible
        self.usersettings.set("nav_visible", self._nav_visible)
        self._apply_panel_visibility()

    def _toggle_property_panel(self):
        self._prop_visible = not self._prop_visible
        self.usersettings.set("prop_visible", self._prop_visible)
        self._apply_panel_visibility()

    def _apply_panel_visibility(self):
        nav_extra = "width: 200px; min-width: 200px;" + ("" if self._nav_visible else " display: none;")
        prop_extra = "width: 280px; min-width: 280px;" + ("" if self._prop_visible else " display: none;")
        self.navigator.ui_style = sidebar_style(border_side="right", extra=nav_extra)
        self.property_panel.ui_style = sidebar_style(border_side="left", extra=prop_extra)

    def _sync_property_panel(self):
        """Rebuild property panel to sync checkbox states after keyboard toggling."""
        active = self.app_data.active_tab
        if active:
            comp = self.tab_panel.comp
            tab = self.app_data.get_tab(active)
            type_key = tab.get("type", "") if tab else ""
            self.property_panel.set_component(comp, type_key)

    def redraw(self, *args, **kwargs):
        self.app_data.set_needs_redraw()
        comp = self.tab_panel.comp
        if comp is not None:
            if hasattr(comp, "redraw"):
                comp.redraw()

    def _update(self):
        self.navigator.update()
        self.tab_panel.set_tab()
        active = self.app_data.active_tab
        if active:
            comp = self.tab_panel.comp
            tab = self.app_data.get_tab(active)
            type_key = tab.get("type", "") if tab else ""
            self.property_panel.set_component(comp, type_key)
            self.kb.set_component(comp)
        else:
            self.property_panel.set_component(None, "")
            self.kb.set_component(None)
