"""Floating overlay that shows element info on hover/pick."""

from ngapp.components import Div

from .cerbsim_style import viewport_overlay, viewport_overlay_visible


class PickOverlay(Div):
    """Semi-transparent pill overlay showing pick results (fades via class)."""

    def __init__(self):
        self._label = Div("")
        super().__init__(self._label, ui_class=viewport_overlay)

    def show_text(self, text):
        self._label.ui_children = [text]
        self.ui_class = viewport_overlay + viewport_overlay_visible

    def hide(self):
        self.ui_class = viewport_overlay
