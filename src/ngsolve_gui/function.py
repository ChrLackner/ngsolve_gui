from ngapp.components import *
from ngsolve_webgpu import *
from .webgpu_tab import WebgpuTab
import ngsolve as ngs
import copy


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
        discrete_colormap = data.get("discrete_colormap", False)
        if any([v in data for v in ("min", "max", "discrete_colormap", "autoscale")]):
            saved["colormap"] = (autoscale, discrete_colormap, minval, maxval)

        if (
            self.deformation is None
            and not "deformation" in data
            and self.cf.dim == 1
            and self.mesh.dim < 3
        ):
            self.deformation = ngs.CF((0, 0, self.cf))

        cv = data.get("clipping_vectors", False)
        sv = data.get("surface_vectors", False)
        fl = data.get("field_lines", False)

        # -- Observable properties ------------------------------------------
        s = saved
        self.wireframe_visible = Observable(
            s.get("wireframe_visible", True), "wireframe_visible"
        )
        self.elements2d_visible = Observable(
            s.get("elements2d_visible", True), "elements2d_visible"
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
        self.vector_grid_size = Observable(
            (cv if not isinstance(cv, bool) else None)
            or (sv if not isinstance(sv, bool) else None)
            or s.get("vector_grid_size", 200),
            "vector_grid_size",
        )
        self.vector_scale = Observable(
            s.get("vector_scale", 1.0), "vector_scale", converter=float
        )
        self.vector_scale_by_value = Observable(
            s.get("vector_scale_by_value", True), "vector_scale_by_value",
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
        self.colormap_min = Observable(cm[2], "colormap_min", converter=float)
        self.colormap_max = Observable(cm[3], "colormap_max", converter=float)
        self.colormap_name = Observable(
            s.get("colormap_name", "matlab:jet"), "colormap_name"
        )
        self.ncolors_colormap = Observable(
            s.get("ncolors_colormap", 8), "ncolors_colormap", converter=int
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
        self.clipping_vectors_visible.on_change(self._apply_clipping_vectors)
        self.surface_vectors_visible.on_change(self._apply_surface_vectors)
        self.field_lines_visible.on_change(self._apply_fieldlines)
        self.clipping_visible.on_change(self._apply_clipping_function)
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
        if self.elements2d is not None:
            self.elements2d.active = val
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
        self.wgpu.scene.render()

    def _apply_deformation_scale(self, _val, _old):
        if self.mdata is None:
            return
        if self.deformation_enabled.value:
            self.mdata.deformation_scale = (
                self.deformation_scale.value * self.deformation_scale2.value
            )
            self.wgpu.scene.render()

    def _format_pick_result(self, result):
        """Show element, region, position, and solution value."""
        pos = result.world_pos
        val = result.evaluate(self.cf, self.mesh)
        label = f"{result.kind_label} El {result.element_nr}"
        region = result.region_name or ""
        coords = f"({pos[0]:>9.4f}, {pos[1]:>9.4f}, {pos[2]:>9.4f})"
        text = f"{label:<14s} {region:<12s} {coords}"
        if val is not None:
            if val.size == 1:
                text += f"  val={float(val):>12.6f}"
            else:
                text += f"  val=[{', '.join(f'{v:>9.4f}' for v in val.flat)}]"
        return text

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

    _COLORMAPS = ["viridis", "plasma", "cet_l20", "matlab:jet", "matplotlib:coolwarm"]

    def get_keybindings(self):
        kb = super().get_keybindings()
        kb["flat"].append(("w", self.toggle_wireframe, "Toggle wireframe", "General"))

        # s → Show
        show = [("w", self.toggle_wireframe, "Toggle wireframe")]
        if self.draw_surf:
            show.append(("s", self.toggle_surface_solution, "Toggle surface"))
        if self.surface_vectors is not None:
            show.append(("v", self.toggle_surface_vectors, "Toggle surface vectors"))
        if self.clipping_vectors is not None:
            show.append(("c", self.toggle_clipping_vectors, "Toggle clipping vectors"))
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

    def toggle_clipping_vectors(self):
        self.clipping_vectors_visible.toggle()

    def toggle_surface_vectors(self):
        self.surface_vectors_visible.toggle()

    def toggle_fieldlines(self):
        self.field_lines_visible.toggle()

    def toggle_clipping_function(self):
        self.clipping_visible.toggle()

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
        self.redraw()
        self.wgpu.scene.render()

    @property
    def _complex_renderers(self):
        return [r for r in [self.elements2d, self.clippingcf, self.clipping_vectors, self.surface_vectors] if r is not None]

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

    def draw(self):
        func_data = self.app_data.get_function_gpu_data(
            self.cf, self.region_or_mesh, order=self.order
        )
        mdata = func_data.mesh_data

        if self.deformation is not None:
            deform_data = self.app_data.get_function_gpu_data(
                self.deformation, self.region_or_mesh, order=1
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
        self.colormap = Colormap(minval=minval, maxval=maxval)
        self.colormap.autoscale = autoscale
        self.colormap.discrete = discrete
        self.clipping_vectors = None
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
            self.clippingcf = ClippingCF(func_data, self.clipping, self.colormap)
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
        else:
            self.clippingcf = None
        if self.draw_surf:
            self.elements2d = CFRenderer(
                func_data, clipping=self.clipping, colormap=self.colormap
            )
            self.elements2d.active = self.elements2d_visible.value
        else:
            self.elements2d = None
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
                self.elements2d,
                self.wireframe,
                self.colorbar,
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
    ColorbarSection,
    ClippingSection,
    DeformationSection,
    VectorSection,
    FieldLinesSection,
    FunctionOptionsSection,
    EntityNumbersSection,
)

register_component(
    "function",
    icon="mdi-function-variant",
    component_class=FunctionComponent,
    sections=[
        ColorbarSection,
        ClippingSection,
        DeformationSection,
        VectorSection,
        FieldLinesSection,
        FunctionOptionsSection,
        EntityNumbersSection,
    ],
)
