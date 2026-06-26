"""Reusable property-panel widgets in the designer's visual language.

These are plain ngapp components (Div-based) so they bind directly to the
component's Observables and update the WebGPU scene the same way the old Quasar
checkboxes did — they are drop-in replacements with the designer look.
"""

from ngapp.components import *

from . import cerbsim_style as cb


class Section(Div):
    """Collapsible property section: banded header + colored icon box + body.

    Two modes:
      * normal     — a caret toggles the body open/closed.
      * switchable — a header switch reflects an Observable; the body (details)
                     is shown only while the feature is on, and the icon box is
                     muted while off.

    Subclasses set a ``section_key`` class attribute (used for the icon-box
    accent color and for exclude-by-key filtering).
    """

    section_key = "display"

    def __init__(self, *body, icon, title, opened=False,
                 switchable=False, observable=None, info=None, head_actions=None):
        self._switchable = switchable
        self._obs = observable

        self._ico = Div(QIcon(ui_name=icon), ui_class=cb.psec_ico)
        main = []
        if not switchable:
            main.append(Div(QIcon(ui_name="mdi-chevron-down"), ui_class=cb.psec_caret))
        main.append(self._ico)
        main.append(Div(title, ui_class=cb.psec_title))
        if info:
            main.append(Div(
                QIcon(ui_name="mdi-information-outline"), QTooltip(info),
                ui_class=cb.htip,
            ))
        if switchable:
            self._switch = Div(ui_class=cb.prop_switch)
            main.append(self._switch)

        # Only the main area toggles the section; header actions handle their own
        # clicks (and live to the right of the title).
        self._head_main = Div(*main, ui_class=cb.psec_head_main)
        self._head_main.on("click", lambda e=None: self._on_head_click())
        head_children = [self._head_main]
        if head_actions:
            head_children.append(Div(*head_actions, ui_class=cb.psec_head_actions))
        self._head = Div(*head_children, ui_class=cb.psec_head)
        self._body = Div(*body, ui_class=cb.psec_body)

        super().__init__(self._head, self._body, ui_class=cb.psec)

        if switchable and observable is not None:
            self._open = bool(observable.value)
            observable.on_change(lambda v, _o: self._set_open(bool(v)))
        else:
            self._open = opened
        self._render()

    def _on_head_click(self):
        if self._switchable and self._obs is not None:
            self._obs.value = not self._obs.value  # → on_change → _set_open
        else:
            self._set_open(not self._open)

    def _set_open(self, val):
        self._open = val
        self._render()

    def _render(self):
        muted = self._switchable and not self._open
        self._ico.ui_style = cb.sico_style(self.section_key, muted=muted)
        head_cls = str(cb.psec_head) + (" cb-open" if self._open else " cb-collapsed")
        if self._switchable:
            head_cls += " cb-switchable"
        self._head.ui_class = head_cls
        if self._switchable:
            self._switch.ui_class = str(cb.prop_switch) + (
                " " + str(cb.prop_switch_on) if self._open else "")
        self._body.ui_hidden = not self._open


class Chip(Div):
    """Toggleable option chip (icon + label) bound to an Observable."""

    def __init__(self, label, icon=None, observable=None, small=False):
        self._obs = observable
        self._small = small
        children = []
        if icon:
            children.append(QIcon(ui_name=icon))
        children.append(label)
        super().__init__(*children, ui_class=self._cls(self._on()))
        self.on("click", lambda e=None: self._toggle())
        if observable is not None:
            observable.on_change(lambda v, _o: setattr(self, "ui_class", self._cls(bool(v))))

    def _on(self):
        return bool(self._obs.value) if self._obs is not None else False

    def _cls(self, on):
        c = str(cb.opt_chip)
        if self._small:
            c += " " + str(cb.opt_chip_sm)
        if on:
            c += " " + str(cb.opt_chip_on)
        return c

    def _toggle(self):
        if self._obs is not None:
            self._obs.value = not self._obs.value


def chip_row(*chips):
    """Wrap chips in the flex-wrap chip container."""
    return Div(*chips, ui_class=cb.opt_chips)


