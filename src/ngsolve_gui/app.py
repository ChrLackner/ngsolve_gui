import os
import threading
import time

from ngapp.app import App
from ngapp.components import *

from .app_data import AppData
from .file_loader import load_file
from ngapp.keybindings import KeybindingManager, keybinding_styles
from .navigator import Navigator
from .property_panel import empty_property_panel
from .prop_widgets import Segmented
from . import cerbsim_style as cb
from .cerbsim_style import theme, kb_theme, flex_fill, panel_full
from .system_monitor import SystemMonitor
from .footer import StatusFooter


class Panel(Div):
    def __init__(self, app_data):
        self.app_data = app_data
        self.comp = None
        super().__init__(ui_class=panel_full)
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
    """Designer-styled settings dropdown (sections, segmented theme, switches)."""

    def __init__(self, app):
        self.app = app
        us = app.usersettings

        theme_seg = Segmented(
            [("light", "Light"), ("dark", "Dark"), ("system", "System")],
            us.get("theme", "system"), self._on_theme,
        )
        colormap_select = QSelect(
            ui_options=[
                {"label": "Auto (theme)", "value": ""},
                "rainbow", "turbo", "viridis", "plasma", "cet_l20",
                "matlab:jet", "matplotlib:coolwarm",
            ],
            ui_model_value=us.get("default_colormap", ""),
            ui_dense=True, ui_options_dense=True, ui_emit_value=True, ui_map_options=True,
            ui_style="width: 134px;",
        )
        colormap_select.on_update_model_value(us.update("default_colormap"))

        ncolors = QInput(
            QTooltip("Number of color bands when colorbars are discrete."),
            ui_type="number", ui_dense=True,
            ui_model_value=int(us.get("default_ncolors", 8)), ui_style="width: 72px;",
        )
        ncolors.on_update_model_value(us.update("default_ncolors"))

        vecdensity = QInput(
            QTooltip("Default arrow grid density for vector fields "
                     "(cells across the longest domain side)."),
            ui_type="number", ui_dense=True,
            ui_model_value=int(us.get("default_vector_grid_size", 20)),
            ui_style="width: 72px;",
        )
        vecdensity.on_update_model_value(us.update("default_vector_grid_size"))

        nthreads = QInput(
            QTooltip("Threads used by NGSolve (0 = all cores). Restart to apply."),
            ui_type="number", ui_dense=True, ui_model_value=us.get("nthreads", 0),
            ui_style="width: 72px;",
        )
        nthreads.on_update_model_value(us.update("nthreads"))
        redraw = QInput(
            QTooltip("Min milliseconds between redraws while a script runs (0 = no throttle)."),
            ui_type="number", ui_dense=True, ui_suffix="ms",
            ui_model_value=int(us.get("redraw_interval_ms", 50)), ui_style="width: 96px;",
        )
        redraw.on_update_model_value(self._on_redraw)
        gpu = QSelect(
            QTooltip("Preferred GPU adapter. Restart to apply."),
            ui_options=["high-performance", "low-power"],
            ui_model_value=us.get("gpu_power_preference", "high-performance"),
            ui_dense=True, ui_options_dense=True, ui_emit_value=True,
            ui_style="width: 134px;",
        )
        gpu.on_update_model_value(us.update("gpu_power_preference"))

        timer_item = Div(
            QIcon(ui_name="mdi-timer-outline"), "Timer / profiling…",
            Div("diagnostics", ui_class=cb.menu_item_meta), ui_class=cb.menu_item,
        )
        timer_item.on("click", lambda e=None: app._open_timers())

        super().__init__(Div(
            Div("Appearance", ui_class=cb.menu_h),
            self._row("Theme", theme_seg),
            self._row("Default colormap", colormap_select),
            self._row("Discrete colormap", self._switch("default_discrete_colormap", False)),
            self._row("Default N colors", ncolors),
            Div(ui_class=cb.menu_sep),
            Div("Defaults", ui_class=cb.menu_h),
            self._row("Show axes", self._switch("axes_visible", True)),
            self._row("Show navigation cube", self._switch("navcube_visible", False)),
            self._row("Default vector density", vecdensity),
            Div(ui_class=cb.menu_sep),
            Div("Performance", ui_class=cb.menu_h),
            self._row("Worker threads", nthreads),
            self._row("Redraw interval", redraw),
            self._row("GPU preference", gpu),
            Div(ui_class=cb.menu_sep),
            timer_item,
            ui_class=cb.menu_card,
        ))

    def _row(self, label, control):
        return Div(Div(label, ui_class=cb.menu_label), control, ui_class=cb.menu_row)

    def _scls(self, on):
        return str(cb.prop_switch) + (" " + str(cb.prop_switch_on) if on else "")

    def _switch(self, key, default, on_set=None):
        state = {"v": bool(self.app.usersettings.get(key, default))}
        sw = Div(ui_class=self._scls(state["v"]))

        def toggle(e=None):
            state["v"] = not state["v"]
            sw.ui_class = self._scls(state["v"])
            self.app.usersettings.set(key, state["v"])
            if on_set:
                on_set(state["v"])
        sw.on("click", toggle)
        return sw

    def _on_theme(self, val):
        self.app.usersettings.set("theme", val)
        cb.set_theme(self.app, val)
        self.app._apply_viewport_theme()

    def _on_redraw(self, event):
        v = int(event.value)
        self.app.usersettings.set("redraw_interval_ms", v)
        self.app._redraw_interval = max(0, v) / 1000.0




