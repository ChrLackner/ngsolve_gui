import ctypes
import os
import threading
import time

from ngapp.app import App
from ngapp.components import *

from .app_data import AppData
from .file_loader import load_file
from ngapp.keybindings import KeybindingManager, keybinding_styles
from .navigator import Navigator
from .property_panel import PropertyPanel
from .styles import css, theme, flex_fill, panel_full


class Panel(Div):
    def __init__(self, app_data):
        self.app_data = app_data
        self.comp = None
        super().__init__(ui_class=str(panel_full))
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
        nthreads = QInput(
            QTooltip(
                "Set number of threads used by NGSolve, 0 for all available cores. Only takes effect after restarting the application."
            ),
            ui_label="Number of Threads",
            ui_type="number",
            ui_model_value=val,
        )
        nthreads.on_update_model_value(self.app.usersettings.update("nthreads"))
        super().__init__(QCard(QCardSection("Settings"), QCardSection(nthreads)))


class StatusBar(Div):
    """Floating pill overlay at the bottom of the scene showing loading progress."""

    # Outer wrapper — anchored to the bottom-center of the nearest
    # position:relative ancestor (the scene container).
    _VISIBLE = (
        "position: fixed; bottom: 24px; left: 50%; transform: translateX(-50%); "
        "z-index: 1000; display: flex; flex-direction: column; align-items: stretch; "
        "background: rgba(15,23,42,0.88); backdrop-filter: blur(6px); "
        "border-radius: 12px; padding: 10px 18px 12px; min-width: 320px; "
        "max-width: 480px; box-shadow: 0 4px 24px rgba(0,0,0,0.25); "
        "color: #e2e8f0; font-size: 0.82rem;"
    )
    _HIDDEN = "display: none;"

    def __init__(self):
        # Top row: icon + label + cancel
        self._label = Div(
            "",
            ui_style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis;",
        )
        self._pct_label = Div(
            "",
            ui_style=(
                "white-space: nowrap; font-variant-numeric: tabular-nums; "
                "font-size: 0.78rem; color: #94a3b8; min-width: 36px; text-align: right;"
            ),
        )
        self._cancel_btn = QBtn(
            QTooltip("Cancel"),
            ui_icon="mdi-close",
            ui_flat=True,
            ui_dense=True,
            ui_round=True,
            ui_size="xs",
            ui_padding="2px",
            ui_color="grey-5",
        )
        self._cancel_btn.on_click(self._on_cancel)

        top_row = Div(
            QSpinner(ui_color="accent", ui_size="18px"),
            self._label,
            QSpace(),
            self._pct_label,
            self._cancel_btn,
            ui_style="display: flex; align-items: center; gap: 8px;",
        )

        # Progress bar (track + filled portion)
        self._bar_fill = Div(
            ui_style=(
                "height: 100%; width: 0%; border-radius: 3px; "
                "background: linear-gradient(90deg, #14B8A6, #0EA5E9); "
                "transition: width 0.3s ease;"
            ),
        )
        bar_track = Div(
            self._bar_fill,
            ui_style=(
                "height: 6px; border-radius: 3px; "
                "background: rgba(255,255,255,0.12); margin-top: 8px; "
                "overflow: hidden;"
            ),
        )

        self._thread = None
        self._done_event = None
        self._generation = 0

        super().__init__(top_row, bar_track, ui_style=self._HIDDEN)

    def show(self, filename, thread, done_event):
        self._generation += 1
        self._thread = thread
        self._done_event = done_event
        self._thread_name = thread.name if thread else ""
        self._label.ui_children = [f"Running {filename} \u2026"]
        self._pct_label.ui_children = [""]
        self._bar_fill.ui_style = (
            "height: 100%; width: 100%; border-radius: 3px; "
            "background: linear-gradient(90deg, #14B8A6, #0EA5E9); "
            "animation: indeterminate 1.4s ease infinite; "
            "transition: none;"
        )
        self.ui_style = self._VISIBLE
        self._start_poll(self._generation)

    def hide(self):
        self._thread = None
        self._done_event = None
        self.ui_style = self._HIDDEN

    def _set_progress(self, percent):
        """Set determinate progress (0–100)."""
        w = max(0, min(100, percent))
        self._bar_fill.ui_style = (
            f"height: 100%; width: {w:.1f}%; border-radius: 3px; "
            "background: linear-gradient(90deg, #14B8A6, #0EA5E9); "
            "transition: width 0.3s ease;"
        )
        self._pct_label.ui_children = [f"{w:.0f}%"]

    def _set_indeterminate(self):
        self._bar_fill.ui_style = (
            "height: 100%; width: 100%; border-radius: 3px; "
            "background: linear-gradient(90deg, #14B8A6, #0EA5E9); "
            "animation: indeterminate 1.4s ease infinite; "
            "transition: none;"
        )
        self._pct_label.ui_children = [""]

    def _start_poll(self, gen):
        def poll():
            from netgen.libngpy._meshing import _GetStatus

            while gen == self._generation:
                time.sleep(0.3)
                done_event = self._done_event
                if done_event is None:
                    break
                try:
                    status_text, percent = _GetStatus()
                except Exception:
                    status_text, percent = "idle", 0.0

                done = done_event.is_set()

                if status_text and status_text != "idle":
                    self._label.ui_children = [status_text]
                    if percent > 0:
                        self._set_progress(percent)
                    else:
                        self._set_indeterminate()
                    # Script finished but netgen hasn't reset status yet
                    if done:
                        self.hide()
                        break
                elif done:
                    self.hide()
                    break

        threading.Thread(target=poll, daemon=True, name="StatusPoll").start()

    def _on_cancel(self):
        self._generation += 1
        thread = self._thread
        # Only interrupt non-IPython threads; the IPython shell stays
        # alive for interactive use — just dismiss the pill.
        if (
            thread
            and thread.is_alive()
            and self._thread_name != "IPythonEmbedder"
        ):
            try:
                ctypes.pythonapi.PyThreadState_SetAsyncExc(
                    ctypes.c_ulong(thread.ident),
                    ctypes.py_object(KeyboardInterrupt),
                )
            except Exception:
                pass
        self.hide()