class Toggle(Div):
    """A label with a switch on the right, bound to an Observable."""

    def __init__(self, label, observable):
        self._obs = observable
        self._switch = Div(ui_class=self._scls(bool(observable.value)))
        self._switch.on("click", lambda e=None: self._toggle())
        super().__init__(Div(label), self._switch, ui_class=cb.prop_toggle)
        observable.on_change(lambda v, _o: setattr(self._switch, "ui_class", self._scls(bool(v))))

    def _scls(self, on):
        return str(cb.prop_switch) + (" " + str(cb.prop_switch_on) if on else "")

    def _toggle(self):
        self._obs.value = not self._obs.value


class SubToggleBlock(Div):
    """A flow sub-feature inside the grouped flow card: a label+switch header
    whose settings body is shown only while the feature is enabled.

    Collapsing the body when off keeps the grouped block compact (matching the
    switchable-section behaviour used elsewhere in the panel)."""

    def __init__(self, label, observable, *body):
        self._obs = observable
        self._toggle = Toggle(label, observable)
        self._body = Div(*body, ui_class=cb.flow_sub_body)
        self._body.ui_hidden = not bool(observable.value)
        super().__init__(self._toggle, self._body, ui_class=cb.flow_sub)
        observable.on_change(
            lambda v, _o: setattr(self._body, "ui_hidden", not bool(v))
        )


class PickPill(Div):
    """A small round pill (e.g. S / F / E / V) bound to an Observable."""

    def __init__(self, label, observable, tooltip=None):
        self._obs = observable
        children = [label]
        if tooltip:
            children.append(QTooltip(tooltip))
        super().__init__(*children, ui_class=self._cls(bool(observable.value)))
        self.on("click", lambda e=None: self._toggle())
        observable.on_change(lambda v, _o: setattr(self, "ui_class", self._cls(bool(v))))

    def _cls(self, on):
        return str(cb.chk_pill) + (" " + str(cb.chk_pill_on) if on else "")

    def _toggle(self):
        self._obs.value = not self._obs.value


def field(label, control):
    """Uppercase micro-label stacked above a control."""
    return Div(Div(label, ui_class=cb.prop_flab), control, ui_class=cb.prop_field)


