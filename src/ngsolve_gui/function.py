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
        self.mesh = self.region_or_mesh.mesh if isinstance(self.region_or_mesh, ngs.Region) else self.region_or_mesh
        self.order = data.get("order", None)
        if self.order is None:
            self.order = 2
            if isinstance(cf, ngs.GridFunction):
                self.order = min(2, cf.space.globalorder)
        self.deformation = data.get("deformation", None)
        self.contact = data.get("contact", None)
        self.contact_pairs = None
        minval = data.get("min", 0.0)
        maxval = data.get("max", 1.0)
        autoscale = not ("min" in data or "max" in data) and not data.get("autoscale", False)
        discrete_colormap = data.get("discrete_colormap", False)
        if any([v in data for v in ("min", "max", "discrete_colormap", "autoscale")]):
            self.settings.set(
                "colormap", (autoscale, discrete_colormap, minval, maxval)
            )
        if self.deformation is None and not "deformation" in data and self.cf.dim == 1 and self.mesh.dim < 3:
            self.deformation = ngs.CF((0, 0, self.cf))
        if data.get("deformation", None) is not None:
            self.settings.set("deformation_enabled", True)
        cv = data.get("clipping_vectors", False)
        if cv:
            if isinstance(cv, bool):
                self.settings.set("clipping_vectors", cv)
            else:
                self.settings.set("clipping_vectors", True)
                self.settings.set("vector_grid_size", cv)
        sv = data.get("surface_vectors", False)
        if sv:
            if isinstance(sv, bool):
                self.settings.set("surface_vectors", sv)
            else:
                self.settings.set("surface_vectors", True)
                self.settings.set("vector_grid_size", sv)
        fl = data.get("field_lines", False)
        if fl:
            self.settings.set("field_lines", True)
        if "clipping_function" in data:
            self.settings.set("clipping_visible", data["clipping_function"])
        super().__init__(name, data, app_data)

    # -- Keybinding support ---------------------------------------------

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
        kb["modes"].append(("s", "Show", show))

        # c → Clipping (3D only)
        if self.mesh.dim == 3:
            clip = list(self._clipping_mode_bindings())
            if self.clippingcf is not None:
                clip.append(("f", self.toggle_clipping_function, "Toggle clipping function"))
            kb["modes"].append(("c", "Clipping", clip))

        # d → Deformation
        if self.deformation is not None or (self.cf.dim == 1 and self.mesh.dim < 3):
            kb["modes"].append(("d", "Deformation", [
                ("d", self.toggle_deformation, "Toggle deformation"),
                ("+", self.increase_deformation, "Increase scale"),
                ("-", self.decrease_deformation, "Decrease scale"),
                ("0", self.reset_deformation, "Reset scale to 1.0"),
            ]))

        # m → Colormap
        kb["modes"].append(("m", "Colormap", [
            ("a", self.toggle_autoscale, "Toggle autoscale"),
            ("d", self.toggle_discrete, "Toggle discrete"),
            ("n", self.cycle_colormap_next, "Next colormap"),
            ("p", self.cycle_colormap_prev, "Previous colormap"),
        ]))

        return kb

    def toggle_wireframe(self):
        self.wireframe.active = not self.wireframe.active
        self.settings.set("wireframe_visible", self.wireframe.active)
        self.wgpu.scene.render()

    def toggle_surface_solution(self):
        self.elements2d.active = not self.elements2d.active
        self.settings.set("elements2d_visible", self.elements2d.active)
        self.wgpu.scene.render()

    def toggle_clipping_vectors(self):
        self.clipping_vectors.active = not self.clipping_vectors.active
        self.settings.set("clipping_vectors", self.clipping_vectors.active)
        self.wgpu.scene.render()

    def toggle_surface_vectors(self):
        self.surface_vectors.active = not self.surface_vectors.active
        self.settings.set("surface_vectors", self.surface_vectors.active)
        self.wgpu.scene.render()

    def toggle_fieldlines(self):
        self.fieldlines.active = not self.fieldlines.active
        self.settings.set("field_lines", self.fieldlines.active)
        self.wgpu.scene.render()

    def toggle_clipping_function(self):
        self.clippingcf.active = not self.clippingcf.active
        self.settings.set("clipping_visible", self.clippingcf.active)
        self.wgpu.scene.render()

    def _change_vector_density(self, factor):
        grid_size = self.settings.get("vector_grid_size", 200)
        grid_size = max(10, int(grid_size * factor))
        self.settings.set("vector_grid_size", grid_size)
        if self.clipping_vectors is not None:
            self.clipping_vectors.set_grid_size(grid_size)
            self.clipping_vectors.set_needs_update()
        if self.surface_vectors is not None:
            self.surface_vectors.set_grid_size(grid_size)
            self.surface_vectors.set_needs_update()
        self.wgpu.scene.render()

    def increase_vector_density(self):
        self._change_vector_density(1.25)

    def decrease_vector_density(self):
        self._change_vector_density(0.8)

    def toggle_deformation(self):
        if self.mdata is None:
            return
        enabled = not self.settings.get("deformation_enabled", False)
        self.settings.set("deformation_enabled", enabled)
        if enabled:
            scale = self.settings.get("deformation_scale", 1.0) * self.settings.get("deformation_scale2", 1.0)
        else:
            scale = 0.0
        self.mdata.deformation_scale = scale
        self.wgpu.scene.render()

    def increase_deformation(self):
        self._step_deformation(1.25)

    def decrease_deformation(self):
        self._step_deformation(0.8)

    def _step_deformation(self, factor):
        if self.mdata is None:
            return
        scale = self.settings.get("deformation_scale", 1.0) * factor
        self.settings.set("deformation_scale", scale)
        if self.settings.get("deformation_enabled", False):
            self.mdata.deformation_scale = scale * self.settings.get("deformation_scale2", 1.0)
            self.wgpu.scene.render()

    def reset_deformation(self):
        if self.mdata is None:
            return
        self.settings.set("deformation_scale", 1.0)
        self.settings.set("deformation_scale2", 1.0)
        if self.settings.get("deformation_enabled", False):
            self.mdata.deformation_scale = 1.0
            self.wgpu.scene.render()

    def toggle_autoscale(self):
        self.colormap.autoscale = not self.colormap.autoscale
        if self.colormap.autoscale:
            self.wgpu.scene.redraw(blocking=True)
        else:
            self.wgpu.scene.render()
        self.settings.set("colormap", (
            self.colormap.autoscale, self.colormap.discrete,
            self.colormap.minval, self.colormap.maxval,
        ))

    def toggle_discrete(self):
        self.colormap.set_discrete(not self.colormap.discrete)
        self.wgpu.scene.render()
        self.settings.set("colormap", (
            self.colormap.autoscale, self.colormap.discrete,
            self.colormap.minval, self.colormap.maxval,
        ))

    def _cycle_colormap(self, direction):
        current = self.settings.get("colormap_name", "matlab:jet")
        try:
            idx = self._COLORMAPS.index(current)
        except ValueError:
            idx = 0
        idx = (idx + direction) % len(self._COLORMAPS)
        name = self._COLORMAPS[idx]
        self.colormap.set_colormap(name)
        self.settings.set("colormap_name", name)
        self.redraw()
        self.wgpu.scene.render()

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
            mdata.deformation_scale = self.settings.get(
                "deformation_scale", 1.0
            ) * self.settings.get("deformation_scale2", 1.0)
            if not self.settings.get("deformation_enabled", False):
                mdata.deformation_scale = 0.0
            func_data.mesh_data = mdata
        self.wireframe = MeshWireframe2d(mdata, clipping=self.clipping)
        self.wireframe.active = self.settings.get("wireframe_visible", True)

        autoscale, discrete, minval, maxval = self.settings.get(
            "colormap", (True, False, 0.0, 1.0)
        )
        self.colormap = Colormap(minval=minval, maxval=maxval)
        self.colormap.autoscale = autoscale
        self.colormap.discrete = discrete
        self.clipping_vectors = None
        if self.cf.dim == self.mesh.dim:
            vec3 = self.cf
            if self.cf.dim == 2:
                vec3 = ngs.CF((self.cf[0], self.cf[1], 0))
            vec_data = self.app_data.get_function_gpu_data(vec3,
                                                           self.region_or_mesh, order=self.order)
            self.surface_vectors = SurfaceVectors(vec_data, clipping=self.clipping, colormap=self.colormap,
                                                  grid_size=self.settings.get("vector_grid_size", 200))
            self.surface_vectors.active = self.settings.get("surface_vectors", False)
        else:
            self.surface_vectors = None
        self.fieldlines = None
        if self.cf.dim == self.mesh.dim:
            from ngsolve_webgpu.cf import FieldLines
            vec3 = self.cf if self.cf.dim == 3 else ngs.CF((self.cf[0], self.cf[1], 0))
            self.fieldlines = FieldLines(
                vec3,
                self.region_or_mesh,
                num_lines=self.settings.get("fieldlines_num_lines", 100),
                length=self.settings.get("fieldlines_length", 0.5),
                thickness=self.settings.get("fieldlines_thickness", 0.0015),
                direction=self.settings.get("fieldlines_direction", 0),
                colormap=self.colormap,
                clipping=self.clipping,
            )
            self.fieldlines.active = self.settings.get("field_lines", False)
        if self.mesh.dim == 3 and self.draw_vol:
            self.clippingcf = ClippingCF(func_data, self.clipping, self.colormap)
            self.clippingcf.active = self.settings.get("clipping_visible", True)
            if self.cf.dim == 3:
                self.clipping_vectors = ClippingVectors(
                    func_data,
                    clipping=self.clipping,
                    colormap=self.colormap,
                    grid_size=self.settings.get("vector_grid_size", 200),
                )
                self.clipping_vectors.active = self.settings.get(
                    "clipping_vectors", False
                )
        else:
            self.clippingcf = None
        if self.draw_surf:
            self.elements2d = CFRenderer(
                func_data, clipping=self.clipping, colormap=self.colormap
            )
            self.elements2d.active = self.settings.get("elements2d_visible", True)
        else:
            self.elements2d = None
        self.colorbar = Colorbar(self.colormap)
        self.colorbar.width = 0.8
        self.colorbar.position = (-0.5, 0.9)

        if self.contact is not None:
            from ngsolve_webgpu.contact import ContactPairs
            from webgpu.renderer import MultipleRenderer
            if isinstance(self.contact, list):
                from .region_colors import get_random_colors
                colors = get_random_colors(len(self.contact))
                self.contact_pairs = MultipleRenderer([ContactPairs(self.region_or_mesh, cb, color=c) for cb, c in zip(self.contact, colors)])
            else:
                self.contact_pairs = ContactPairs(
                    self.region_or_mesh,
                    self.contact,
                )
            self.contact_pairs.active = self.settings.get(
                "contact_enabled", True
            )

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
            ]
            if obj is not None
        ]
        self.wgpu.draw(render_objects, camera=self.camera)

        def set_min_max():
            self.min_max = (self.colormap.minval, self.colormap.maxval)
            self.settings.set(
                "colormap",
                (self.colormap.autoscale, self.colormap.discrete, self.colormap.minval, self.colormap.maxval),
            )

        self.wgpu.on_mounted(set_min_max)

        self.func_data = func_data


# Register with the component registry
from .registry import register_component
from .sections import (
    ColorbarSection, ClippingSection, DeformationSection,
    VectorSection, FieldLinesSection, FunctionOptionsSection,
)

register_component("function",
    icon="mdi-function-variant",
    component_class=FunctionComponent,
    sections=[ColorbarSection, ClippingSection, DeformationSection,
              VectorSection, FieldLinesSection, FunctionOptionsSection],
)
