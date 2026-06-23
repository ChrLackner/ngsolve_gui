"""Bottom status bar: live run status (left), quick stats, viewport mode.

The leftmost item doubles as the loading indicator: it shows "Ready" when idle
and, while a script/mesh job runs, the live status text polled from netgen plus
an inline progress bar and a cancel button.
"""

import ctypes
import threading
import time

from ngapp.components import Div, QIcon, QBtn, QTooltip, QSpinner

from .cerbsim_style import (
    statusbar,
    status_item,
    status_num,
    status_spacer,
    status_mode,
    status_chip,
    status_chip_ready,
    status_dot,
    status_dot_ready,
    status_track_inline,
    status_fill,
    status_fill_indeterminate,
    status_text as status_text_cls,
    mono,
    hint,
    gap_sm,
)


def _fmt(n):
    """Group thousands with thin spaces for readable counts."""
    try:
        return f"{int(n):,}".replace(",", " ")
    except (TypeError, ValueError):
        return str(n)


class StatusFooter(Div):
    def __init__(self):
        # -- Left: run-status indicator (idle "Ready" / busy text + progress) --
        self._idle = Div(
            Div(ui_class=str(status_dot) + " " + str(status_dot_ready)),
            "Ready",
            ui_class=str(status_chip) + " " + str(status_chip_ready),
        )

        self._status_text = Div("", ui_class=status_text_cls)
        self._pct_label = Div("", ui_class=str(mono) + " " + str(hint))
        self._bar_fill = Div(ui_class=status_fill)
        self._bar_track = Div(self._bar_fill, ui_class=status_track_inline)
        self._cancel_btn = QBtn(
            QTooltip("Cancel"),
            ui_icon="mdi-close", ui_flat=True, ui_dense=True, ui_round=True,
            ui_size="xs", ui_padding="2px",
        )
        self._cancel_btn.on_click(self._on_cancel)
        self._busy = Div(
            QSpinner(ui_color="primary", ui_size="14px"),
            self._status_text,
            self._bar_track,
            self._pct_label,
            self._cancel_btn,
            ui_class="row items-center no-wrap " + str(gap_sm),
        )
        self._busy.ui_hidden = True

        self._status_section = Div(
            self._idle, self._busy,
            ui_class=status_item,
        )

        # -- Middle: per-object quick stats --
        self._stats = Div(ui_class="row items-center no-wrap")

        # -- Right: viewport mode --
        self._mode_section = Div(ui_class=status_item)
        self._mode_section.ui_hidden = True

        # Polling state (mirrors the old floating status pill).
        self._thread = None
        self._thread_name = ""
        self._done_event = None
        self._generation = 0
        self._task_label = None

        super().__init__(
            self._status_section,
            self._stats,
            Div(ui_class=status_spacer),
            self._mode_section,
            ui_class=statusbar,
        )
        self.set_component(None, "")

    # -- active object -------------------------------------------------
    def set_component(self, comp, type_key):
        if comp is None:
            self._stats.ui_children = []
            return
        self._stats.ui_children = [
            self._stat(label, value) for label, value in self._stats_for(comp, type_key)
        ]

    def _stat(self, label, value):
        return Div(
            label, Div(value, ui_class=status_num),
            ui_class=status_item,
        )

    def _stats_for(self, comp, type_key):
        """Best-effort quick stats read directly off the active component."""
        try:
            if type_key == "geometry":
                geo = comp.geo
                out = []
                try:
                    out.append(("Solids", _fmt(len(geo.shape.solids))))
                except Exception:
                    pass
                out.append(("Faces", _fmt(len(geo.faces))))
                out.append(("Edges", _fmt(len(geo.edges))))
                return out
            if type_key == "mesh":
                import ngsolve as ngs
                m = comp.mesh
                return [
                    ("VOL", _fmt(m.GetNE(ngs.VOL))),
                    ("BND", _fmt(m.GetNE(ngs.BND))),
                    ("Points", _fmt(m.nv)),
                    ("Dim", f"{m.dim}D"),
                ]
            if type_key == "function":
                import ngsolve as ngs
                out = []
                cf = comp.cf
                if isinstance(cf, ngs.GridFunction):
                    try:
                        out.append(("DOF", _fmt(cf.space.ndof)))
                    except Exception:
                        pass
                dim = getattr(cf, "dim", 1)
                out.append(("Components", str(dim)))
                out.append(("Dim", f"{comp.mesh.dim}D"))
                return out
            if type_key == "plot":
                return [("Type", "plot"), ("Renderer", "Plotly")]
        except Exception:
            pass
        return []

    # -- viewport mode -------------------------------------------------
    def set_mode(self, name):
        if name:
            self._mode_section.ui_children = [
                QIcon(ui_name="mdi-keyboard-outline", ui_size="13px"),
                Div(f"{name} mode", ui_class=status_mode),
            ]
            self._mode_section.ui_hidden = False
        else:
            self._mode_section.ui_children = []
            self._mode_section.ui_hidden = True

    # -- run status (busy) ---------------------------------------------
    def show(self, filename, thread, done_event):
        """Enter the busy state and start polling netgen for live status."""
        self._generation += 1
        self._thread = thread
        self._done_event = done_event
        self._thread_name = thread.name if thread else ""
        self._task_label = None
        self._status_text.ui_children = [f"Running {filename} …"]
        self._set_indeterminate()
        self._idle.ui_hidden = True
        self._busy.ui_hidden = False
        self._start_poll(self._generation)

    def set_task(self, label):
        """Set a high-level task label shown in preference to the kernel status
        (e.g. 'Merging into the neighbouring face…'). Cleared on the next op."""
        self._task_label = label or None

    def hide(self):
        """Return to the idle 'Ready' state."""
        self._thread = None
        self._done_event = None
        self._task_label = None
        self._busy.ui_hidden = True
        self._idle.ui_hidden = False

    def _set_progress(self, percent):
        w = max(0, min(100, percent))
        self._bar_fill.ui_class = status_fill
        self._bar_fill.ui_style = f"width: {w:.1f}%;"
        self._pct_label.ui_children = [f"{w:.0f}%"]

    def _set_indeterminate(self):
        self._bar_fill.ui_class = status_fill_indeterminate
        self._bar_fill.ui_style = ""
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

                task = self._task_label
                if task:
                    self._status_text.ui_children = [task]
                    if percent > 0:
                        self._set_progress(percent)
                    else:
                        self._set_indeterminate()
                    if done:
                        self.hide()
                        break
                elif status_text and status_text != "idle":
                    self._status_text.ui_children = [status_text]
                    if percent > 0:
                        self._set_progress(percent)
                    else:
                        self._set_indeterminate()
                    if done:
                        self.hide()
                        break
                elif done:
                    self.hide()
                    break

        threading.Thread(target=poll, daemon=True, name="StatusPoll").start()

    def _on_cancel(self):
        self._generation += 1
        try:
            from .meshing_preview import set_terminate

            set_terminate(True)
        except Exception:
            pass
        thread = self._thread
        if thread and thread.is_alive() and self._thread_name != "IPythonEmbedder":
            try:
                ctypes.pythonapi.PyThreadState_SetAsyncExc(
                    ctypes.c_ulong(thread.ident),
                    ctypes.py_object(KeyboardInterrupt),
                )
            except Exception:
                pass
        self.hide()
