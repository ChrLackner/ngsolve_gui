"""Regions section — per-region draw visibility for function scenes.

Volume regions (materials) get plain visibility checkboxes; surfaces follow
automatically through the mesh adjacency (an interface stays visible while
either adjacent volume region is visible — see ``region_state.RegionState``).
Per-boundary overrides live behind a "Boundaries" disclosure: each boundary
cycles auto → hidden → shown, and its label dims when it is currently not
drawn (whether by override or derivation).
"""

from ngapp.components import *

from ..prop_widgets import Section, MoreDisclosure
from .. import cerbsim_style as cb
from ..cerbsim_style import field_label, region_item_row


class RegionsSection(Section):
    section_key = "regions"

    def __init__(self, comp):
        self.comp = comp
        st = comp.region_state
        mats = st.unique_materials
        bnds = st.unique_boundaries if comp.mesh.dim == 3 else []
        if len(mats) <= 1 and len(bnds) <= 1:
            raise ValueError("no regions to manage")

        self._updating = False
        self._mat_cbs = {}
        self._mat_rows = {}
        self._bnd_state_btns = {}
        self._bnd_labels = {}

        rows = []
        if len(mats) + len(bnds) > 10:
            filt = QInput(
                ui_label="Filter...", ui_dense=True, ui_clearable=True,
                ui_debounce=300, ui_class="q-mb-xs",
            )
            filt.on_update_model_value(self._on_filter)
            rows.append(filt)

        rows += [self._make_mat_row(name) for name in mats]

        self._bnd_rows = {}
        if bnds:
            hint = Div(
                "auto: drawn while an adjacent volume region is visible",
                ui_class=field_label,
            )
            body = [hint] + [self._make_bnd_row(name) for name in bnds]
            rows.append(MoreDisclosure(
                *body, label_more="Boundaries", label_less="Boundaries"))

        show_all = QBtn(
            QTooltip("Show all regions"),
            ui_icon="mdi-eye-refresh-outline", ui_flat=True, ui_dense=True,
            ui_round=True, ui_size="sm",
        )
        show_all.on_click(lambda e=None: comp.show_all_regions())

        super().__init__(
            *rows, icon="mdi-layers-outline", title="Regions",
            opened=bool(st.any_hidden()), head_actions=[show_all],
        )

        # Reflect programmatic changes (keybindings, undo, show-all).
        comp.hidden_regions.on_change(self._sync_from_state)
        comp.boundary_overrides.on_change(self._sync_from_state)

    # -- rows --------------------------------------------------------------

    def _make_mat_row(self, name):
        st = self.comp.region_state
        vis = QCheckbox(ui_model_value=st.material_visible(name), ui_dense=True)
        vis.on_update_model_value(
            lambda e, n=name: self._on_mat_toggle(n, e.value))
        self._mat_cbs[name] = vis
        row = Div(
            Div(vis, ui_class="col-auto"),
            Div(Label(name), ui_class="col " + field_label + " ellipsis"),
            ui_class="row items-center no-wrap " + region_item_row,
        )
        self._mat_rows[name] = row
        return row

    _BND_CYCLE = {None: False, False: True, True: None}
    _BND_TEXT = {None: "auto", False: "off", True: "on"}

    def _make_bnd_row(self, name):
        st = self.comp.region_state
        state = st.overrides.get(name)
        btn = QBtn(
            QTooltip("Cycle auto / off / on"),
            ui_label=self._BND_TEXT[state], ui_flat=True, ui_dense=True,
            ui_size="sm", ui_no_caps=True,
        )
        btn.on_click(lambda e=None, n=name: self._on_bnd_cycle(n))
        self._bnd_state_btns[name] = btn
        label = Label(name)
        self._bnd_labels[name] = label
        row = Div(
            Div(btn, ui_class="col-auto"),
            Div(label, ui_class="col " + field_label + " ellipsis"),
            ui_class="row items-center no-wrap " + region_item_row,
        )
        self._bnd_rows[name] = row
        self._style_bnd(name)
        return row

    # -- handlers ----------------------------------------------------------

    def _on_mat_toggle(self, name, visible):
        if self._updating:
            return
        self.comp.set_region_visible(name, bool(visible))

    def _on_bnd_cycle(self, name):
        if self._updating:
            return
        current = self.comp.region_state.overrides.get(name)
        self.comp.set_boundary_override(name, self._BND_CYCLE[current])

    def _on_filter(self, event):
        text = (event.value or "").lower().strip()
        for name, row in {**self._mat_rows, **self._bnd_rows}.items():
            row.ui_hidden = bool(text) and text not in name.lower()

    # -- sync --------------------------------------------------------------

    def _style_bnd(self, name):
        st = self.comp.region_state
        effective = st.boundary_effective(name)
        self._bnd_labels[name].ui_style = (
            "" if effective else "opacity: 0.45;")
        self._bnd_state_btns[name].ui_label = self._BND_TEXT[
            st.overrides.get(name)]

    def _sync_from_state(self, *_):
        st = self.comp.region_state
        self._updating = True
        try:
            for name, cbx in self._mat_cbs.items():
                cbx.ui_model_value = st.material_visible(name)
            for name in self._bnd_state_btns:
                self._style_bnd(name)
        finally:
            self._updating = False
