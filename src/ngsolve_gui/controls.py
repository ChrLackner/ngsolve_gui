"""Script-driven UI controls: a bar a running script can put widgets into.

::

    from ngsolve_gui import controls

    step = controls.add_slider("Timestep", 0, n - 1, value=0,
                               callback=show, format=lambda k: f"t = {t[k]:.1f} s")
    player = controls.Player(show, n, rate=10)
    controls.add_button("Play", callback=player.toggle, icon="mdi-play")
    controls.add_select("Speed", [1, 2, 5, 10, 25, 50], value=10,
                        format=lambda r: f"{r:g}/s",
                        callback=lambda r: setattr(player, "rate", r))

The bar lives between the viewport and the status bar and is app-level.

**Outside the GUI every call here is a no-op** returning a handle whose `value`
still works, so a case script that also runs headless does not need to branch.

Callbacks run on the websocket event thread.  Two consequences, both handled
here rather than in every script:

* an exception in a callback must not take the connection down, so it is caught
  and printed with its traceback;
* a slider dragged across 400 steps emits an event per pixel, and a callback
  that rewrites 100,000 dofs cannot keep up.  Events are therefore
  **coalesced**: while a callback runs, further values overwrite a single
  pending slot, and the LAST one is run when it returns.  Scrubbing stays
  smooth and never lands on a stale frame.
"""

from __future__ import annotations

import threading
import time
import traceback

from ngapp.components import Div, QBtn, QIcon, QSlider, QTooltip

from . import cerbsim_style as cb

__all__ = ["add_slider", "add_button", "add_select", "add_readout", "clear",
           "available", "control_bar", "Slider", "Button", "Select", "Readout",
           "Player"]

_NOTHING = object()          # "no value pending", which `None` cannot mean


def get_app():
    """The running :class:`~ngsolve_gui.app.NGSolveGui`, or `None` if headless."""
    from .meshing_preview import get_app as _get

    return _get()


def control_bar():
    """The app's :class:`ControlBar`, or `None` when there is no app."""
    app = get_app()
    return getattr(app, "controls", None) if app is not None else None


def available() -> bool:
    """True when controls will actually appear."""
    return control_bar() is not None


def _default_format(v):
    return f"{v:g}" if isinstance(v, (int, float)) and not isinstance(v, bool) \
        else str(v)


# --------------------------------------------------------------------- widgets
class _Handle:
    """Base: value access plus the coalescing callback dispatch."""

    def __init__(self, callback=None, value=None):
        self._callback = callback
        self._value = value
        self._lock = threading.Lock()
        self._pending = _NOTHING
        self._busy = False

    @property
    def value(self):
        return self._value

    def _dispatch(self, value):
        """Run `callback(value)`, keeping only the newest value while busy.

        Not a thread pool and not a drop: the newest value always runs, exactly
        once, after whatever is in flight finishes.  A dropped final event is
        the failure mode that leaves a slider reading one step and the picture
        showing another.
        """
        if self._callback is None:
            self._value = value
            return
        with self._lock:
            self._pending = value
            if self._busy:
                return
            self._busy = True
        try:
            while True:
                with self._lock:
                    v, self._pending = self._pending, _NOTHING
                    if v is _NOTHING:
                        self._busy = False
                        return
                self._value = v
                try:
                    self._callback(v)
                except Exception:                          # noqa: BLE001
                    traceback.print_exc()
        finally:
            with self._lock:
                self._busy = False


