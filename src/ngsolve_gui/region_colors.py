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
    colors = [[c[0] / 255, c[1] / 255, c[2] / 255, 1] for c in colors]
    return colors[:n]


# ── color helpers ─────────────────────────────────────────────────


def _rgba_str(r, g, b, a):
    """(r,g,b,a) in [0,1] → CSS rgba() string."""
    return f"rgba({int(r * 255)},{int(g * 255)},{int(b * 255)},{a})"


def _parse_rgba(s):
    """CSS rgba() string → (r,g,b,a) in [0,1]."""
    parts = s[5:-1].split(",")
    return (int(parts[0]) / 255, int(parts[1]) / 255, int(parts[2]) / 255, float(parts[3]))


def _hex_str(r, g, b):
    """(r,g,b) in [0,1] → #rrggbb."""
    return f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"


# ── color swatch button ──────────────────────────────────────────

_SWATCH = (
    "min-width:22px; max-width:22px; min-height:22px; max-height:22px;"
    "border-radius:4px; border:1px solid rgba(0,0,0,0.15); padding:0;"
)


class ColorpickerButton(QBtn):
    """Small color swatch that opens a picker popup.

    All colors are stored and exchanged as ``(r, g, b, a)`` in **[0, 1]**.
    """

    def __init__(self, color=None, **kwargs):
        if color is None:
            color = (0.5, 0.5, 0.5, 1.0)
        self._color = tuple(color[:4])
        self.picker = QColor(
            ui_format_model="rgba",
            ui_model_value=_rgba_str(*self._color),
            ui_default_view="palette",
        )
        self.picker.on_update_model_value(self._on_pick)
        super().__init__(
            QMenu(self.picker), ui_size="sm", ui_style=self._style(), **kwargs
        )

    def _style(self):
        r, g, b, _ = self._color
        return f"background-color:{_hex_str(r, g, b)};{_SWATCH}"

    @property
    def color(self):
        """Current color as (r, g, b, a) in [0, 1]."""
        return self._color

    def set_color(self, rgba):
        """Set color from (r, g, b, a) in [0, 1]."""
        self._color = tuple(rgba[:4])
        self.ui_style = self._style()
        self.picker.ui_model_value = _rgba_str(*self._color)

    def _on_pick(self, event):
        self._color = _parse_rgba(event.value)
        self.ui_style = self._style()

    def on_change(self, func):
        """Register *func(event)*.  Use ``_parse_rgba(event.value)`` to decode."""
        self.picker.on_update_model_value(func)


# ── region color editor ──────────────────────────────────────────