class ColorbarLegend(Div):
    """In-viewport colorbar legend (top-right corner). Shows the quantity, a
    vertical gradient and ticks; clicking it opens a popover to pick the
    colormap, edit min/max, toggle autoscale, and (vectors) choose the shown
    component. This replaces the side-panel field summary."""

    CMAPS = ["rainbow", "turbo", "viridis", "plasma", "cet_l20",
             "matlab:jet", "matplotlib:coolwarm"]

    def __init__(self, comp):
        self._comp = comp
        # -- title (quantity) + component selector (|u| / ux / uy / uz) --
        self._quantity = Div(comp.title, ui_class=cb.legend_quantity)
        self._norm_pill = None
        self._comp_select = None
        selector = self._build_component_selector(comp)
        title_children = [self._quantity]
        if selector is not None:
            title_children.append(selector)
        title_row = Div(*title_children, ui_class=cb.legend_title)

        # -- gradient bar (click → colormap picker) + editable max/min ticks --
        # Inputs are not bound to the observable: driven by _refresh, committed on change.
        self.maxval = QInput(ui_type="number", ui_dense=True, ui_borderless=True)
        self.minval = QInput(ui_type="number", ui_dense=True, ui_borderless=True)
        self.maxval.on_change(self._set_max)
        self.minval.on_change(self._set_min)
        self._t75, self._t50, self._t25 = Div(""), Div(""), Div("")
        self._bar = Div(QTooltip("Colormap options"), ui_class=cb.legend_bar)
        self._bar.on("click", lambda e=None: self._toggle_pop())
        ticks = Div(self.maxval, self._t75, self._t50, self._t25, self.minval,
                    ui_class=cb.legend_ticks)
        wrap = Div(self._bar, ticks, ui_class=cb.legend_wrap)

        # -- autoscale pill --
        self._auto_icon = QIcon(ui_name=self._lock(comp.colormap_autoscale.value))
        self._auto = Div(self._auto_icon, "Auto",
                         ui_class=self._auto_cls(comp.colormap_autoscale.value))
        self._auto.on("click", lambda e=None: setattr(
            comp.colormap_autoscale, "value", not comp.colormap_autoscale.value))
        auto_row = Div(self._auto, ui_class="row q-mt-sm")

        # -- advanced popover (colormap / discrete / ncolors / showing) --
        self._pop = self._build_pop(comp)
        self._pop.ui_hidden = True

        super().__init__(title_row, wrap, auto_row, self._pop, ui_class=cb.vp_legend)

        comp.colormap_autoscale.on_change(self._render_auto)
        for obs in ("colormap_name", "colormap_min", "colormap_max"):
            getattr(comp, obs).on_change(lambda v, _o: self._refresh())
        self.on_mounted(self._refresh)

    # -- autoscale pill --
    @staticmethod
    def _lock(on):
        return "mdi-lock" if on else "mdi-lock-open-variant"

    def _auto_cls(self, on):
        return str(cb.ps_auto) + (" " + str(cb.ps_auto_on) if on else "")

    def _render_auto(self, v, _o):
        self._auto.ui_class = self._auto_cls(bool(v))
        self._auto_icon.ui_name = self._lock(bool(v))
        self._refresh()

    # -- advanced popover --------------------------------------------------
    def _build_pop(self, comp):
        rows = [Div(Div("Colormap options", ui_class=cb.ps_lab),
                    _close_x(lambda: self._toggle_pop(False)),
                    ui_class="row items-center justify-between")]

        self._opts = {}
        opt_rows = []
        for name in self.CMAPS:
            row = Div(
                Div(ui_class=cb.cmap_swatch, ui_style="background: " + cb.colormap_gradient(name) + ";"),
                Div(name, ui_class=cb.cmap_opt_name),
                QIcon(ui_name="mdi-check"),
                ui_class=self._opt_cls(name == comp.colormap_name.value),
            )
            row.on("click", lambda e=None, n=name: setattr(comp.colormap_name, "value", n))
            self._opts[name] = row
            opt_rows.append(row)
        rows.append(field("Colormap", Div(*opt_rows)))

        self._discrete = Chip("Discrete", "mdi-grid", comp.colormap_discrete, small=True)
        self._ncolors = QInput(ui_type="number", ui_model_value=comp.ncolors_colormap,
                               ui_dense=True, ui_filled=True, ui_class=cb.input_tiny)
        self._ncolors.on_change(self._set_ncolors)
        rows.append(Div(self._discrete, field("N colors", self._ncolors),
                        ui_class="row items-end " + str(cb.gap_sm)))
        return Div(*rows, ui_class=cb.legend_pop)

    def _opt_cls(self, on):
        return str(cb.cmap_opt) + (" " + str(cb.cmap_opt_on) if on else "")

    def _toggle_pop(self, show=None):
        self._pop.ui_hidden = (not self._pop.ui_hidden) if show is None else (not show)

    def _set_ncolors(self, event):
        try:
            n = max(1, min(32, self._comp.ncolors_colormap.value))
            self._comp.colormap.set_n_colors(n)
            self._comp.wgpu.scene.render()
        except (ValueError, TypeError):
            pass

    # -- component selector (next to the legend title) --------------------
    def _build_component_selector(self, comp):
        """Build the |u| / component picker shown beside the legend title.

        Scalar fields get nothing. Fields with up to 3 components get an inline
        segmented control (|u| ux uy uz). Fields with more than 3 components get
        a |u| pill plus a dropdown to pick the component (keeps the legend narrow)."""
        dim = getattr(comp.cf, "dim", 1)
        if dim <= 1:
            return None
        if dim <= 3:
            names = ["x", "y", "z"][:dim]
            opts = [("norm", "|u|")] + [(str(i), names[i]) for i in range(dim)]
            return Div(Segmented(opts, "norm", self._set_component), ui_class=cb.legend_comp)
        # >3 components: |u| pill + dropdown (1..dim).
        self._norm_pill = Div("|u|", ui_class=self._norm_cls(True))
        self._norm_pill.on("click", lambda e=None: self._select_component("norm"))
        self._comp_select = QSelect(
            QTooltip("Component"),
            ui_options=[str(i + 1) for i in range(dim)],
            ui_dense=True, ui_borderless=True,
            ui_class=cb.legend_comp_select,
        )
        self._comp_select.on_update_model_value(
            lambda e=None: self._select_component(str(int(self._comp_select.ui_model_value) - 1)))
        return Div(self._norm_pill, self._comp_select, ui_class=cb.legend_comp)

    def _norm_cls(self, on):
        return str(cb.legend_pill) + (" " + str(cb.seg_btn_on) if on else "")

    def _select_component(self, val):
        """Combined handler for the >3-component pill+dropdown selector."""
        is_norm = val == "norm"
        if self._norm_pill is not None:
            self._norm_pill.ui_class = self._norm_cls(is_norm)
        if self._comp_select is not None and is_norm:
            self._comp_select.ui_model_value = None
        self._set_component(val)

    def _set_component(self, val):
        comp = self._comp
        idx = -1 if val == "norm" else int(val)
        try:
            if comp.elements2d is not None:
                comp.elements2d.set_component(idx)
            if comp.clippingcf is not None:
                comp.clippingcf.set_component(idx)
            comp.colorbar.set_needs_update()
            comp.wgpu.scene.render()
        except Exception:
            pass

    def _set_min(self, event):
        try:
            v = float(event.value)
            self._comp.colormap.set_min(v)
            self._comp.colormap_autoscale.value = False
            self._comp.colormap_min.value = v
            self._comp.wgpu.scene.render()
        except (ValueError, TypeError):
            pass

    def _set_max(self, event):
        try:
            v = float(event.value)
            self._comp.colormap.set_max(v)
            self._comp.colormap_autoscale.value = False
            self._comp.colormap_max.value = v
            self._comp.wgpu.scene.render()
        except (ValueError, TypeError):
            pass

    # -- visual refresh ----------------------------------------------------
    def _range(self):
        cmap = getattr(self._comp, "colormap", None)
        if cmap is not None:
            try:
                return float(cmap.minval), float(cmap.maxval)
            except Exception:
                pass
        try:
            return float(self._comp.colormap_min.value), float(self._comp.colormap_max.value)
        except Exception:
            return 0.0, 1.0

    def _refresh(self):
        name = self._comp.colormap_name.value
        self._quantity.ui_children = [self._comp.title]
        self._bar.ui_style = "background: " + cb.colormap_gradient_vertical(name) + ";"
        mn, mx = self._range()
        # editable end values + read-only middle ticks
        self.maxval.ui_model_value = self._fmt(mx)
        self.minval.ui_model_value = self._fmt(mn)
        self._t75.ui_children = [self._fmt(mn + 0.75 * (mx - mn))]
        self._t50.ui_children = [self._fmt(mn + 0.5 * (mx - mn))]
        self._t25.ui_children = [self._fmt(mn + 0.25 * (mx - mn))]
        for n, r in getattr(self, "_opts", {}).items():
            r.ui_class = self._opt_cls(n == name)

    @staticmethod
    def _fmt(v):
        return f"{v:.3g}"


