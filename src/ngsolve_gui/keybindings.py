from ngapp.components import *

_INDICATOR_HIDDEN = (
    "position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%);"
    " background: rgba(15, 23, 42, 0.92); color: white; padding: 8px 20px;"
    " border-radius: 8px; font-size: 0.85rem; z-index: 9999;"
    " backdrop-filter: blur(4px); box-shadow: 0 4px 12px rgba(0,0,0,0.3);"
    " align-items: center; gap: 8px; display: none;"
)

_INDICATOR_VISIBLE = (
    "position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%);"
    " background: rgba(15, 23, 42, 0.92); color: white; padding: 8px 20px;"
    " border-radius: 8px; font-size: 0.85rem; z-index: 9999;"
    " backdrop-filter: blur(4px); box-shadow: 0 4px 12px rgba(0,0,0,0.3);"
    " align-items: center; gap: 8px; display: flex;"
)

_KEY_BADGE = (
    "display: inline; background: #334155; padding: 1px 6px;"
    " border-radius: 3px; font-family: monospace; margin-right: 4px;"
)

_OVERLAY_HIDDEN = (
    "position: fixed; top: 0; left: 0; width: 100%; height: 100%;"
    " background: rgba(0,0,0,0.5); z-index: 9998;"
    " align-items: center; justify-content: center; display: none;"
)

_OVERLAY_VISIBLE = (
    "position: fixed; top: 0; left: 0; width: 100%; height: 100%;"
    " background: rgba(0,0,0,0.5); z-index: 9998;"
    " align-items: center; justify-content: center; display: flex;"
)


class ModeIndicator(Div):
    """Floating bar showing available keys in the active submenu."""

    def __init__(self):
        super().__init__(ui_style=_INDICATOR_HIDDEN)

    def show(self, mode_name, entries):
        children = [
            Div(mode_name, ui_style="font-weight: 700; color: #14B8A6;"),
        ]
        for key, desc in entries:
            children.append(
                Div(
                    Div(key, ui_style=_KEY_BADGE),
                    desc,
                    ui_style="display: flex; align-items: center;",
                )
            )
        children.append(
            Div(
                Div("Esc", ui_style=_KEY_BADGE),
                "Cancel",
                ui_style="display: flex; align-items: center; color: #94a3b8;",
            )
        )
        self.ui_children = children
        self.ui_style = _INDICATOR_VISIBLE

    def hide(self):
        self.ui_children = []
        self.ui_style = _INDICATOR_HIDDEN


class HelpOverlay(Div):
    """Floating overlay showing all registered keybindings."""

    def __init__(self, manager):
        self._manager = manager
        super().__init__(ui_style=_OVERLAY_HIDDEN)

    def show(self):
        entries = self._manager.entries
        groups = {}
        for key, desc, group in entries:
            groups.setdefault(group, []).append((key, desc))

        children = [
            Div(
                "Keyboard Shortcuts",
                ui_style=(
                    "font-size: 1.1rem; font-weight: 700; padding: 16px 20px 8px;"
                    " border-bottom: 1px solid #e0e0e0;"
                ),
            ),
        ]
        for group_name, bindings in groups.items():
            children.append(
                Div(
                    group_name,
                    ui_style=(
                        "font-size: 0.75rem; letter-spacing: 0.05em; text-transform: uppercase;"
                        " font-weight: 700; color: #78909c; padding: 12px 20px 4px;"
                    ),
                )
            )
            for key, desc in bindings:
                children.append(
                    Div(
                        Div(
                            key,
                            ui_style=(
                                "min-width: 80px; font-family: monospace; font-weight: 600;"
                                " background: #f1f5f9; padding: 2px 8px; border-radius: 4px;"
                                " font-size: 0.8rem; text-align: center;"
                            ),
                        ),
                        Div(desc, ui_style="font-size: 0.85rem;"),
                        ui_style="display: flex; align-items: center; gap: 12px; padding: 3px 20px;",
                    )
                )

        children.append(
            Div(
                "Press H or Esc to close",
                ui_style="text-align: center; color: #94a3b8; font-size: 0.8rem; padding: 12px;",
            )
        )

        card = Div(
            *children,
            ui_style=(
                "background: white; border-radius: 12px; max-width: 480px; width: 90%;"
                " max-height: 80vh; overflow-y: auto; box-shadow: 0 8px 32px rgba(0,0,0,0.2);"
            ),
        )
        self.ui_children = [card]
        self.ui_style = _OVERLAY_VISIBLE

    def hide(self):
        self.ui_children = []
        self.ui_style = _OVERLAY_HIDDEN