class Slider(_Handle):
    """A labelled slider with a live numeric readout."""

    def __init__(self, label, lo, hi, *, step=1, value=None, callback=None,
                 format=None, width=None, tooltip=None):
        lo, hi = (lo, hi) if hi >= lo else (hi, lo)
        value = lo if value is None else value
        super().__init__(callback, value)
        self.lo, self.hi, self.step = lo, hi, step
        self._format = format or (lambda v: f"{v:g}")
        self._slider = QSlider(
            ui_min=lo, ui_max=hi, ui_step=step, ui_model_value=value,
            ui_dense=True, ui_class=str(cb.ctl_slider),
            ui_style=f"width: {width}px;" if width else None,
        )
        self._slider.on_update_model_value(self._on_event)
        self._readout = Div(self._format(value), ui_class=str(cb.ctl_val))
        head = [Div(label, ui_class=str(cb.ctl_label))] if label else []
        if tooltip:
            head.insert(0, QTooltip(tooltip))
        self.comp = Div(*head, self._slider, self._readout,
                        ui_class=str(cb.ctl_group) + " " + str(cb.ctl_grow))

    def _on_event(self, event):
        v = getattr(event, "value", event)
        try:
            v = type(self.step)(v) if isinstance(self.step, int) else float(v)
        except (TypeError, ValueError):
            return
        self._readout.ui_children = [self._format(v)]
        self._dispatch(v)

    def set(self, value, *, fire: bool = False):
        """Move the slider from Python (what a play button drives)."""
        value = max(self.lo, min(self.hi, value))
        self._slider.ui_model_value = value
        self._readout.ui_children = [self._format(value)]
        if fire:
            self._dispatch(value)
        else:
            self._value = value
        return value


class Button(_Handle):
    def __init__(self, label=None, *, callback=None, icon=None, tooltip=None):
        super().__init__(callback, None)
        kids = [QTooltip(tooltip)] if tooltip else []
        self._btn = QBtn(*kids, ui_label=label, ui_icon=icon, ui_dense=True,
                         ui_flat=True, ui_no_caps=True,
                         ui_class=str(cb.ctl_btn))
        self._btn.on_click(lambda *a: self._dispatch(True))
        self.comp = Div(self._btn, ui_class=str(cb.ctl_group))

    def set_icon(self, icon):
        self._btn.ui_icon = icon

    def set_label(self, label):
        self._btn.ui_label = label


class Select(_Handle):
    """One of a fixed set of choices the script supplies, as a segmented row.

    A *selector* rather than a second slider, for the case it was added for --
    playback speed.  The useful rates span a decade or more (1 to 50 steps a
    second) and are wanted exactly: on a linear track most of the travel goes
    to rates nobody asks for, and landing on 23 when you meant 25 is not
    something anyone did on purpose.  And the bar already has a slider, which
    is the one people mean to grab.

    Segmented pills rather than a dropdown: every choice is visible without a
    click, changing it is one click rather than two, and there is no popup to
    land wrongly in a bar that is 38 pixels tall.  It is the same widget the
    property panel uses for its small fixed choices, so it looks like the rest
    of the app.  With more than about eight options this is the wrong shape --
    that is what a slider or a real dropdown is for.

    `format(value) -> str` makes the labels; the handle's `value` is always
    the underlying object, never its label.
    """

    def __init__(self, label, options, *, value=None, callback=None,
                 format=None, width=None, tooltip=None):
        options = list(options)
        if not options:
            raise ValueError("a Select needs at least one option")
        self._format = format or _default_format
        self.options = options
        value = options[0] if value is None else value
        super().__init__(callback, value)
        self._btns = []
        for v in options:
            b = Div(self._format(v), ui_class=self._btn_cls(v == value))
            b.on("click", lambda e=None, v=v: self._on_event(v))
            self._btns.append(b)
        self._seg = Div(*self._btns, ui_class=str(cb.ctl_seg),
                        ui_style=f"width: {width}px;" if width else None)
        head = [Div(label, ui_class=str(cb.ctl_label))] if label else []
        if tooltip:
            head.insert(0, QTooltip(tooltip))
        self.comp = Div(*head, self._seg, ui_class=str(cb.ctl_group))

    @staticmethod
    def _btn_cls(on):
        return str(cb.ctl_seg_btn) + (" " + str(cb.ctl_seg_btn_on) if on else "")

    def _paint(self, value):
        for b, v in zip(self._btns, self.options):
            b.ui_class = self._btn_cls(v == value)

    def _on_event(self, value):
        self._paint(value)
        self._dispatch(value)

    def set(self, value, *, fire: bool = False):
        """Choose *value* from Python.  Unknown values are ignored."""
        if value not in self.options:
            return self._value
        self._paint(value)
        if fire:
            self._dispatch(value)
        else:
            self._value = value
        return value


