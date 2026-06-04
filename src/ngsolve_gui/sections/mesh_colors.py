import numpy as np
from ngapp.components import *
from ngsolve_gui.region_colors import RegionColors
from ..prop_widgets import Section, Segmented
from ..cerbsim_style import (
    gap_sm, grow, mono, hint, muted, prop_switch, prop_switch_on, qhist_col,
)


class MeshColorSection(Section):
    """Coloring / visibility, switchable between modes:
    ``By region`` keeps the grouped region colors; ``By quality`` isolates the
    worst elements by Jacobian condition number; ``By element type`` (3D only)
    toggles visibility per element type (boundary-layer prisms, closure pyramids)."""

    section_key = "colors"

    def __init__(self, comp):
        self.comp = comp
        self._boxes = {}
        self._boxes["region"] = self._build_region(comp)
        self._boxes["quality"] = self._build_quality(comp)

        options = [("region", "By region"), ("quality", "By quality")]
        if comp.mesh.dim == 3:
            self._boxes["eltype"] = self._build_eltype(comp)
            options.append(("eltype", "By element type"))

        for key, box in self._boxes.items():
            box.ui_hidden = key != "region"
        seg = Segmented(options, "region", self._set_mode)
        super().__init__(seg, *self._boxes.values(),
                         icon="mdi-palette", title="Coloring")

    def _set_mode(self, val):
        # The segment just chooses which controls are shown; the region (alpha),
        # element-type and quality filters compose and stay applied across modes.
        for key, box in self._boxes.items():
            box.ui_hidden = key != val
        if val in ("eltype", "quality") and self.comp.mesh.dim == 3:
            # show the volume mesh so volume-element filtering is visible
            self.comp.elements3d_visible.value = True

    # -- By region (grouped region colors) --------------------------------
    def _build_region(self, comp):
        colors = [(c[0], c[1], c[2], c[3]) for c in
                  (fd.color for fd in comp.mesh.ngmesh.FaceDescriptors())]
        names = [fd.bcname for fd in comp.mesh.ngmesh.FaceDescriptors()]
        face_colors = RegionColors("Face Colors", colors, names)
        face_colors.on_change_color(self.change_color)
        cards = [QCard(QCardSection(face_colors), ui_flat=True, ui_bordered=True)]

        edge_descriptors = list(comp.mesh.ngmesh.EdgeDescriptors())
        if edge_descriptors:
            enames = [ed.name for ed in edge_descriptors]
            saved = comp.edge_colors.value
            self.ecolors = {name: saved.get(name, [0, 0, 0, 255]) for name in set(enames)}
            ecolors = [
                (c[0] / 255, c[1] / 255, c[2] / 255, c[3] / 255 if c[3] > 1 else c[3])
                for c in [self.ecolors[name] for name in enames]
            ]
            edge_colors = RegionColors("Edge Colors", ecolors, enames)
            edge_colors.on_change_color(self.change_edge_color)
            cards.append(QCard(QCardSection(edge_colors), ui_flat=True, ui_bordered=True))

        if comp.mesh.dim == 3:
            dnames = list(set(comp.mesh.GetMaterials()))
            dcolors = [(1.0, 0.0, 0.0, 1.0) for _ in range(len(dnames))]
            domain_colors = RegionColors("Domain Colors", dcolors, dnames)
            self.dcolors = {name: [int(255 * ci) for ci in dcol]
                            for name, dcol in zip(dnames, dcolors)}
            domain_colors.on_change_color(self.change_d_color)
            cards.append(QCard(QCardSection(domain_colors), ui_flat=True, ui_bordered=True))

        return Div(*cards, ui_class="column " + str(gap_sm))

    # -- By element type (3D visibility) ----------------------------------
    _TYPE_LABELS = {
        "ET.TET": "Tetrahedra",
        "ET.PRISM": "Prisms · boundary layer",
        "ET.PYRAMID": "Pyramids · closure",
        "ET.HEX": "Hexahedra",
    }

    def _build_eltype(self, comp):
        self._tvis = {}
        types = comp.element_types_3d()
        rows = []
        for et, count in types.items():
            self._tvis[et] = True
            rows.append(self._type_row(comp, et, count))
        return Div(*rows, ui_class="column " + str(gap_sm))

    def _type_row(self, comp, et, count):
        label = self._TYPE_LABELS.get(str(et), str(et))
        sw = Div(ui_class=self._scls(True))

        def toggle(e=None, et=et, sw=sw):
            self._tvis[et] = not self._tvis[et]
            sw.ui_class = self._scls(self._tvis[et])
            self._apply_eltype()
        sw.on("click", toggle)

        return Div(
            Div(label, ui_class=str(grow)),
            Div(str(count), ui_class=str(mono) + " " + str(hint)),
            sw,
            ui_class="row items-center no-wrap " + str(gap_sm),
        )

    def _apply_eltype(self):
        self.comp.set_visible_element_types(
            {t for t, v in self._tvis.items() if v})

    def _scls(self, on):
        return str(prop_switch) + (" " + str(prop_switch_on) if on else "")

    # -- By quality (Jacobian condition number) ---------------------------
    def _build_quality(self, comp):
        q = comp.element_quality()
        self._q = q
        self._qmin = float(np.min(q))
        self._qmax = float(np.max(q))
        self._q_total = len(q)
        self._q_isolate = False
        self._q_thr = float(np.percentile(q, 90))  # default cut: worst ~10%

        qmed = float(np.median(q))
        stats = Div(
            Div(f"best {self._qmin:.2f}"),
            Div(f"median {qmed:.2f}"),
            Div(f"worst {self._qmax:.2f}"),
            ui_class="row " + str(gap_sm) + " " + str(mono) + " " + str(hint),
        )

        # log-binned histogram when the range spans more than a factor of 3
        nbins = 22
        self._q_log = self._qmax > self._qmin * 3
        if self._qmax <= self._qmin:
            edges = np.array([self._qmin, self._qmin + 1.0])
        elif self._q_log:
            edges = np.logspace(np.log10(self._qmin), np.log10(self._qmax), nbins + 1)
        else:
            edges = np.linspace(self._qmin, self._qmax, nbins + 1)
        counts, _ = np.histogram(q, bins=edges)
        self._q_edges = edges
        cmax = max(1, int(counts.max()))
        bars = []
        for i, c in enumerate(counts):
            pos = i / (len(counts) - 1) if len(counts) > 1 else 0.0
            hue = 140 * (1 - pos)               # green (good) → red (bad)
            h = 5 + 39 * (c / cmax)
            fill = Div(ui_style=(
                f"width:100%; height:{h:.0f}px; border-radius:2px;"
                f" background:hsl({hue:.0f},62%,55%);"
            ))
            # The whole column is clickable so even 1-element bars are easy to hit.
            col = Div(QTooltip(f"cond ≥ {edges[i]:.2f} · {int(c)} here"), fill,
                      ui_class=str(qhist_col))
            col.on("click", lambda e=None, i=i: self._set_thr_bar(i))
            bars.append(col)
        self._q_marker = Div(ui_style=self._marker_style(
            self._marker_frac(self._q_thr)))
        histo = Div(*bars, self._q_marker, ui_style=(
            "position:relative; display:flex; align-items:stretch; gap:1px;"
            " height:46px; margin:2px 0;"
        ))

        self._q_sw = Div(ui_class=self._scls(False))
        self._q_sw.on("click", self._toggle_isolate)
        toggle_row = Div(
            Div("Isolate worst elements", ui_class=str(grow)),
            self._q_sw,
            ui_class="row items-center no-wrap " + str(gap_sm),
        )
        self._q_readout = Div(ui_class=str(mono) + " " + str(muted))
        self._update_q_readout()

        return Div(
            stats, histo, toggle_row,
            self._q_readout,
            ui_class="column " + str(gap_sm),
        )

    def _marker_style(self, frac):
        return (
            f"position:absolute; top:0; bottom:0; left:{frac:.1f}%; width:2px;"
            " background:var(--fg); opacity:0.65; pointer-events:none;"
        )

    def _marker_frac(self, thr):
        lo, hi = self._qmin, self._qmax
        if hi <= lo:
            return 100.0
        if self._q_log:
            f = (np.log10(thr) - np.log10(lo)) / (np.log10(hi) - np.log10(lo))
        else:
            f = (thr - lo) / (hi - lo)
        return float(min(1.0, max(0.0, f)) * 100.0)

    def _set_thr_bar(self, i):
        # Click a bar → isolate that bin and everything worse (to its right).
        self._q_thr = float(self._q_edges[i])
        if not self._q_isolate:
            self._q_isolate = True
            self._q_sw.ui_class = self._scls(True)
        self._apply_quality()

    def _toggle_isolate(self, e=None):
        self._q_isolate = not self._q_isolate
        self._q_sw.ui_class = self._scls(self._q_isolate)
        self._apply_quality()

    def _apply_quality(self):
        self._q_marker.ui_style = self._marker_style(self._marker_frac(self._q_thr))
        self.comp.set_quality_threshold(self._q_thr if self._q_isolate else None)
        self._update_q_readout()

    def _update_q_readout(self):
        thr = self._q_thr
        n = int(np.sum(self._q > thr))
        if self._q_isolate:
            self._q_readout.ui_children = [
                f"showing worst {n} of {self._q_total} · cond > {thr:.2f}"]
        else:
            self._q_readout.ui_children = [
                f"worst {n} of {self._q_total} would isolate · cond > {thr:.2f}"]

    # -- color change handlers (unchanged) --------------------------------
    def change_color(self, name, color):
        colors = []
        colmap = dict(zip(name, color))
        for fd in self.comp.mesh.ngmesh.FaceDescriptors():
            if fd.bcname in colmap:
                fd.color = colmap[fd.bcname]
            colors.append([int(fd.color[i] * 255) for i in range(4)])
        self.comp.elements2d.gpu_objects.colormap.set_colormap(colors)
        self.comp.elements2d.set_needs_update()
        self.comp.wgpu.scene.render()

    def change_edge_color(self, name, color):
        colmap = dict(zip(name, color))
        for n, c in colmap.items():
            self.ecolors[n] = [int(c[i] * 255) for i in range(4)]
        self.comp.edge_colors._value = self.ecolors
        edge_descriptors = list(self.comp.mesh.ngmesh.EdgeDescriptors())
        colors = [self.ecolors[ed.name] for ed in edge_descriptors]
        self.comp.elements1d._user_colors = colors
        self.comp.elements1d.set_needs_update()
        self.comp.wgpu.scene.render()

    def change_d_color(self, name, color):
        colmap = dict(zip(name, color))
        for d, c in colmap.items():
            self.dcolors[d] = [int(c[i] * 255) for i in range(4)]
        colors = [self.dcolors[d] for d in self.comp.mesh.GetMaterials()]
        if self.comp.elements3d is not None:
            self.comp.elements3d.colormap.set_colormap(colors)
            self.comp.elements3d.set_needs_update()
            self.comp.wgpu.scene.render()