class RegionColors(Div):
    """Color editor with automatic tree-grouping by underscore prefix.

    All colors are ``(r, g, b, a)`` tuples in **[0, 1]** range, both
    internally and in callbacks.
    """

    def __init__(
        self, title, colors: list[tuple[float, float, float, float]], names: list[str]
    ):
        # Deduplicate: keep first colour per unique name
        self._colors: dict[str, tuple] = {}
        for name, color in zip(names, colors):
            if name not in self._colors:
                self._colors[name] = tuple(color[:4])
        self._title = title

        # Widget registries (filled by _build)
        self._pickers: dict[str, ColorpickerButton] = {}
        self._vis_cbs: dict[str, QCheckbox] = {}
        self._group_members: dict[str, list[str]] = {}
        self._group_bodies: dict[str, Div] = {}
        self._group_icons: dict[str, QIcon] = {}
        self._group_rows: dict[str, Div] = {}
        self._group_pickers: dict[str, ColorpickerButton] = {}
        self._group_expanded: dict[str, bool] = {}
        self._item_rows: dict[str, Div] = {}

        self._color_cbs: list = []
        self._updating = False

        super().__init__()
        self._build()

    # ── grouping ──────────────────────────────────────────────────

    @staticmethod
    def _build_groups(names):
        groups: dict[str | None, list[str]] = {}
        for name in sorted(names):
            parts = name.split("_", 1)
            key = parts[0] if len(parts) > 1 else None
            groups.setdefault(key, []).append(name)
        # fold single-member groups into ungrouped
        ungrouped = groups.pop(None, [])
        for k in [k for k, v in groups.items() if len(v) == 1]:
            ungrouped.extend(groups.pop(k))
        if ungrouped:
            groups[None] = sorted(ungrouped)
        return groups

    # ── item row ──────────────────────────────────────────────────

    def _make_item_row(self, name):
        color = self._colors[name]
        picker = ColorpickerButton(color=color)
        self._pickers[name] = picker
        picker.on_change(lambda e, n=name: self._on_item_color(n, e.value))

        vis = QCheckbox(ui_model_value=True)
        self._vis_cbs[name] = vis
        vis.on_update_model_value(lambda e, n=name: self._on_item_vis(n, e.value))

        return Div(
            Div(vis, ui_class="col-auto"),
            Div(picker, ui_class="col-auto", ui_style="padding: 0 4px;"),
            Div(
                Label(name),
                ui_class="col",
                ui_style=(
                    "font-size:0.8rem; white-space:nowrap;"
                    "overflow:hidden; text-overflow:ellipsis;"
                ),
            ),
            ui_class="row items-center no-wrap",
            ui_style="padding:2px 4px 2px 20px; min-height:30px;",
        )

    # ── group ─────────────────────────────────────────────────────

    def _make_group(self, key, members):
        self._group_members[key] = members
        self._group_expanded[key] = False

        # group-level controls
        gpicker = ColorpickerButton()
        self._group_pickers[key] = gpicker
        gpicker.on_change(lambda e, k=key: self._on_group_color(k, e.value))

        gvis = QCheckbox(ui_model_value=True)
        gvis.on_update_model_value(lambda e, k=key: self._on_group_vis(k, e.value))

        grand = QBtn(
            ui_icon="mdi-dice-multiple", ui_flat=True, ui_dense=True,
            ui_size="xs", ui_color="accent", ui_round=True,
        )
        grand.on_click(lambda e, k=key: self._randomize_group(k))

        icon = QIcon(ui_name="mdi-chevron-right", ui_size="xs")
        self._group_icons[key] = icon

        # the clickable label area toggles expand/collapse
        toggle = QItem(
            Div(icon, ui_class="col-auto", ui_style="margin-right:2px;"),
            Div(
                Label(f"{key}"),
                ui_class="col-auto",
                ui_style="font-size:0.82rem; font-weight:600;",
            ),
            Div(
                Label(f"({len(members)})"),
                ui_class="col-auto",
                ui_style="font-size:0.72rem; color:#999; padding-left:4px;",
            ),
            ui_clickable=True,
            ui_dense=True,
            ui_style="padding:0; min-height:unset; user-select:none; flex:1;",
            ui_class="row items-center no-wrap",
        )
        toggle.on_click(lambda e, k=key: self._toggle(k))

        header = Div(
            Div(gvis, ui_class="col-auto"),
            Div(gpicker, ui_class="col-auto", ui_style="padding:0 6px;"),
            toggle,
            Div(grand, ui_class="col-auto"),
            ui_class="row items-center no-wrap",
            ui_style=(
                "padding:3px 6px; border-radius:6px;"
                "background:linear-gradient(135deg, rgba(0,0,0,0.025), rgba(0,0,0,0.05));"
                "transition: background 0.15s;"
            ),
        )

        body = Div(
            *[self._make_item_row(n) for n in members],
            ui_style="display:none; padding:2px 0 2px 0; border-left:2px solid rgba(0,0,0,0.06); margin-left:14px;",
        )
        self._group_bodies[key] = body

        group_div = Div(header, body, ui_style="margin-bottom:3px;")
        self._group_rows[key] = group_div
        return group_div

    def _toggle(self, key):
        body = self._group_bodies[key]
        icon = self._group_icons[key]
        expanded = self._group_expanded[key]
        if expanded:
            body.ui_style = "display:none; padding:2px 0 2px 0; border-left:2px solid rgba(0,0,0,0.06); margin-left:14px;"
            icon.ui_name = "mdi-chevron-right"
        else:
            body.ui_style = "padding:2px 0 2px 0; border-left:2px solid rgba(0,0,0,0.06); margin-left:14px;"
            icon.ui_name = "mdi-chevron-down"
        self._group_expanded[key] = not expanded

    # ── build ─────────────────────────────────────────────────────

    def _build(self):
        rows = []

        # title row
        randomize = QBtn(
            "Randomize",
            ui_icon="mdi-dice-multiple",
            ui_flat=True,
            ui_color="accent",
            ui_size="sm",
            ui_dense=True,
            ui_no_caps=True,
        )
        randomize.on_click(self._randomize)
        rows.append(
            Row(
                Div(Heading(self._title, 7), ui_class="col-auto"),
                Div(ui_class="col"),
                Div(randomize, ui_class="col-auto"),
            )
        )

        groups = self._build_groups(self._colors.keys())
        has_groups = any(k is not None for k in groups)

        if has_groups:
            if len(self._colors) > 10:
                filt = QInput(
                    ui_label="Filter...",
                    ui_dense=True,
                    ui_clearable=True,
                    ui_debounce=300,
                    ui_style="margin-bottom:6px;",
                )
                filt.on_update_model_value(self._on_filter)
                rows.append(filt)

            for key in sorted(k for k in groups if k is not None):
                rows.append(self._make_group(key, groups[key]))
            if None in groups:
                for name in groups[None]:
                    row = self._make_item_row(name)
                    self._item_rows[name] = row
                    rows.append(row)
        else:
            for name in sorted(self._colors.keys()):
                row = self._make_item_row(name)
                self._item_rows[name] = row
                rows.append(row)

        self.ui_children = rows

    # ── filter ────────────────────────────────────────────────────

    def _on_filter(self, event):
        text = (event.value or "").lower().strip()
        for key, widget in self._group_rows.items():
            members = self._group_members[key]
            hit = not text or text in key.lower() or any(text in m.lower() for m in members)
            widget.ui_style = "margin-bottom:3px;" if hit else "display:none;"
        for name, widget in self._item_rows.items():
            hit = not text or text in name.lower()
            widget.ui_style = "padding:2px 4px;" if hit else "display:none;"

    # ── public API ────────────────────────────────────────────────

    def on_change_color(self, func):
        """Register ``func(names: list[str], colors: list[tuple])``
        where each color is ``(r, g, b, a)`` in [0, 1]."""
        self._color_cbs.append(func)

    # ── notify ────────────────────────────────────────────────────

    def _notify(self, names, colors):
        for func in self._color_cbs:
            func(names, colors)

    # ── item handlers ─────────────────────────────────────────────

    def _on_item_color(self, name, rgba_str):
        if self._updating:
            return
        color = _parse_rgba(rgba_str)
        old = self._colors.get(name)
        if old == color:
            return
        self._colors[name] = color
        self._notify([name], [color])

    def _on_item_vis(self, name, visible):
        if self._updating:
            return
        r, g, b, old_a = self._colors[name]
        new_a = 1.0 if visible else 0.0
        if old_a == new_a:
            return
        color = (r, g, b, new_a)
        self._colors[name] = color
        self._notify([name], [color])

    # ── group handlers ────────────────────────────────────────────

    def _on_group_color(self, key, rgba_str):
        color = _parse_rgba(rgba_str)
        members = self._group_members[key]
        self._updating = True
        for name in members:
            self._colors[name] = color
            self._pickers[name].set_color(color)
        self._updating = False
        self._notify(members, [color] * len(members))

    def _on_group_vis(self, key, visible):
        members = self._group_members[key]
        new_a = 1.0 if visible else 0.0
        self._updating = True
        for name in members:
            r, g, b, _ = self._colors[name]
            self._colors[name] = (r, g, b, new_a)
            self._vis_cbs[name].ui_model_value = visible
        self._updating = False
        self._notify(members, [self._colors[n] for n in members])

    # ── randomize ─────────────────────────────────────────────────

    def _make_palette(self, n_needed):
        import random, math, itertools

        n = 2
        while n ** 3 - 2 < n_needed:
            n += 1
        vals = [int(255 * i / (n - 1)) for i in range(n)]
        palette = [
            (vals[cr], vals[cg], vals[cb])
            for cr, cg, cb in itertools.product(range(n), range(n), range(n))
        ][1:-1]
        random.shuffle(palette)
        return palette

    def _randomize_group(self, key):
        """Randomize individual colors within a single group."""
        members = self._group_members[key]
        palette = self._make_palette(len(members))
        self._updating = True
        new_colors = []
        for i, name in enumerate(members):
            c = palette[i % len(palette)]
            _, _, _, a = self._colors[name]
            color = (c[0] / 255, c[1] / 255, c[2] / 255, a)
            self._colors[name] = color
            new_colors.append(color)
            self._pickers[name].set_color(color)
        self._updating = False
        self._notify(members, new_colors)

    def _randomize(self):
        """Randomize colors respecting expand state.

        Collapsed groups get one color for all members.
        Expanded groups get individual colors per member.
        Ungrouped items get individual colors.
        """
        # Count how many distinct palette entries we need
        n_needed = len(self._item_rows)  # ungrouped items
        for key in self._group_members:
            if self._group_expanded.get(key):
                n_needed += len(self._group_members[key])
            else:
                n_needed += 1
        palette = self._make_palette(n_needed)

        self._updating = True
        all_names = []
        all_colors = []
        pi = 0
        for key, members in self._group_members.items():
            if self._group_expanded.get(key):
                for name in members:
                    c = palette[pi % len(palette)]
                    pi += 1
                    _, _, _, a = self._colors[name]
                    color = (c[0] / 255, c[1] / 255, c[2] / 255, a)
                    self._colors[name] = color
                    all_colors.append(color)
                    all_names.append(name)
                    self._pickers[name].set_color(color)
            else:
                c = palette[pi % len(palette)]
                pi += 1
                group_color = (c[0] / 255, c[1] / 255, c[2] / 255, 1.0)
                self._group_pickers[key].set_color(group_color)
                for name in members:
                    _, _, _, a = self._colors[name]
                    color = (c[0] / 255, c[1] / 255, c[2] / 255, a)
                    self._colors[name] = color
                    all_colors.append(color)
                    all_names.append(name)
                    self._pickers[name].set_color(color)
        for name in self._item_rows:
            c = palette[pi % len(palette)]
            pi += 1
            _, _, _, a = self._colors[name]
            color = (c[0] / 255, c[1] / 255, c[2] / 255, a)
            self._colors[name] = color
            all_colors.append(color)
            all_names.append(name)
            self._pickers[name].set_color(color)
        self._updating = False
        self._notify(all_names, all_colors)