class Readout:
    """A piece of text the script updates -- a clock, a value, a status."""

    def __init__(self, text="", label=None):
        self._text = Div(text, ui_class=str(cb.ctl_val) + " " + str(cb.ctl_wide))
        head = [Div(label, ui_class=str(cb.ctl_label))] if label else []
        self.comp = Div(*head, self._text, ui_class=str(cb.ctl_group))

    def set(self, text):
        self._text.ui_children = [str(text)]


class Player:
    """Walk an index `0 .. n-1` at *rate* steps per second, on a wall clock.

    Playback of a stored transient, in the one form that stays honest when the
    frames cost more than the frame interval.  A loop that advances a fixed
    number of steps per tick and sleeps a fixed time does not: at 50 steps a
    second, with a reconstruct that takes 40 ms, it falls behind the clock a
    little more every frame and ends up minutes behind the slider.

    So the index is driven by *elapsed time*, not by tick count.  Each pass
    adds `elapsed * rate` steps, floors it, and jumps straight there -- the
    steps in between are **dropped, never queued**.  What that buys:

    * the requested rate is what you get in *seconds of run per second of wall
      clock*, at every rate, however slow the callback is;
    * nothing accumulates: there is no backlog to work off, so `stop()` stops
      now, and moving the slider by hand while it plays is answered at once;
    * `dropped` counts what was skipped, `drawn` what was shown, so "it cannot
      keep up" is a number rather than a feeling.

    The callback runs on this thread and is exception-caught, for the same
    reason the widget callbacks are: a raise here must not take playback (or
    the socket the caller is on) down with it.

    Widget-free on purpose -- it is the same object headless, where the script
    still wants to be able to walk the run.  Wire it to controls yourself::

        player = Player(show, n_steps, rate=10)
        add_button("Play", callback=lambda _: player.toggle())
        add_select("Speed", [1, 5, 10, 25], value=10,
                   callback=lambda v: setattr(player, "rate", v))
    """

    #: never divide by zero, and never sleep forever waiting for the next step.
    MIN_RATE = 1e-3
    #: longest single sleep, so `stop()` and a rate change are answered fast.
    MAX_SLEEP = 0.05

    def __init__(self, callback, n, *, rate=10.0, index=0, loop=True,
                 on_stop=None):
        self._callback = callback
        self.n = max(1, int(n))
        self.rate = float(rate)
        self.loop = bool(loop)
        self._on_stop = on_stop
        self._index = int(index) % self.n
        self._thread = None
        self._on = False
        self.dropped = 0
        self.drawn = 0

    # -- state -------------------------------------------------------------
    @property
    def playing(self) -> bool:
        return self._on

    @property
    def index(self) -> int:
        return self._index

    @index.setter
    def index(self, k):
        """Where playback continues from -- what a slider drag has to set."""
        self._index = int(k) % self.n

    # -- transport ---------------------------------------------------------
    def start(self) -> bool:
        """Start playing.  False if it already was."""
        if self._on:
            return False
        self._on = True
        self.dropped = self.drawn = 0
        self._thread = threading.Thread(target=self._run, daemon=True,
                                        name="ngsolve_gui.Player")
        self._thread.start()
        return True

    def stop(self) -> bool:
        """Stop playing.  False if it already was."""
        was, self._on = self._on, False
        thread, self._thread = self._thread, None
        if thread is not None and thread is not threading.current_thread():
            thread.join(timeout=2.0)
        if was and self._on_stop is not None:
            self._on_stop(self)
        return was

    def toggle(self, *_) -> bool:
        """Flip, and return whether it is now playing (a button binds here)."""
        if self._on:
            self.stop()
            return False
        self.start()
        return True

    # -- the loop ----------------------------------------------------------
    def _run(self):
        prev = time.monotonic()
        carry = 0.0                       # steps owed, fractional
        while self._on:
            rate = max(self.MIN_RATE, float(self.rate))
            now = time.monotonic()
            carry += (now - prev) * rate
            prev = now
            advance = int(carry)
            if not advance:
                time.sleep(min(self.MAX_SLEEP, (1.0 - carry) / rate))
                continue
            carry -= advance
            self.dropped += advance - 1   # everything between here and there
            k = self._index + advance
            if k >= self.n and not self.loop:
                self._emit(self.n - 1)
                self._on = False
                if self._on_stop is not None:
                    self._on_stop(self)
                return
            self._emit(k % self.n)

    def _emit(self, k):
        self._index = k
        self.drawn += 1
        try:
            self._callback(k)
        except Exception:                                  # noqa: BLE001
            traceback.print_exc()


