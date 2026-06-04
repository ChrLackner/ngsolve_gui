"""Floating pick-info card shown on hover/pick (designer style).

Hover fires on every mouse move, so the card updates its values *in place*
(reusing the row components) and only toggles its visibility class on an actual
show/hide — otherwise the constant DOM churn / fade restart makes it flicker.
"""

from ngapp.components import Div, QIcon

from . import cerbsim_style as cb


class PickOverlay(Div):
    """Bottom-right card showing structured pick info (fades in/out)."""

    def __init__(self):
        self._header_text = Div("")
        self._header = Div(QIcon(ui_name="mdi-crosshairs"), self._header_text,
                           ui_class=str(cb.pk_h))
        self._rows = Div()
        self._labels = None      # current row labels (structure key)
        self._value_divs = []    # value Div per row, for in-place updates
        self._visible = False
        self._last_header = None
        super().__init__(self._header, self._rows, ui_class=str(cb.vp_pick))

    def _set_header(self, header):
        if header != self._last_header:
            self._last_header = header
            self._header_text.ui_children = [header]

    def show_info(self, header, rows, accent_last=False):
        """header: str; rows: list of (label, value). Last row may be accented."""
        self._set_header(header)
        labels = [k for k, _ in rows]
        if labels != self._labels:
            # Structure changed — rebuild the rows once.
            self._labels = labels
            self._value_divs = []
            out = []
            n = len(rows)
            for i, (k, v) in enumerate(rows):
                vcls = cb.pk_v_accent if (accent_last and i == n - 1) else cb.pk_v
                vdiv = Div(str(v), ui_class=str(vcls))
                self._value_divs.append(vdiv)
                out.append(Div(Div(k), vdiv, ui_class=str(cb.pk_r)))
            self._rows.ui_children = out
        else:
            # Same structure — just update the value text (no DOM churn).
            for vdiv, (_, v) in zip(self._value_divs, rows):
                vdiv.ui_children = [str(v)]
        self._set_visible(True)

    def show_text(self, text):
        """Single-line fallback (used by geometry picking)."""
        self._set_header("Picked")
        if self._labels != ["_text"]:
            self._labels = ["_text"]
            self._value_divs = [Div(str(text))]
            self._rows.ui_children = list(self._value_divs)
        else:
            self._value_divs[0].ui_children = [str(text)]
        self._set_visible(True)

    def hide(self):
        self._set_visible(False)

    def _set_visible(self, visible):
        if visible == self._visible:
            return
        self._visible = visible
        self.ui_class = (str(cb.vp_pick) + " " + str(cb.vp_pick_visible)
                         if visible else str(cb.vp_pick))
