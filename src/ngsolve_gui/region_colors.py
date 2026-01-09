from ngapp.components import *

def get_random_colors(n):
    import random, math, itertools

    n = max(math.floor((n - 1) ** (1 / 3)), 2)
    n = 2
    while n**3 + 1 < n:
        n += 1
    vals = [int(255 * i / (n - 1)) for i in range(n)]
    colors = [
        (vals[colr], vals[colg], vals[colb])
        for colr, colg, colb in itertools.product(range(n), range(n), range(n))
    ][1:-1]
    random.shuffle(colors)
    colors = [
        [c[0]/255, c[1]/255, c[2]/255, 1]
        for c in colors
    ]
    return colors[:n]

class ColorpickerButton(QBtn):
    def __init__(self, default, **kwargs):
        if default is None:
            default = (0.5, 0.5, 0.5, 1.0)
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
        return f"rgba(" + ",".join((str(vi) for vi in self.color)) + ")"

    def to_hex_string(self):
        return (
            f"#{int(self.color[0]):02x}{int(self.color[1]):02x}{int(self.color[2]):02x}"
        )

    def set_color(self, color):
        self.color = (
            int(color[0]),
            int(color[1]),
            int(color[2]),
            color[3] if len(color) == 4 else self.color[3],
        )
        self.ui_style = "background-color: " + self.to_hex_string()
        self.picker.ui_model_value = self.to_rgba_string()

    def _change_color(self, event):
        c = tuple(vi for vi in event.value[5:-1].split(","))
        self.color = (int(c[0]), int(c[1]), int(c[2]), float(c[3]))
        self.ui_style = "background-color: " + self.to_hex_string()

    def on_update_model_value(self, func, *arg, **kwargs):
        self.picker.on_update_model_value(func, *arg, **kwargs)


class RegionColors(Div):
    def __init__(
        self, title, colors: list[tuple[float, float, float, float]], names: list[str]
    ):
        self.name_color_map = {name: set() for name in set(names)}
        self.title = title
        for name, color in zip(names, colors):
            self.name_color_map[name].add(color)
        super().__init__()
        self.create_layout()
        self._on_change_callbacks = []

    def create_layout(self):
        rows = []
        self.pickers = []
        randomize_btn = QBtn(
            "Randomize", ui_icon="mdi-dice-multiple", ui_flat=True, ui_color="accent"
        )
        randomize_btn.on_click(self.randomize_colors)
        rows.append(
            Row(
                Div(Heading(self.title, 7), ui_class="col-auto"),
                Div(randomize_btn, ui_class="col-auto"),
            )
        )
        for name, colors in self.name_color_map.items():
            if len(colors) == 1:
                dcol = list(colors)[0]
            else:
                dcol = None
            color_picker = ColorpickerButton(default=dcol)
            self.pickers.append(color_picker)
            color_picker.on_update_model_value(
                lambda e, name=name: self.change_color(name, e.value)
            )
            visible_cb = QCheckbox(ui_model_value=True)
            visible_cb.on_update_model_value(
                lambda e, name=name: self.change_visibility(name, e.value)
            )

            row = Div(
                Div(visible_cb, ui_class="col-auto"),
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

    def change_visibility(self, name, visible):
        c = list(self.name_color_map[name])[0]
        color = (c[0], c[1], c[2], 1.0 if visible else 0.0)
        self.name_color_map[name] = {color}
        for func in self._on_change_callbacks:
            func([name], [(color[0] / 255, color[1] / 255, color[2] / 255, color[3])])

    def randomize_colors(self):
        import random, math, itertools
        n = 2
        while n**3 - 2 < len(self.name_color_map):
            n += 1
        vals = [int(255 * i / (n - 1)) for i in range(n)]
        colors = [
            (vals[colr], vals[colg], vals[colb])
            for colr, colg, colb in itertools.product(range(n), range(n), range(n))
        ][1:-1]
        random.shuffle(colors)
        colors = [
            [c[0], c[1], c[2], list(self.name_color_map[name])[0][3]]
            for c, name in zip(colors, self.name_color_map.keys())
        ]
        for name, color in zip(self.name_color_map.keys(), colors):
            self.name_color_map[name] = {tuple(color)}
        for p, c in zip(self.pickers, colors):
            p.set_color(c)
        for func in self._on_change_callbacks:
            func(
                list(self.name_color_map.keys()),
                [(c[0] / 255, c[1] / 255, c[2] / 255, c[3]) for c in colors],
            )

    def change_color(self, name, color):
        c = tuple(vi for vi in color[5:-1].split(","))
        color = (int(c[0]) / 255, int(c[1]) / 255, int(c[2]) / 255, float(c[3]))
        self.name_color_map[name] = {color}
        for func in self._on_change_callbacks:
            func([name], [color])
