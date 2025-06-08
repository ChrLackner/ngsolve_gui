from ngapp.components import *


class ColorpickerButton(QBtn):
    def __init__(self, default, **kwargs):
        self.color = (
            int(255 * default[0]),
            int(255 * default[1]),
            int(255 * default[2]),
            default[3] if len(default) == 4 else 1.0,
        )
        self.picker = QColor(
            ui_format_model="rgba",
            ui_model_value=self.to_rgba_string(),
            ui_default_view="palette",
        )
        self.picker.on_update_model_value(self._change_color)
        menu = QMenu(self.picker)
        super().__init__(
            menu, ui_style="background-color: " + self.to_hex_string(), **kwargs
        )

    def to_rgba_string(self):
        return f"rgb(" + ",".join((str(vi) for vi in self.color)) + ")"

    def to_hex_string(self):
        return (
            f"#{int(self.color[0]):02x}{int(self.color[1]):02x}{int(self.color[2]):02x}"
        )

    def _change_color(self, event):
        c = tuple(vi for vi in event.value[5:-1].split(","))
        self.color = (int(c[0]), int(c[1]), int(c[2]), float(c[3]))
        self.ui_style = "background-color: " + self.to_hex_string()

    def on_update_model_value(self, func, *arg, **kwargs):
        self.picker.on_update_model_value(func, *arg, **kwargs)


class RegionColors(Div):
    def __init__(
        self, comp, colors: list[tuple[float, float, float, float]], names: list[str]
    ):
        self.name_color_map = {name: set() for name in set(names)}
        for name, color in zip(names, colors):
            self.name_color_map[name].add(color)
        super().__init__()
        self.create_layout()
        self._on_change_callbacks = []

    def create_layout(self):
        rows = []
        for name, colors in self.name_color_map.items():
            if len(colors) == 1:
                dcol = list(colors)[0]
            else:
                dcol = None
            color_picker = ColorpickerButton(default=dcol)
            color_picker.on_update_model_value(
                lambda e, name=name: self.change_color(name, e.value)
            )

            row = Div(
                Div(color_picker, ui_class="col-auto"),
                Div(Label(name), ui_class="col-auto", ui_style="padding-left: 5px;"),
                ui_style="padding: 5px;",
                ui_class="row items-center",
            )
            rows.append(row)
        self.ui_children = rows

    def on_change_color(self, func):
        """Register a callback function that is called when a color is changed."""
        self._on_change_callbacks.append(func)

    def change_color(self, name, color):
        c = tuple(vi for vi in color[5:-1].split(","))
        color = (int(c[0]) / 255, int(c[1]) / 255, int(c[2]) / 255, float(c[3]))
        for func in self._on_change_callbacks:
            func(name, color)