def _close_x(callback):
    x = Div(QIcon(ui_name="mdi-close"), ui_class=cb.probe_del)
    x.on("click", lambda e=None: callback())
    return x


class ColormapBar(Div):
    """The active-colormap gradient swatch. Click it to open a picker dropdown
    with the colormap list plus discrete / N-colors controls."""

    CMAPS = ["rainbow", "turbo", "viridis", "plasma", "cet_l20",
             "matlab:jet", "matplotlib:coolwarm"]

    def __init__(self, comp):
        self._comp = comp
        self._bar = Div(ui_class=cb.cmap_bar)
        self._bar.ui_style = "background: " + cb.colormap_gradient(comp.colormap_name.value) + ";"

        self._opts = {}
        rows = []
        for name in self.CMAPS:
            row = Div(
                Div(ui_class=cb.cmap_swatch, ui_style="background: " + cb.colormap_gradient(name) + ";"),
                Div(name, ui_class=cb.cmap_opt_name),
                QIcon(ui_name="mdi-check"),
                ui_class=self._opt_cls(name == comp.colormap_name.value),
            )
            row.on("click", lambda e=None, n=name: setattr(comp.colormap_name, "value", n))
            self._opts[name] = row
            rows.append(row)

        self._discrete = Chip("Discrete", "mdi-grid", comp.colormap_discrete, small=True)
        self._ncolors = QInput(ui_type="number", ui_model_value=comp.ncolors_colormap,
                               ui_dense=True, ui_filled=True, ui_class=cb.input_tiny)
        self._ncolors.on_change(self._set_ncolors)
        footer = Div(self._discrete, field("N colors", self._ncolors),
                     ui_class="row items-end " + str(cb.gap_sm),
                     ui_style="padding: 8px 8px 2px;")

        menu = QMenu(
            Div(*rows, QSeparator(), footer, ui_class=cb.cmap_menu),
            ui_anchor="bottom left", ui_self="top left",
        )
        # Nest the menu in the bar so the bar is the click anchor.
        self._bar.ui_children = [menu]
        super().__init__(self._bar)
        comp.colormap_name.on_change(self._on_name)

    def _opt_cls(self, on):
        return str(cb.cmap_opt) + (" " + str(cb.cmap_opt_on) if on else "")

    def _on_name(self, v, _o):
        self._bar.ui_style = "background: " + cb.colormap_gradient(v) + ";"
        for n, r in self._opts.items():
            r.ui_class = self._opt_cls(n == v)

    def _set_ncolors(self, event):
        try:
            ncolors = max(1, min(32, self._comp.ncolors_colormap.value))
            self._comp.colormap.set_n_colors(ncolors)
            self._comp.wgpu.scene.render()
        except (ValueError, TypeError):
            pass