class NGSolveGui(App):
    def __init__(self, filename=None, local_path=None):
        self._local_path = local_path
        self.app_data = AppData()

        # -- Toolbar buttons (compact flat icon buttons, muted like the designer) --
        def _tbtn(icon, tip, handler=None):
            btn = QBtn(
                QTooltip(tip), ui_flat=True, ui_dense=True, ui_icon=icon,
                ui_class=str(cb.topbar_icon),
            )
            if handler is not None:
                btn.on_click(handler)
            return btn

        # File actions
        upload_file = _tbtn(
            "mdi-file-plus-outline", "Load file  ·  geometry / mesh / .py", self._load_file
        )
        savebtn = _tbtn("mdi-content-save-outline", "Save Project", self.save_local)
        loadbtn = _tbtn("mdi-folder-open-outline", "Load Project", self.load_local)
        file_group = Div(upload_file, savebtn, loadbtn, ui_class=cb.tb_group)

        # Settings + quit (panel toggles removed — sidebars are draggable;
        # theme lives in the settings menu).
        settings_btn = QBtn(
            Settings(self), QTooltip("User Settings"),
            ui_flat=True, ui_dense=True, ui_icon="mdi-cog-outline",
            ui_class=str(cb.topbar_icon),
        )
        close_btn = _tbtn("mdi-close", "Quit", self.quit)
        close_btn.ui_class = str(cb.topbar_icon) + " " + str(cb.topbar_icon_danger)
        view_group = Div(settings_btn, close_btn, ui_class=cb.tb_group)

        ngs_logo = Div(
            QImg(
                ui_src=self.load_asset("ngsolve-mark.png"),
                ui_height="34px",
                ui_width="34px",
                ui_fit="contain",
            ),
            Div("Netgen / NGSolve", ui_class=cb.brand_wordmark),
            ui_class=cb.brand,
        )

        self.system_monitor = SystemMonitor()

        # -- Redraw throttling state --
        self._redraw_lock = threading.Lock()
        self._redraw_pending = False
        self._redraw_timer_running = False
        self._last_redraw_time = 0.0
        self._redraw_interval = max(0, int(self.usersettings.get("redraw_interval_ms", 50))) / 1000.0

        bar = QBar(
            ngs_logo,
            file_group,
            QSpace(),
            self.system_monitor,
            Div(ui_class=cb.tb_sep),
            view_group,
            ui_class=cb.app_bar,
        )

        # Three-column layout using flex
        self.navigator = Navigator(self.app_data, self._click_tab, self._load_file)
        # The property panel is owned by each component; this host swaps in the
        # active component's own panel (built via comp.build_property_panel()).
        self.property_host = Div(empty_property_panel(), ui_class=panel_full)
        self.tab_panel = Panel(self.app_data)
        self.footer = StatusFooter()

        from .meshing_preview import install as _install_meshing_preview

        _install_meshing_preview(self)

        self._nav_visible = self.usersettings.get("nav_visible", True)
        self._prop_visible = self.usersettings.get("prop_visible", True)
        self._nav_width = self.usersettings.get("nav_width", 200)
        self._prop_width = self.usersettings.get("prop_width", 280)

        self.kb = KeybindingManager(self, theme=kb_theme)

        # Inner splitter: center | property panel (reverse so model = prop width)
        self._inner_splitter = QSplitter(
            ui_model_value=self._prop_width if self._prop_visible else 0,
            ui_unit="px",
            ui_reverse=True,
            ui_limits=[0, 500] if self._prop_visible else [0, 0],
            ui_emit_immediately=True,
            ui_slots={
                "before": [Div(self.tab_panel, ui_class=flex_fill)],
                "after": [self.property_host],
            },
            ui_class=cb.body_height,
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
            ui_class=cb.body_height,
        )
        self._outer_splitter.on_update_model_value(self._on_nav_width_change)

        page = self._outer_splitter

        # Timer / profiling diagnostics dialog (opened from the settings menu).
        self._timer_body = Div()
        timer_refresh = QBtn(QTooltip("Refresh"), ui_icon="mdi-refresh",
                             ui_flat=True, ui_dense=True, ui_round=True, ui_size="sm")
        timer_refresh.on_click(lambda *a: self._refresh_timers())
        self._timer_dialog = QDialog(QCard(
            Div(Div("Timer / profiling", ui_class=cb.prop_title_text), timer_refresh,
                ui_class=cb.prop_title),
            QSeparator(),
            self._timer_body,
            ui_class="cb-timer-card",
        ))

        super().__init__(
            bar, page, self.footer, self._timer_dialog,
            self.kb.indicator, self.kb.help_overlay,
        )

        # Keep the footer's mode indicator in sync with the keybinding manager.
        self._wire_footer_mode()

        cb.install(self, default_theme=self.usersettings.get("theme", "system"))
        from .webgpu_tab import sync_default_viewport_clear
        sync_default_viewport_clear()
        keybinding_styles.inject(self)
        self.on_load(self.__on_load)

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

    def _load_file(self):
        from ngapp.utils import EnvironmentType, get_environment

        if get_environment().type == EnvironmentType.LOCAL_APP:
            from .native_dialog import open_file_dialog

            initialdir = (
                self._local_path
                or self.usersettings.get("load_dir", "")
                or os.path.expanduser("~")
            )
            file_path = open_file_dialog(initialdir=initialdir)
            if file_path:
                self._local_path = os.path.dirname(file_path)
                self.usersettings.set("load_dir", self._local_path)
        else:
            file_path = self._pick_file_to_temp()
        self._load_with_status(file_path)

    def _pick_file_to_temp(self):
        """Browser-picker fallback: the File System Access API only hands us the
        file's content and name (never a real path), so materialise it in a temp
        dir keeping the original name (preserves multi-part suffixes like
        .vol.gz that the loader dispatches on)."""
        import tempfile

        try:
            handles = self.js.showOpenFilePicker({"multiple": False})
        except Exception:
            return None
        if not handles:
            return None
        js_file = handles[0].getFile()
        tmpdir = tempfile.mkdtemp(prefix="ngsolve_gui_")
        file_path = os.path.join(tmpdir, js_file.name)
        with open(file_path, "wb") as f:
            f.write(js_file.arrayBuffer())
        return file_path

    def _load_with_status(self, filename):
        if not filename:
            return
        result = load_file(filename, self)
        if result:
            thread, done_event = result
            name = os.path.basename(str(filename))
            self.footer.show(name, thread, done_event)

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
        self._show_property_panel(comp)
        self.footer.set_component(comp, type_key)
        self.kb.set_component(comp)

    def _show_property_panel(self, comp):
        """Host the active component's own property panel (or a placeholder)."""
        if comp is not None and hasattr(comp, "build_property_panel"):
            self.property_host.ui_children = [comp.build_property_panel()]
        else:
            self.property_host.ui_children = [empty_property_panel()]

    def _toggle_navigator(self):
        self._nav_visible = not self._nav_visible
        self.usersettings.set("nav_visible", self._nav_visible)
        self._apply_panel_visibility()

    def _toggle_property_panel(self):
        self._prop_visible = not self._prop_visible
        self.usersettings.set("prop_visible", self._prop_visible)
        self._apply_panel_visibility()

    def _wire_footer_mode(self):
        """Mirror the keybinding manager's active mode into the footer."""
        kb = self.kb
        orig_enter = kb._enter_mode
        orig_exit = kb._exit_mode

        def _enter(name):
            orig_enter(name)
            self.footer.set_mode(kb._mode)

        def _exit():
            orig_exit()
            self.footer.set_mode(None)

        kb._enter_mode = _enter
        kb._exit_mode = _exit

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

    def _open_timers(self):
        self._refresh_timers()
        self._timer_dialog.ui_model_value = True

    def _refresh_timers(self):
        try:
            import ngsolve
            timers = sorted(ngsolve.Timers(), key=lambda t: -t.get("time", 0.0))[:40]
        except Exception:
            timers = []
        if not timers:
            rows = [Div("No timing data recorded yet.",
                        ui_class=cb.hint, ui_style="padding: 12px;")]
        else:
            rows = []
            for t in timers:
                rows.append(Div(
                    Div(t.get("name", ""), ui_class="ellipsis", ui_style="flex: 1; min-width: 0;"),
                    Div(f"{t.get('time', 0.0):.4f} s", ui_class=cb.mono, ui_style="flex: none;"),
                    ui_class="row items-center no-wrap " + str(cb.gap_sm),
                    ui_style="padding: 4px 2px; border-bottom: 1px solid var(--border-faint);"
                             " font-size: 12px;",
                ))
        self._timer_body.ui_children = [
            Div(*rows, ui_style="max-height: 56vh; overflow: auto; min-width: 400px; padding: 4px 14px 12px;")
        ]

    def _apply_viewport_theme(self):
        """Update the scene background of every open 3D tab to the active theme."""
        from .webgpu_tab import sync_default_viewport_clear
        sync_default_viewport_clear()  # so tabs opened later also start correct
        for tab in self.app_data.get_tabs().values():
            comp = tab.get("component")
            if comp is not None and hasattr(comp, "apply_viewport_theme"):
                comp.apply_viewport_theme()


    def redraw(self, *args, **kwargs):
        self.app_data.set_needs_redraw()
        self._request_redraw()

    def _request_redraw(self):
        """Coalesce rapid redraw calls into at most one actual redraw per interval.

        When a Python script calls ngs.Redraw() in a tight loop (e.g. time-stepping),
        this avoids blocking the script thread and flooding the GPU with renders.
        Only the *active* tab is redrawn; other tabs pick up `_redraw_needed` when
        they are next switched to (via `redraw_if_needed` on mount).

        The trailing-edge timer guarantees the *last* requested redraw is always
        rendered, even if no further calls arrive.
        """
        interval = self._redraw_interval
        if interval <= 0:
            # No throttling — redraw immediately on every call.
            self._do_redraw()
            return

        now = time.monotonic()
        with self._redraw_lock:
            self._redraw_pending = True
            elapsed = now - self._last_redraw_time
            if elapsed >= interval:
                # Enough time passed — redraw immediately (leading edge).
                self._do_redraw()
            elif not self._redraw_timer_running:
                # Schedule a trailing-edge timer so the last redraw is never lost.
                self._redraw_timer_running = True
                delay = interval - elapsed
                threading.Timer(delay, self._deferred_redraw).start()

    def _deferred_redraw(self):
        """Trailing-edge timer callback — guarantees the final redraw fires."""
        with self._redraw_lock:
            self._redraw_timer_running = False
            if self._redraw_pending:
                self._do_redraw()

    def _do_redraw(self):
        """Actually perform the redraw (must be called with _redraw_lock held, or interval=0)."""
        self._redraw_pending = False
        self._last_redraw_time = time.monotonic()
        comp = self.tab_panel.comp
        if comp is not None and hasattr(comp, "redraw"):
            comp.redraw()

    def _update(self):
        self.navigator.update()
        self.tab_panel.set_tab()
        active = self.app_data.active_tab
        if active:
            comp = self.tab_panel.comp
            tab = self.app_data.get_tab(active)
            type_key = tab.get("type", "") if tab else ""
            self._show_property_panel(comp)
            self.footer.set_component(comp, type_key)
            self.kb.set_component(comp)
        else:
            self._show_property_panel(None)
            self.footer.set_component(None, "")
            self.kb.set_component(None)