class _Null:
    """Headless stand-in: keeps a value, does nothing, never raises."""

    def __init__(self, value=None):
        self.value = value
        self.comp = None

    def set(self, value, *, fire=False):
        self.value = value
        return value

    def set_icon(self, icon):
        pass

    def set_label(self, label):
        pass


class ControlBar(Div):
    """The bar itself.  Hidden while empty, so nothing changes for scripts
    that never touch it."""

    def __init__(self):
        self._items = []
        super().__init__(ui_class=str(cb.ctlbar))
        self.ui_hidden = True

    def add(self, handle):
        self._items.append(handle.comp)
        self.ui_children = list(self._items)
        self.ui_hidden = False
        return handle

    def clear(self):
        self._items = []
        self.ui_children = []
        self.ui_hidden = True


# ------------------------------------------------------------------ public API
def add_slider(label, lo, hi, *, step=1, value=None, callback=None,
               format=None, width=None, tooltip=None):
    """Add a slider bound to `callback(value)`.  Returns the handle.

    `format(value) -> str` drives the readout beside it, which is where a
    timestep index turns into a physical time.
    """
    bar = control_bar()
    if bar is None:
        return _Null(lo if value is None else value)
    return bar.add(Slider(label, lo, hi, step=step, value=value,
                          callback=callback, format=format, width=width,
                          tooltip=tooltip))


def add_button(label=None, *, callback=None, icon=None, tooltip=None):
    """Add a button bound to `callback(True)`.  Returns the handle."""
    bar = control_bar()
    if bar is None:
        return _Null()
    return bar.add(Button(label, callback=callback, icon=icon, tooltip=tooltip))


def add_select(label, options, *, value=None, callback=None, format=None,
               width=None, tooltip=None):
    """Add a dropdown over `options`, bound to `callback(value)`.

    The choices and the default are the script's -- playback rates in steps a
    second, a list of eigenmodes, a set of load cases::

        controls.add_select("Speed", [1, 2, 5, 10, 25, 50], value=10,
                            format=lambda r: f"{r:g}/s",
                            callback=lambda r: setattr(player, "rate", r))
    """
    bar = control_bar()
    if bar is None:
        return _Null((list(options) or [None])[0] if value is None else value)
    return bar.add(Select(label, options, value=value, callback=callback,
                          format=format, width=width, tooltip=tooltip))


def add_readout(text="", label=None):
    """Add a text field the script writes with `.set(...)`."""
    bar = control_bar()
    if bar is None:
        return _Null(text)
    return bar.add(Readout(text, label))


def clear():
    """Remove every control and hide the bar."""
    bar = control_bar()
    if bar is not None:
        bar.clear()