class NGSolveGui(App):
    def __init__(self, filename=None, local_path=None):
        self._local_path = local_path if local_path else os.path.expanduser("~")
        self.app_data = AppData()

        # Toolbar buttons
        upload_file = QBtn(QTooltip("Load File"), ui_flat=True, ui_icon="mdi-plus")
        upload_file.on_click(self._load_file)
        savebtn = QBtn(
            QTooltip("Save Project"), ui_flat=True, ui_icon="mdi-content-save"
        )
        savebtn.on_click(self.save_local)
        loadbtn = QBtn(
            QTooltip("Load Project"), ui_flat=True, ui_icon="mdi-folder-open"
        )
        loadbtn.on_click(self.load_local)

        # Panel toggle buttons
        self._nav_btn = QBtn(
            QTooltip("Toggle Navigator"),
            ui_flat=True,
            ui_icon="mdi-page-layout-sidebar-left",
        )
        self._nav_btn.on_click(self._toggle_navigator)
        self._prop_btn = QBtn(
            QTooltip("Toggle Properties"),
            ui_flat=True,
            ui_icon="mdi-page-layout-sidebar-right",
        )
        self._prop_btn.on_click(self._toggle_property_panel)

        settings_btn = QBtn(
            Settings(self), QTooltip("User Settings"), ui_flat=True, ui_icon="mdi-cog"
        )
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
        self.status_bar = StatusBar()

        self._nav_visible = self.usersettings.get("nav_visible", True)
        self._prop_visible = self.usersettings.get("prop_visible", True)
        self._nav_width = self.usersettings.get("nav_width", 200)
        self._prop_width = self.usersettings.get("prop_width", 280)

        self.kb = KeybindingManager(self, theme=theme)

        # Inner splitter: center | property panel (reverse so model = prop width)
        self._inner_splitter = QSplitter(
            ui_model_value=self._prop_width if self._prop_visible else 0,
            ui_unit="px",
            ui_reverse=True,
            ui_limits=[0, 500] if self._prop_visible else [0, 0],
            ui_emit_immediately=True,
            ui_slots={
                "before": [Div(self.tab_panel, ui_class=str(flex_fill))],
                "after": [self.property_panel],
            },
            ui_style="height: calc(100vh - 60px);",
        )
        self._inner_splitter.on_update_model_value(self._on_prop_width_change)

        # Outer splitter: navigator | inner splitter
        self._outer_splitter = QSplitter(
            ui_model_value=self._nav_width if self._nav_visible else 0,
            ui_unit="px",
            ui_limits=[0, 500] if self._nav_visible else [0, 0],
            ui_emit_immediately=True,
            ui_slots={
                "before": [self.navigator],
                "after": [self._inner_splitter],
            },
            ui_style="height: calc(100vh - 60px);",
        )
        self._outer_splitter.on_update_model_value(self._on_nav_width_change)

        page = self._outer_splitter

        super().__init__(bar, page, self.status_bar, self.kb.indicator, self.kb.help_overlay)

        theme.apply(self)
        css.inject(self)
        keybinding_styles.inject(self)
        self._inject_status_bar_css()
        self.on_load(self.__on_load)
        self.on_mounted(self._disable_contextmenu)

        # -- Global keybindings (always active) --
        kb = self.kb
        kb.add("h", kb.toggle_help, "Show keyboard shortcuts", "General")
        kb.add("ctrl+b", self._toggle_navigator, "Toggle navigator", "Panels")
        kb.add(
            "ctrl+alt+b", self._toggle_property_panel, "Toggle property panel", "Panels"
        )
        for i in range(1, 10):
            kb.add(
                str(i),
                lambda n=i: self.navigator.select_by_index(n),
                f"Select item {i}",
                "Navigation",
            )
        self.add_keybinding("escape", lambda e: self.kb.on_escape())
        self.on_before_save(self.__on_before_save)
        if isinstance(filename, str):
            self._load_with_status(filename)
        elif isinstance(filename, list):
            for f in filename:
                self._load_with_status(f)

    def _disable_contextmenu(self):
        import webgpu.platform as pl

        pl.js.document.addEventListener(
            "contextmenu", pl.create_event_handler(lambda e: None, prevent_default=True)
        )

    def _inject_status_bar_css(self):
        kf = (
            "@keyframes indeterminate {"
            "  0%   { transform: translateX(-100%); }"
            "  100% { transform: translateX(100%);  }"
            "}"
        )

        def _inject(js):
            el = js.document.createElement("style")
            el.textContent = kf
            js.document.head.appendChild(el)

        self.call_js(_inject)

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
        self._load_with_status(file_path)

    def _load_with_status(self, filename):
        if not filename:
            return
        result = load_file(filename, self)
        if result:
            thread, done_event = result
            name = os.path.basename(str(filename))
            self.status_bar.show(name, thread, done_event)

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

    def _on_nav_width_change(self, event):
        val = int(event.value)
        if val > 0:
            self._nav_width = val
            self.usersettings.set("nav_width", val)

    def _on_prop_width_change(self, event):
        val = int(event.value)
        if val > 0:
            self._prop_width = val
            self.usersettings.set("prop_width", val)

    def _apply_panel_visibility(self):
        if not hasattr(self, "_outer_splitter"):
            return
        if self._nav_visible:
            self._outer_splitter.ui_model_value = self._nav_width
            self._outer_splitter.ui_limits = [0, 500]
        else:
            self._outer_splitter.ui_model_value = 0
            self._outer_splitter.ui_limits = [0, 0]
        if self._prop_visible:
            self._inner_splitter.ui_model_value = self._prop_width
            self._inner_splitter.ui_limits = [0, 500]
        else:
            self._inner_splitter.ui_model_value = 0
            self._inner_splitter.ui_limits = [0, 0]


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