class KeybindingManager:
    """Two-layer keybinding manager with floating indicator and help overlay.

    *Global* bindings (``add``) are always active.
    *Component* bindings come from ``comp.get_keybindings()`` and are swapped
    on every ``set_component()`` call so only relevant shortcuts are shown.

    ``get_keybindings()`` returns::

        {
            "flat": [(key, callback, description, group), ...],
            "modes": [(trigger_key, mode_name, [(key, cb, desc), ...]), ...],
        }
    """

    def __init__(self, app, after_action=None):
        self._app = app
        self._after_action = after_action

        # Global layer
        self._global_entries = []
        self._global_key_callbacks = {}

        # Active set (rebuilt on set_component)
        self._entries = []
        self._key_callbacks = {}
        self._modes = {}  # mode_name -> {key: callback}
        self._mode_entries = {}  # mode_name -> [(key, desc)]
        self._mode_triggers = {}  # trigger_key -> mode_name

        self._registered_keys = set()
        self._mode = None
        self._help_visible = False
        self.indicator = ModeIndicator()
        self.help_overlay = HelpOverlay(self)

    @property
    def entries(self):
        return list(self._entries)

    # -- Global bindings ------------------------------------------------

    def add(self, key, callback, description, group="General"):
        """Register a global keybinding (always active)."""
        self._global_entries.append((key, description, group))
        self._global_key_callbacks[key] = callback
        self._entries.append((key, description, group))
        self._key_callbacks[key] = callback
        self._ensure_key(key)

    # -- Component bindings ---------------------------------------------

    def set_component(self, comp):
        """Swap component bindings. Only these + global are active."""
        self._exit_mode()

        # Rebuild from global
        self._entries = list(self._global_entries)
        self._key_callbacks = dict(self._global_key_callbacks)
        self._modes = {}
        self._mode_entries = {}
        self._mode_triggers = {}

        if comp is None or not hasattr(comp, "get_keybindings"):
            return

        spec = comp.get_keybindings()

        for key, cb, desc, group in spec.get("flat", []):
            self._entries.append((key, desc, group))
            self._key_callbacks[key] = self._wrap(cb)
            self._ensure_key(key)

        for trigger, name, bindings in spec.get("modes", []):
            self._modes[name] = {}
            self._mode_entries[name] = []
            for key, cb, desc in bindings:
                self._modes[name][key] = self._wrap(cb)
                self._mode_entries[name].append((key, desc))
                self._entries.append((f"{trigger} \u2192 {key}", desc, name))
                self._ensure_key(key)
            self._entries.append((trigger, f"{name}\u2026", name))
            self._mode_triggers[trigger] = name
            self._key_callbacks[trigger] = lambda n=name: self._enter_mode(n)
            self._ensure_key(trigger)

    # -- Internals ------------------------------------------------------

    def _wrap(self, cb):
        def wrapped():
            cb()
            if self._after_action:
                self._after_action()

        return wrapped

    def _ensure_key(self, key):
        if key not in self._registered_keys:
            self._registered_keys.add(key)
            self._app.add_keybinding(key, lambda e, k=key: self._dispatch(k))

    def _dispatch(self, key):
        if self._help_visible and key == "h":
            self.toggle_help()
            return
        if self._mode:
            handlers = self._modes.get(self._mode, {})
            if key in handlers:
                handlers[key]()
                self._exit_mode()
                return
            exited_mode = self._mode
            self._exit_mode()
            if self._mode_triggers.get(key) == exited_mode:
                return
        cb = self._key_callbacks.get(key)
        if cb:
            cb()

    def _enter_mode(self, mode_name):
        if self._mode == mode_name:
            self._exit_mode()
            return
        self._mode = mode_name
        self.indicator.show(mode_name, self._mode_entries.get(mode_name, []))

    def _exit_mode(self):
        self._mode = None
        self.indicator.hide()

    def toggle_help(self):
        if self._mode:
            self._exit_mode()
        self._help_visible = not self._help_visible
        if self._help_visible:
            self.help_overlay.show()
        else:
            self.help_overlay.hide()

    def on_escape(self):
        if self._mode:
            self._exit_mode()
        elif self._help_visible:
            self._help_visible = False
            self.help_overlay.hide()