class MoreDisclosure(Div):
    """Inline 'More options' / 'Fewer options' disclosure that shows extra body."""

    def __init__(self, *body, label_more="More options", label_less="Fewer options"):
        self._more = label_more
        self._less = label_less
        self._open = False
        self._caret = QIcon(ui_name="mdi-chevron-down")
        self._label = Div(self._more)
        self._toggle = Div(self._caret, self._label, ui_class=self._tcls())
        self._toggle.on("click", lambda e=None: self._flip())
        self._body = Div(*body, ui_class=cb.psec_body + " q-pa-none")
        self._body.ui_style = "padding: 0; gap: 11px;"
        self._body.ui_hidden = True
        super().__init__(self._body, self._toggle, ui_class="column " + str(cb.gap_sm))

    def _tcls(self):
        return str(cb.psec_more) + ("" if self._open else " cb-collapsed")

    def _flip(self):
        self._open = not self._open
        self._toggle.ui_class = self._tcls()
        self._label.ui_children = [self._less if self._open else self._more]
        self._body.ui_hidden = not self._open


class Segmented(Div):
    """A segmented button group. ``options`` is a list of (value, label)."""

    def __init__(self, options, value, on_change=None):
        self._value = value
        self._on_change = on_change
        self._btns = {}
        children = []
        for val, lab in options:
            b = Div(lab, ui_class=self._cls(val == value))
            b.on("click", lambda e=None, v=val: self._select(v))
            self._btns[val] = b
            children.append(b)
        super().__init__(*children, ui_class=cb.seg)

    def _cls(self, on):
        return str(cb.seg_btn) + (" " + str(cb.seg_btn_on) if on else "")

    def _select(self, val):
        self._value = val
        for v, b in self._btns.items():
            b.ui_class = self._cls(v == val)
        if self._on_change:
            self._on_change(val)


