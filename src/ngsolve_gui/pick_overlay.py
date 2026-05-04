"""Floating overlay that shows element info on hover/pick."""

from ngapp.components import Div


class PickOverlay(Div):
    """Semi-transparent pill overlay showing pick results."""

    _STYLE = (
        "position: absolute; bottom: 8px; right: 8px; "
        "background: rgba(15,23,42,0.82); backdrop-filter: blur(4px); "
        "color: #e2e8f0; font-size: 12px; font-family: monospace; "
        "border-radius: 6px; padding: 4px 10px; "
        "pointer-events: none; white-space: pre; "
        "transition: opacity 0.15s; z-index: 10;"
    )

    def __init__(self):
        self._label = Div("", ui_style="min-height: 1.2em;")
        super().__init__(self._label, ui_style=self._STYLE)
        self.hide()

    def show_text(self, text):
        self._label.ui_children = [text]
        self.ui_style = self._STYLE + " opacity: 1;"

    def hide(self):
        self.ui_style = self._STYLE + " opacity: 0;"
