from ngapp.components import *
from ngsolve_webgpu import *
from .webgpu_tab import WebgpuTab, _usersettings
from . import cerbsim_style as cb
import ngsolve as ngs
import copy
import math


def _fmt_value(v):
    """Fixed-width numeric format for the pick overlay.

    Scientific notation keeps very large/small magnitudes readable; fixed-point
    is used in the [1e-2, 1e2) range. The result is padded to a constant width
    so the value doesn't jitter horizontally as it updates while hovering.
    """
    v = float(v)
    a = abs(v)
    if a != 0 and (a < 1e-2 or a >= 1e2):
        s = f"{v: .4e}"   # e.g. ' 1.2345e+05' / '-1.2345e+05'
    else:
        s = f"{v: .5f}"   # e.g. ' 12.34567'
    return s.rjust(11)


class FunctionComponent(WebgpuTab):
    def __init__(self, name, data, app_data):
        self.app_data = app_data
        cf = data["obj"]
        self.name = name
        self.mdata = None
        self.cf = cf
        self.region_or_mesh = data["mesh"]
        self.draw_vol = data.get("draw_vol", True)
        self.draw_surf = data.get("draw_surf", True)
        self.mesh = (
            self.region_or_mesh.mesh
            if isinstance(self.region_or_mesh, ngs.Region)
            else self.region_or_mesh
        )
        self.order = data.get("order", None)
        if self.order is None:
            self.order = 2
            if isinstance(cf, ngs.GridFunction):
                self.order = min(2, cf.space.globalorder)
        self.deformation = data.get("deformation", None)
        self.deformation_order = data.get("deformation_order", 1)
        self.facet = data.get("facet", None)
        self.contact = data.get("contact", None)
        self.contact_pairs = None

        # -- Resolve initial values from data args + saved settings ---------
        tab = app_data.get_tab(name)
        saved = tab.get("settings", {}) if tab else {}
        minval = data.get("min", 0.0)
        maxval = data.get("max", 1.0)
        autoscale = not ("min" in data or "max" in data) and not data.get(
            "autoscale", False
        )
        discrete_colormap = data.get(
            "discrete_colormap", _usersettings.get("default_discrete_colormap", False)
        )
        if any([v in data for v in ("min", "max", "discrete_colormap", "autoscale")]):
            saved["colormap"] = (autoscale, discrete_colormap, minval, maxval)

        if (
            self.deformation is None
            and not "deformation" in data
            and self.cf.dim == 1
            and self.mesh.dim < 3
        ):
            # Skip auto-deformation for FacetFESpace (can't evaluate on elements)
            is_facet = isinstance(self.cf, ngs.GridFunction) and isinstance(self.cf.space, ngs.FacetFESpace)
            if not is_facet:
                self.deformation = ngs.CF((0, 0, self.cf))

        cv = data.get("clipping_vectors", False)
        sv = data.get("surface_vectors", False)
        fl = data.get("field_lines", False)
        lic = data.get("lic", False)

        # -- Observable properties ------------------------------------------
        s = saved
        self.wireframe_visible = Observable(
            s.get("wireframe_visible", True), "wireframe_visible"
        )
        self.elements2d_visible = Observable(
            s.get("elements2d_visible", True), "elements2d_visible"
        )
        self.facet_visible = Observable(
            bool(self.facet) if self.facet is not None else s.get("facet_visible", False),
            "facet_visible",
        )
        self.facet_thickness = Observable(
            s.get("facet_thickness", 0.008), "facet_thickness", converter=float
        )
        self.clipping_vectors_visible = Observable(
            bool(cv) if cv else s.get("clipping_vectors", False), "clipping_vectors"
        )
        self.surface_vectors_visible = Observable(
            bool(sv) if sv else s.get("surface_vectors", False), "surface_vectors"
        )
        self.field_lines_visible = Observable(
            bool(fl) if fl else s.get("field_lines", False), "field_lines"
        )
        self.clipping_visible = Observable(
            data.get("clipping_function", s.get("clipping_visible", True)),
            "clipping_visible",
        )
        # -- LIC (line integral convolution) on the clipping plane --
        self.lic_visible = Observable(
            bool(lic) if lic else s.get("lic_visible", False), "lic_visible"
        )
        self.lic_kernel_length = Observable(
            s.get("lic_kernel_length", 30), "lic_kernel_length", converter=int
        )
        self.lic_oriented = Observable(
            s.get("lic_oriented", False), "lic_oriented"
        )
        self.lic_thickness = Observable(
            s.get("lic_thickness", 2), "lic_thickness", converter=int
        )
        self.lic_contrast = Observable(
            s.get("lic_contrast", 1.0), "lic_contrast", converter=float
        )
        # Supersampling (SSAA) checkbox: off → 1 sample, on → 2 samples.
        self.lic_supersample = Observable(
            s.get("lic_supersample", False), "lic_supersample"
        )
        self.vector_grid_size = Observable(
            (cv if not isinstance(cv, bool) else None)
            or (sv if not isinstance(sv, bool) else None)
            or s.get("vector_grid_size", int(_usersettings.get("default_vector_grid_size", 20))),
            "vector_grid_size",
        )
        self.vector_scale = Observable(
            s.get("vector_scale", 1.0), "vector_scale", converter=float
        )
        self.vector_scale_by_value = Observable(
            s.get("vector_scale_by_value", False), "vector_scale_by_value",
        )
        self.deformation_enabled = Observable(
            data.get("deformation", None) is not None
            or s.get("deformation_enabled", False),
            "deformation_enabled",
        )
        self.deformation_scale = Observable(
            s.get("deformation_scale", 1.0), "deformation_scale", converter=float
        )
        self.deformation_scale2 = Observable(
            s.get("deformation_scale2", 1.0), "deformation_scale2", converter=float
        )
        cm = s.get("colormap", (autoscale, discrete_colormap, minval, maxval))
        self.colormap_autoscale = Observable(cm[0], "colormap_autoscale")
        self.colormap_discrete = Observable(cm[1], "colormap_discrete")
        self.colormap_min = Observable(cm[2], "colormap_min", converter=float, formatter=lambda v: f"{v:.4g}")
        self.colormap_max = Observable(cm[3], "colormap_max", converter=float, formatter=lambda v: f"{v:.4g}")
        self.colormap_name = Observable(
            s.get("colormap_name", cb.default_colormap(_usersettings)), "colormap_name"
        )
        self.ncolors_colormap = Observable(
            s.get("ncolors_colormap", int(_usersettings.get("default_ncolors", 8))),
            "ncolors_colormap", converter=int,
        )
        self.contact_enabled = Observable(
            s.get("contact_enabled", True), "contact_enabled"
        )
        self.fieldlines_num_lines = Observable(
            s.get("fieldlines_num_lines", 100), "fieldlines_num_lines", converter=int
        )
        self.fieldlines_length = Observable(
            s.get("fieldlines_length", 0.5), "fieldlines_length", converter=float
        )
        self.fieldlines_thickness = Observable(
            s.get("fieldlines_thickness", 0.0015), "fieldlines_thickness", converter=float
        )
        self.fieldlines_direction = Observable(
            s.get("fieldlines_direction", 0), "fieldlines_direction", converter=int
        )

        if self.cf.is_complex:
            self.complex_mode = Observable(
                s.get("complex_mode", "real"), "complex_mode"
            )
            self.complex_animate = Observable(False, "complex_animate")
            self.complex_speed = Observable(
                s.get("complex_speed", 1.0), "complex_speed", converter=float
            )

        # -- Entity number observables --
        self.entity_number_entities = ["vertices", "edges", "facets", "segments", "surface_elements"]
        if self.mesh.dim == 3:
            self.entity_number_entities.append("volume_elements")
        self.entity_number_entities += ["surface_indices", "segment_indices"]
        if self.mesh.dim == 3:
            self.entity_number_entities.append("volume_indices")
        for entity in self.entity_number_entities:
            key = f"{entity}_numbers_visible"
            setattr(self, key, Observable(saved.get(key, False), key))
        self.numbers_one_based = Observable(
            saved.get("numbers_one_based", False), "numbers_one_based"
        )

        super().__init__(name, data, app_data)

        # -- Wire GPU side-effects -----------------------------------------
        self.wireframe_visible.on_change(self._apply_wireframe)
        self.elements2d_visible.on_change(self._apply_elements2d)
        self.facet_visible.on_change(self._apply_facet)
        self.facet_thickness.on_change(self._apply_facet_thickness)
        self.clipping_vectors_visible.on_change(self._apply_clipping_vectors)
        self.surface_vectors_visible.on_change(self._apply_surface_vectors)
        self.field_lines_visible.on_change(self._apply_fieldlines)
        self.clipping_visible.on_change(self._apply_clipping_function)
        self.lic_visible.on_change(self._apply_lic)
        self.lic_kernel_length.on_change(self._apply_lic_kernel_length)
        self.lic_oriented.on_change(self._apply_lic_oriented)
        self.lic_thickness.on_change(self._apply_lic_thickness)
        self.lic_contrast.on_change(self._apply_lic_contrast)
        self.lic_supersample.on_change(self._apply_lic_supersample)
        self.vector_grid_size.on_change(self._apply_vector_grid_size)
        self.vector_scale.on_change(self._apply_vector_scale)
        self.vector_scale_by_value.on_change(self._apply_vector_scale_by_value)
        self.deformation_enabled.on_change(self._apply_deformation_toggle)
        self.deformation_scale.on_change(self._apply_deformation_scale)
        self.deformation_scale2.on_change(self._apply_deformation_scale)
        self.contact_enabled.on_change(self._apply_contact)
        self.colormap_autoscale.on_change(self._apply_autoscale)
        self.colormap_discrete.on_change(self._apply_discrete)
        self.colormap_name.on_change(self._apply_colormap_name)
        if self.cf.is_complex:
            self.complex_mode.on_change(self._apply_complex_mode)
            self.complex_animate.on_change(self._apply_complex_animate)
            self.complex_speed.on_change(self._apply_complex_speed)
        for entity in self.entity_number_entities:
            obs = getattr(self, f"{entity}_numbers_visible")
            obs.on_change(lambda val, _old, e=entity: self._apply_entity_numbers(e, val))
        self.numbers_one_based.on_change(self._apply_numbers_one_based)

    # -- GPU side-effect handlers -------------------------------------------

    def _apply_wireframe(self, val, _old):
        self.wireframe.active = val
        self.wgpu.scene.render()

    def _apply_elements2d(self, val, _old):
        self._sync_surface_elements()
        self.wgpu.scene.render()

    def _sync_surface_elements(self):
        """Show the flat surface field unless a surface LIC is replacing it.

        A SurfaceLIC is itself the surface renderer, so drawing elements2d on top
        of it z-fights; hide elements2d while the surface LIC is visible (the 3D
        ClippingLIC, by contrast, is independent of elements2d)."""
        if self.elements2d is None:
            return
        hide_for_lic = (
            self._lic_is_surface
            and self.lic is not None
            and self.lic_visible.value
        )
        self.elements2d.active = self.elements2d_visible.value and not hide_for_lic

    def _apply_facet(self, visible, _old):
        if self.facet_renderer is not None:
            self.facet_renderer.active = visible
            self.wgpu.scene.render()

    def _apply_facet_thickness(self, val, _old):
        if self.facet_renderer is not None:
            self.facet_renderer.thickness = val
            self.facet_renderer.set_needs_update()
            self.wgpu.scene.render()

    def _apply_clipping_vectors(self, val, _old):
        if self.clipping_vectors is not None:
            self.clipping_vectors.active = val
        self.wgpu.scene.render()

    def _apply_surface_vectors(self, val, _old):
        if self.surface_vectors is not None:
            self.surface_vectors.active = val
        self.wgpu.scene.render()

    def _apply_fieldlines(self, val, _old):
        if self.fieldlines is not None:
            self.fieldlines.active = val
        self.wgpu.scene.render()

    def _apply_clipping_function(self, val, _old):
        if self.clippingcf is not None:
            self.clippingcf.active = val
        self.wgpu.scene.render()

    def _apply_lic(self, val, _old):
        if self.lic is not None:
            self.lic.active = val
        self._sync_surface_elements()
        self.wgpu.scene.render()

    def _apply_lic_kernel_length(self, val, _old):
        if self.lic is not None:
            self.lic.set_kernel_length(val)
        self.wgpu.scene.render()

    def _apply_lic_oriented(self, val, _old):
        if self.lic is not None:
            self.lic.set_oriented(val)
        self.wgpu.scene.render()

    def _apply_lic_thickness(self, val, _old):
        if self.lic is not None:
            self.lic.set_thickness(val)
        self.wgpu.scene.render()

    def _apply_lic_contrast(self, val, _old):
        if self.lic is not None:
            self.lic.set_contrast(val)
        self.wgpu.scene.render()

    def _apply_lic_supersample(self, val, _old):
        if self.lic is not None:
            # Checkbox toggles between 1 (off) and 2 (on) samples per pixel.
            self.lic.set_supersample(2 if val else 1)
        self.wgpu.scene.render()

    def _apply_vector_grid_size(self, val, _old):
        if self.clipping_vectors is not None:
            self.clipping_vectors.set_grid_size(val)
            self.clipping_vectors.set_needs_update()
        if self.surface_vectors is not None:
            self.surface_vectors.set_grid_size(val)
            self.surface_vectors.set_needs_update()
        self.wgpu.scene.render()

    def _apply_vector_scale(self, val, _old):
        for r in self._vector_renderers:
            r.user_scale = val
            r.set_needs_update()
        self.wgpu.scene.render()

    def _apply_vector_scale_by_value(self, val, _old):
        for r in self._vector_renderers:
            r.scale_by_value = val
            r.set_needs_update()
        self.wgpu.scene.render()

    def _apply_deformation_toggle(self, val, _old):
        if self.mdata is None:
            return
        if val:
            self.mdata.deformation_scale = (
                self.deformation_scale.value * self.deformation_scale2.value
            )
        else:
            self.mdata.deformation_scale = 0.0
        if self.clippingcf is not None:
            self.clippingcf.set_needs_update()
        self.wgpu.scene.render()

    def _apply_deformation_scale(self, _val, _old):
        if self.mdata is None:
            return
        if self.deformation_enabled.value:
            self.mdata.deformation_scale = (
                self.deformation_scale.value * self.deformation_scale2.value
            )
            if self.clippingcf is not None:
                self.clippingcf.set_needs_update()
            self.wgpu.scene.render()

    def _pick_info(self, result):
        """Element / region / position / value — value uses the *undeformed*
        point so it stays correct when deformation is on."""
        header, rows, _ = super()._pick_info(result)
        val = self._eval_cf(self._probe_mesh_point(result.world_pos))
        if val is not None:
            if val.size == 1:
                rows.append(("value", _fmt_value(val)))
            else:
                rows.append(("value", "[" + ", ".join(_fmt_value(v) for v in val.flat) + "]"))
            return ("Picked value", rows, True)
        return ("Picked value", rows, False)

    def _eval_cf(self, P):
        try:
            import numpy as np
            mip = self.mesh(*[float(P[i]) for i in range(self.mesh.dim)])
            return np.real(np.asarray(self.cf(mip)))
        except Exception:
            return None

    def _apply_contact(self, val, _old):
        if self.contact_pairs is not None:
            self.contact_pairs.active = val
        self.wgpu.scene.render()

    def _apply_entity_numbers(self, entity, val):
        self._entity_number_renderers[entity].active = val
        self.wgpu.scene.render()

    def _apply_numbers_one_based(self, val, _old):
        for r in self._entity_number_renderers.values():
            r.zero_based = not val
            r.set_needs_update()
        self.wgpu.scene.render()

    # -- Keybinding support -------------------------------------------------

    _COLORMAPS = ["rainbow", "turbo", "viridis", "plasma", "cet_l20", "matlab:jet", "matplotlib:coolwarm"]

    def get_keybindings(self):
        kb = super().get_keybindings()
        kb["flat"].append(("w", self.toggle_wireframe, "Toggle wireframe", "General"))

        # s → Show
        show = [("w", self.toggle_wireframe, "Toggle wireframe")]
        if self.draw_surf:
            show.append(("s", self.toggle_surface_solution, "Toggle surface"))
        if self.facet_renderer is not None:
            show.append(("e", self.toggle_facet, "Toggle element boundaries"))
        if self.surface_vectors is not None:
            show.append(("v", self.toggle_surface_vectors, "Toggle surface vectors"))
        if self.clipping_vectors is not None:
            show.append(("c", self.toggle_clipping_vectors, "Toggle clipping vectors"))
        if self.lic is not None:
            show.append(("l", self.toggle_lic, "Toggle LIC"))
        if self.fieldlines is not None:
            show.append(("f", self.toggle_fieldlines, "Toggle field lines"))
        if self.surface_vectors is not None or self.clipping_vectors is not None:
            show.append(("+", self.increase_vector_density, "Increase vector density"))
            show.append(("-", self.decrease_vector_density, "Decrease vector density"))
        show += self._gizmo_show_bindings()
        kb["modes"].append(("s", "Show", show))

        # c → Clipping (3D only)
        if self.mesh.dim == 3:
            clip = list(self._clipping_mode_bindings())
            if self.clippingcf is not None:
                clip.append(
                    ("f", self.toggle_clipping_function, "Toggle clipping function")
                )
            if self.lic is not None:
                clip.append(("l", self.toggle_lic, "Toggle LIC"))
            kb["modes"].append(("c", "Clipping", clip))

        # d → Deformation
        if self.deformation is not None or (self.cf.dim == 1 and self.mesh.dim < 3):
            kb["modes"].append(
                (
                    "d",
                    "Deformation",
                    [
                        ("d", self.toggle_deformation, "Toggle deformation"),
                        ("+", self.increase_deformation, "Increase scale"),
                        ("-", self.decrease_deformation, "Decrease scale"),
                        ("0", self.reset_deformation, "Reset scale to 1.0"),
                    ],
                )
            )

        # m → Colormap
        kb["modes"].append(
            (
                "m",
                "Colormap",
                [
                    ("a", self.toggle_autoscale, "Toggle autoscale"),
                    ("d", self.toggle_discrete, "Toggle discrete"),
                    ("n", self.cycle_colormap_next, "Next colormap"),
                    ("p", self.cycle_colormap_prev, "Previous colormap"),
                ],
            )
        )

        if self.cf.is_complex:
            kb["modes"].append(
                (
                    "x",
                    "Complex",
                    [
                        ("r", lambda: setattr(self.complex_mode, 'value', 'real'), "Real part"),
                        ("i", lambda: setattr(self.complex_mode, 'value', 'imag'), "Imag part"),
                        ("a", lambda: setattr(self.complex_mode, 'value', 'abs'), "Absolute value"),
                        ("p", lambda: setattr(self.complex_mode, 'value', 'arg'), "Phase/Arg"),
                        ("space", lambda: self.complex_animate.toggle(), "Toggle animation"),
                    ],
                )
            )

        num_bindings = [
            ("v", lambda: self._toggle_numbers("vertices"), "Vertex numbers"),
            ("e", lambda: self._toggle_numbers("edges"), "Edge numbers"),
            ("f", lambda: self._toggle_numbers("facets"), "Facet numbers"),
            ("s", lambda: self._toggle_numbers("surface_elements"), "Surface el. numbers"),
        ]
        if self.mesh.dim == 3:
            num_bindings.append(("3", lambda: self._toggle_numbers("volume_elements"), "Volume el. numbers"))
        kb["modes"].append(("n", "Numbers", num_bindings))

        return kb

    # -- Toggle methods (now one-liners) ------------------------------------

    def toggle_wireframe(self):
        self.wireframe_visible.toggle()

    def toggle_surface_solution(self):
        self.elements2d_visible.toggle()

    def toggle_facet(self):
        self.facet_visible.toggle()

    def toggle_clipping_vectors(self):
        self.clipping_vectors_visible.toggle()

    def toggle_surface_vectors(self):
        self.surface_vectors_visible.toggle()

    def toggle_fieldlines(self):
        self.field_lines_visible.toggle()

    def toggle_clipping_function(self):
        self.clipping_visible.toggle()

    def toggle_lic(self):
        self.lic_visible.toggle()

    def _toggle_numbers(self, entity):
        getattr(self, f"{entity}_numbers_visible").toggle()

    def _change_vector_density(self, factor):
        grid_size = max(10, int(self.vector_grid_size.value * factor))
        self.vector_grid_size.value = grid_size

    def increase_vector_density(self):
        self._change_vector_density(1.25)

    def decrease_vector_density(self):
        self._change_vector_density(0.8)

    def toggle_deformation(self):
        self.deformation_enabled.toggle()

    def increase_deformation(self):
        self._step_deformation(1.25)

    def decrease_deformation(self):
        self._step_deformation(0.8)

    def _step_deformation(self, factor):
        if self.mdata is None:
            return
        self.deformation_scale.value = self.deformation_scale.value * factor

    def reset_deformation(self):
        if self.mdata is None:
            return
        with observable_batch():
            self.deformation_scale.value = 1.0
            self.deformation_scale2.value = 1.0

    def _apply_autoscale(self, val, _old):
        self.colormap.autoscale = val
        if val:
            self.wgpu.scene.redraw(blocking=True)
            self.colormap_min.value = float(self.colormap.minval)
            self.colormap_max.value = float(self.colormap.maxval)
        else:
            self.wgpu.scene.render()

    def _apply_discrete(self, val, _old):
        self.colormap.set_discrete(val)
        self.wgpu.scene.render()

    def _apply_colormap_name(self, val, _old):
        self.colormap.set_colormap(val)
        self.wgpu.scene.render()

    @property
    def _complex_renderers(self):
        return [r for r in [self.elements2d, self.clippingcf, self.clipping_vectors, self.surface_vectors, self.lic] if r is not None]

    @property
    def _vector_renderers(self):
        return [r for r in [self.clipping_vectors, self.surface_vectors] if r is not None]

    def _apply_complex_mode(self, val, _old):
        for r in self._complex_renderers:
            r.set_complex_mode(val)
        self.wgpu.scene.render()

    def _apply_complex_animate(self, val, _old):
        if val:
            if self.colormap_autoscale.value:
                self.colormap_autoscale.value = False
            for r in self._complex_renderers:
                r.animate_phase(self.scene, speed=self.complex_speed.value)
        else:
            for r in self._complex_renderers:
                r.stop_animation()
                r.set_complex_mode(self.complex_mode.value)
            self.wgpu.scene.render()

    def _apply_complex_speed(self, val, _old):
        for r in self._complex_renderers:
            if r._phase_animation is not None:
                r._phase_animation.speed = val

    def toggle_autoscale(self):
        self.colormap_autoscale.toggle()

    def toggle_discrete(self):
        self.colormap_discrete.toggle()

    def _cycle_colormap(self, direction):
        current = self.colormap_name.value
        try:
            idx = self._COLORMAPS.index(current)
        except ValueError:
            idx = 0
        idx = (idx + direction) % len(self._COLORMAPS)
        self.colormap_name.value = self._COLORMAPS[idx]

    def cycle_colormap_next(self):
        self._cycle_colormap(1)

    def cycle_colormap_prev(self):
        self._cycle_colormap(-1)

    def property_subtitle(self):
        kind = "Vector" if self.cf.dim > 1 else "Scalar"
        return f"Function · {self.mesh.dim}D · {kind}"

    def property_xref(self):
        return {"label": "Open as mesh", "icon": "mdi-vector-triangle",
                "callback": self._open_as_mesh}

    def _build_viewport_legend(self):
        # The colorbar (colormap, range, autoscale, component) lives entirely in
        # the in-viewport legend now — not in the side panel.
        from .prop_widgets import ColorbarLegend
        return ColorbarLegend(self)

    def _open_as_mesh(self):
        from .mesh import MeshComponent
        self.app_data.add_tab(
            "Mesh_" + self.name, MeshComponent, {"obj": self.mesh}, self.app_data
        )

    def draw(self):
        func_data = self.app_data.get_function_gpu_data(
            self.cf, self.region_or_mesh, order=self.order
        )
        mdata = func_data.mesh_data

        if self.deformation is not None:
            deform_data = self.app_data.get_function_gpu_data(
                self.deformation, self.region_or_mesh,
                order=self.deformation_order
            )
            mdata = copy.copy(deform_data.mesh_data)
            self.mdata = mdata
            deform_data.mesh_data = mdata
            mdata.deformation_data = deform_data
            mdata.deformation_scale = (
                self.deformation_scale.value * self.deformation_scale2.value
            )
            if not self.deformation_enabled.value:
                mdata.deformation_scale = 0.0
            func_data.mesh_data = mdata
        self.wireframe = MeshWireframe2d(mdata, clipping=self.clipping)
        self.wireframe.active = self.wireframe_visible.value

        autoscale = self.colormap_autoscale.value
        discrete = self.colormap_discrete.value
        minval = self.colormap_min.value
        maxval = self.colormap_max.value
        self.colormap = Colormap(minval=minval, maxval=maxval, colormap=self.colormap_name.value)
        self.colormap.autoscale = autoscale
        self.colormap.discrete = discrete
        self.clipping_vectors = None
        self.lic = None
        # True when self.lic is a SurfaceLIC (2D) that REPLACES the flat surface
        # field, vs a ClippingLIC (3D) that overlays the cutting plane.
        self._lic_is_surface = False
        if self.cf.dim == self.mesh.dim:
            vec3 = self.cf
            if self.cf.dim == 2:
                vec3 = ngs.CF((self.cf[0], self.cf[1], 0))
            vec_data = self.app_data.get_function_gpu_data(
                vec3, self.region_or_mesh, order=self.order
            )
            self.surface_vectors = SurfaceVectors(
                vec_data,
                clipping=self.clipping,
                colormap=self.colormap,
                grid_size=self.vector_grid_size.value,
                scale_by_value=self.vector_scale_by_value.value,
            )
            self.surface_vectors.user_scale = self.vector_scale.value
            self.surface_vectors.active = self.surface_vectors_visible.value
            # Surface LIC: paint the 2D vector field's flow as streamlines on the
            # mesh itself (replaces the flat surface field, like the 3D LIC
            # replaces the clip-plane field). Only for a 2D vector field on a 2D
            # mesh; the 3D case below uses ClippingLIC on the cutting plane.
            if self.mesh.dim == 2:
                self.lic = SurfaceLIC(
                    vec_data,
                    clipping=self.clipping,
                    colormap=self.colormap,
                    kernel_length=self.lic_kernel_length.value,
                    oriented=self.lic_oriented.value,
                    thickness=self.lic_thickness.value,
                    contrast=self.lic_contrast.value,
                    supersample=2 if self.lic_supersample.value else 1,
                )
                self.lic.active = self.lic_visible.value
                self._lic_is_surface = True
        else:
            self.surface_vectors = None
        self.fieldlines = None
        if self.cf.dim == self.mesh.dim:
            from ngsolve_webgpu.cf import FieldLines

            vec3 = self.cf if self.cf.dim == 3 else ngs.CF((self.cf[0], self.cf[1], 0))
            self.fieldlines = FieldLines(
                vec3,
                self.region_or_mesh,
                num_lines=self.fieldlines_num_lines.value,
                length=self.fieldlines_length.value,
                thickness=self.fieldlines_thickness.value,
                direction=self.fieldlines_direction.value,
                colormap=self.colormap,
                clipping=self.clipping,
            )
            self.fieldlines.active = self.field_lines_visible.value
        if self.mesh.dim == 3 and self.draw_vol:
            self.clippingcf = ClippingIsolineRenderer(func_data, clipping=self.clipping,
                                                     n_lines=0, show_field=True, colormap=self.colormap)
            self.clippingcf.active = self.clipping_visible.value
            if self.cf.dim == 3:
                self.clipping_vectors = ClippingVectors(
                    func_data,
                    clipping=self.clipping,
                    colormap=self.colormap,
                    grid_size=self.vector_grid_size.value,
                    scale_by_value=self.vector_scale_by_value.value,
                )
                self.clipping_vectors.user_scale = self.vector_scale.value
                self.clipping_vectors.active = self.clipping_vectors_visible.value
                self.lic = ClippingLIC(
                    func_data,
                    clipping=self.clipping,
                    colormap=self.colormap,
                    kernel_length=self.lic_kernel_length.value,
                    oriented=self.lic_oriented.value,
                    thickness=self.lic_thickness.value,
                    contrast=self.lic_contrast.value,
                    supersample=2 if self.lic_supersample.value else 1,
                )
                self.lic.active = self.lic_visible.value
        else:
            self.clippingcf = None
        if self.draw_surf:
            self.elements2d = IsolineRenderer(
                func_data, n_lines=0, show_field=True,
                clipping=self.clipping, colormap=self.colormap
            )
            self.elements2d.active = self.elements2d_visible.value
            # Hide the flat field if a surface LIC is replacing it.
            self._sync_surface_elements()
        else:
            self.elements2d = None

        # Facet rendering (element-boundary CF visualization)
        self.facet_renderer = None
        if self.mesh.dim == 2 and self.draw_vol:
            facet_cf = self.facet if isinstance(self.facet, ngs.CoefficientFunction) else self.cf
            try:
                facet_data = FacetFunctionData(
                    mdata, facet_cf, order=self.order,
                    deformation_cf=self.deformation if self.deformation is not None and self.deformation_enabled.value else None,
                )
                self.facet_renderer = FacetCFRenderer(
                    facet_data, colormap=self.colormap, clipping=self.clipping,
                    thickness=self.facet_thickness.value,
                )
            except Exception as e:
                import traceback
                print(f"Warning: facet renderer creation failed: {e}")
                traceback.print_exc()
        elif self.mesh.dim == 3 and self.draw_vol:
            try:
                from ngsolve_webgpu.facet_cf import FacetCFRenderer3D
                facet_cf = self.facet if isinstance(self.facet, ngs.CoefficientFunction) else self.cf
                self.facet_renderer = FacetCFRenderer3D(
                    mdata, facet_cf, order=self.order,
                    colormap=self.colormap, clipping=self.clipping,
                )
            except Exception as e:
                import traceback
                print(f"Warning: 3D facet renderer creation failed: {e}")
                traceback.print_exc()
        if self.facet_renderer is not None:
            self.facet_renderer.active = self.facet_visible.value
        if self.cf.is_complex:
            for r in self._complex_renderers:
                r._scene = self.scene
                r.set_complex_mode(self.complex_mode.value)
        self.colorbar = Colorbar(self.colormap)
        self.colorbar.width = 0.8
        self.colorbar.position = (-0.5, 0.9)

        if self.contact is not None:
            from ngsolve_webgpu.contact import ContactPairs
            from webgpu.renderer import MultipleRenderer

            if isinstance(self.contact, list):
                from .region_colors import get_random_colors

                colors = get_random_colors(len(self.contact))
                self.contact_pairs = MultipleRenderer(
                    [
                        ContactPairs(self.region_or_mesh, cb, color=c)
                        for cb, c in zip(self.contact, colors)
                    ]
                )
            else:
                self.contact_pairs = ContactPairs(
                    self.region_or_mesh,
                    self.contact,
                )
            self.contact_pairs.active = self.contact_enabled.value

        render_objects = [
            obj
            for obj in [
                self.clippingcf,
                self.lic,
                self.elements2d,
                self.facet_renderer,
                self.wireframe,
                # colorbar is shown in the UI (FieldSummary), not in the scene
                self.contact_pairs,
                self.clipping_vectors,
                self.surface_vectors,
                self.fieldlines,
                self.coordinate_axes,
                self.navigation_cube,
            ]
            if obj is not None
        ]
        self._entity_number_renderers = {}
        for entity in self.entity_number_entities:
            r = EntityNumbers(mdata, entity=entity, clipping=self.clipping, zero_based=not self.numbers_one_based.value)
            r.active = getattr(self, f"{entity}_numbers_visible").value
            self._entity_number_renderers[entity] = r
        render_objects += list(self._entity_number_renderers.values())
        self.wgpu.draw(render_objects, camera=self.camera)

        pickable = [(r, k) for r, k in [
            (self.elements2d, "surface"),
            # The surface LIC replaces elements2d while visible, so keep picking
            # working on it too (it's a CFRenderer with a select pipeline).
            (self.lic if self._lic_is_surface else None, "surface"),
            (self.clippingcf, "clipping"),
        ] if r is not None]
        self.setup_picking(pickable, self.mesh)

        def set_min_max():
            self.colormap_min.value = float(self.colormap.minval)
            self.colormap_max.value = float(self.colormap.maxval)

        self.wgpu.on_mounted(set_min_max)

        self.func_data = func_data


# Register with the component registry
from .registry import register_component
from .sections import (
    FunctionDisplaySection,
    ClippingSection,
    DeformationSection,
    VectorsFlowSection,
    ComplexSection,
    EntityNumbersSection,
)

# Colormap/colorbar lives in the always-visible FieldSummary (property_summary),
# not as a section — matching the designer's function panel. LIC is folded into
# VectorsFlowSection (grouped with streamlines), so it has no section of its own.
FunctionComponent.property_sections = [
    FunctionDisplaySection,
    DeformationSection,
    VectorsFlowSection,
    ComplexSection,
    EntityNumbersSection,
]

register_component(
    "function",
    icon="mdi-function-variant",
    component_class=FunctionComponent,
)