class FieldSummary(Div):
    """Always-visible function summary: 'Showing' selector, the colorbar legend
    (click to pick a colormap), and autoscale + min/max. Replaces the old
    Colormap section."""

    def __init__(self, comp):
        self.comp = comp
        rows = []

        # Showing — component selector for vectors, quantity text for scalars.
        if comp.cf.dim > 1:
            comp_names = ["x", "y", "z"] if comp.cf.dim <= 3 else [str(i + 1) for i in range(comp.cf.dim)]
            opts = [("norm", "|u|")] + [(str(i), f"u_{comp_names[i]}") for i in range(comp.cf.dim)]
            showing = Segmented(opts, "norm", self._set_component)
            rows.append(Div(Div("Showing", ui_class=cb.ps_lab),
                            Div(showing, ui_class=cb.grow), ui_class=cb.ps_row))
        else:
            rows.append(Div(Div("Showing", ui_class=cb.ps_lab),
                            Div(comp.title, ui_class=cb.ps_q), ui_class=cb.ps_row))

        # Colorbar legend bar (click → colormap picker) + range row (min — Auto — max).
        self.bar = ColormapBar(comp)
        self.minval = QInput(ui_type="number", ui_dense=True, ui_filled=True,
                             ui_model_value=comp.colormap_min)
        self.maxval = QInput(ui_type="number", ui_dense=True, ui_filled=True,
                             ui_model_value=comp.colormap_max)
        self.minval.on_change(self._set_min)
        self.maxval.on_change(self._set_max)
        self._auto_icon = QIcon(ui_name=self._lock_icon(comp.colormap_autoscale.value))
        self._auto = Div(self._auto_icon, "Auto",
                         ui_class=self._auto_cls(comp.colormap_autoscale.value))
        self._auto.on("click", lambda e=None: setattr(
            comp.colormap_autoscale, "value", not comp.colormap_autoscale.value))
        comp.colormap_autoscale.on_change(self._render_auto)
        scale = Div(self.minval, self._auto, self.maxval, ui_class=cb.ps_scale)
        rows.append(Div(self.bar, scale, ui_class="column " + str(cb.gap_sm)))

        super().__init__(*rows, ui_class=cb.prop_summary)
        self.on_mounted(self._update)

    # -- helpers --
    def _lock_icon(self, on):
        return "mdi-lock" if on else "mdi-lock-open-variant"

    def _auto_cls(self, on):
        return str(cb.ps_auto) + (" " + str(cb.ps_auto_on) if on else "")

    def _render_auto(self, v, _o):
        self._auto.ui_class = self._auto_cls(bool(v))
        self._auto_icon.ui_name = self._lock_icon(bool(v))

    def _set_component(self, val):
        comp = self.comp
        idx = -1 if val == "norm" else int(val)
        try:
            if comp.elements2d is not None:
                comp.elements2d.set_component(idx)
            if comp.clippingcf is not None:
                comp.clippingcf.set_component(idx)
            comp.colorbar.set_needs_update()
            comp.wgpu.scene.render()
        except Exception:
            pass

    def _set_min(self, event):
        try:
            val = float(event.value)
            self.comp.colormap.set_min(val)
            self.comp.colormap_autoscale.value = False
            self.comp.colormap_min.value = val
            self.comp.wgpu.scene.render()
            self.minval.ui_model_value = self.comp.colormap_min.display_value
        except (ValueError, TypeError):
            pass

    def _set_max(self, event):
        try:
            val = float(event.value)
            self.comp.colormap.set_max(val)
            self.comp.colormap_autoscale.value = False
            self.comp.colormap_max.value = val
            self.comp.wgpu.scene.render()
            self.maxval.ui_model_value = self.comp.colormap_max.display_value
        except (ValueError, TypeError):
            pass

    def _update(self):
        self.comp.colormap_autoscale.value = self.comp.colormap.autoscale
        self.comp.colormap_discrete.value = bool(self.comp.colormap.discrete)
        self.minval.ui_model_value = self.comp.colormap_min.display_value
        self.maxval.ui_model_value = self.comp.colormap_max.display_value
