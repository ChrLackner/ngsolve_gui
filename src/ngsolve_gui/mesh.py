from ngapp.components import *

import ngsolve as ngs
from ngsolve_webgpu.mesh import *
from webgpu.labels import Labels

from .webgpu_tab import WebgpuTab, _usersettings
import netgen.occ as ngocc
from ngsolve_webgpu import EntityNumbers


class MeshComponent(WebgpuTab):
    def __init__(self, name, data, app_data):
        mesh = data["obj"]
        if isinstance(mesh, ngs.Region):
            self.mesh = mesh.mesh
            self.region_or_mesh = mesh
        else:
            self.mesh = mesh
            self.region_or_mesh = mesh

        self.elements3d = None
        # Base bitarrays (e.g. from DrawBadElements); the effective el2d/el3d
        # bitarrays are the base AND-ed with the active named visibility filters.
        self._base_el2d = data.get("el2d_bitarray", None)
        self._base_el3d = data.get("el3d_bitarray", None)
        self.el2d_bitarray = self._base_el2d
        self.el3d_bitarray = self._base_el3d
        self._vis_filters = {}          # name -> (kind, bool mask); kind in {vol, surf}
        self._el_types_arr = None       # cached per-VOL-element type list
        self._visible_el_types = None   # None = all types visible
        self._quality_arr = None        # cached per-element badness (Jacobian cond.)
        self._quality_threshold = None  # None = no quality isolation

        # -- Observable properties (restored from saved settings) -----------
        tab = app_data.get_tab(name)
        saved = tab.get("settings", {}) if tab else {}
        self.wireframe_visible = Observable(
            saved.get("wireframe_visible", True), "wireframe_visible"
        )
        self.elements1d_visible = Observable(
            saved.get("elements1d_visible", False), "elements1d_visible"
        )
        self.elements2d_visible = Observable(
            saved.get("elements2d_visible", True), "elements2d_visible"
        )
        self.elements3d_visible = Observable(
            saved.get("elements3d_visible", False), "elements3d_visible"
        )
        self.identifications_visible = Observable(
            saved.get("identifications_visible", False), "identifications_visible"
        )
        self.shrink_value = Observable(
            saved.get("shrink", 1.0), "shrink", converter=float
        )
        self.subdivision = Observable(
            saved.get("subdivision",
                      data.get("subdivision",
                               int(_usersettings.get("default_subdivision", -1)))),
            "subdivision", converter=int,
        )
        self.elements3d_subdivision = Observable(
            saved.get("elements3d_subdivision",
                      int(_usersettings.get("default_elements3d_subdivision", -1))),
            "elements3d_subdivision", converter=int,
        )
        actual_curve_order = self.mesh.GetCurveOrder()
        self.mesh_curvature_enabled = Observable(
            saved.get("mesh_curvature_enabled", actual_curve_order > 1),
            "mesh_curvature_enabled",
        )
        self.mesh_curvature_order = Observable(
            saved.get("mesh_curvature_order", max(2, actual_curve_order)),
            "mesh_curvature_order", converter=int,
        )
        self.edge_colors = Observable(
            saved.get("edge_colors", {}), "edge_colors"
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

        # -- Wire GPU side-effects after draw() has created render objects --
        self.wireframe_visible.on_change(self._apply_wireframe)
        self.elements1d_visible.on_change(self._apply_elements1d)
        self.elements2d_visible.on_change(self._apply_elements2d)
        self.elements3d_visible.on_change(self._apply_elements3d)
        self.identifications_visible.on_change(self._apply_identifications)
        self.shrink_value.on_change(self._apply_shrink)
        self.subdivision.on_change(self._apply_subdivision)
        self.elements3d_subdivision.on_change(self._apply_elements3d_subdivision)
        self.mesh_curvature_enabled.on_change(self._apply_curvature)
        self.mesh_curvature_order.on_change(self._apply_curvature_order)
        for entity in self.entity_number_entities:
            obs = getattr(self, f"{entity}_numbers_visible")
            obs.on_change(lambda val, _old, e=entity: self._apply_entity_numbers(e, val))
        self.numbers_one_based.on_change(self._apply_numbers_one_based)

    # -- GPU side-effect handlers -------------------------------------------

    def _apply_wireframe(self, val, _old):
        self.wireframe.active = val
        self.wgpu.scene.render()

    def _apply_elements1d(self, val, _old):
        self.elements1d.active = val
        self.wgpu.scene.render()

    def _apply_elements2d(self, val, _old):
        self.elements2d.active = val
        self.wgpu.scene.render()

    def _apply_elements3d(self, val, _old):
        if self.elements3d is None:
            self.elements3d = MeshElements3d(self.mdata, clipping=self.clipping)
            self.elements3d.shrink = self.shrink_value.value
            self.elements3d.subdivision = self._elements3d_subdiv_override()
            self.scene.render_objects.append(self.elements3d)
            self._add_pickable(self.elements3d, "volume")
        self.elements3d.active = val
        self.wgpu.scene.render()

    def _apply_identifications(self, val, _old):
        self.identifications.active = val
        self.wgpu.scene.render()

    def _apply_shrink(self, val, _old):
        self.mdata.shrink = val
        if self.elements3d is not None:
            self.elements3d.shrink = val
        self.wgpu.scene.render()

    SUBDIVISION_MAX = 5

    def _subdivision_override(self):
        v = int(self.subdivision.value)
        v = max(-1, min(self.SUBDIVISION_MAX, v))
        return None if v < 0 else v + 1

    def _apply_subdivision(self, val, _old):
        clamped = max(-1, min(self.SUBDIVISION_MAX, int(val)))
        if clamped != int(val):
            self.subdivision.value = clamped
            return
        self.mdata.set_needs_update()
        self.draw()

    ELEMENTS3D_SUBDIV_MAX = 3

    def _elements3d_subdiv_override(self):
        v = int(self.elements3d_subdivision.value)
        v = max(-1, min(self.ELEMENTS3D_SUBDIV_MAX, v))
        return None if v < 0 else v + 1

    def _apply_elements3d_subdivision(self, val, _old):
        clamped = max(-1, min(self.ELEMENTS3D_SUBDIV_MAX, int(val)))
        if clamped != int(val):
            self.elements3d_subdivision.value = clamped
            return
        if self.elements3d is not None:
            self.elements3d.subdivision = self._elements3d_subdiv_override()
        self.wgpu.scene.render()

    def _apply_curvature(self, val, _old):
        if not val:
            self.mesh.Curve(1)
        self.mdata.set_needs_update()
        self.draw()

    def _apply_curvature_order(self, val, _old):
        self.mdata.set_needs_update()
        self.draw()

    def _apply_entity_numbers(self, entity, val):
        self._entity_number_renderers[entity].active = val
        self.wgpu.scene.render()

    def _apply_numbers_one_based(self, val, _old):
        for r in self._entity_number_renderers.values():
            r.zero_based = not val
            r.set_needs_update()
        self.wgpu.scene.render()

    # -- Keybinding support -------------------------------------------------

    def get_keybindings(self):
        kb = super().get_keybindings()
        show = [
            ("w", self.toggle_wireframe, "Toggle wireframe"),
            ("2", self.toggle_elements_2d, "Toggle elements 2D"),
            ("1", self.toggle_elements_1d, "Toggle elements 1D"),
            ("i", self.toggle_identifications, "Toggle identifications"),
        ]
        if self.mesh.dim == 3:
            show.append(("3", self.toggle_elements_3d, "Toggle elements 3D"))
        show += self._gizmo_show_bindings()
        kb["flat"].append(("w", self.toggle_wireframe, "Toggle wireframe", "General"))
        kb["modes"].append(("s", "Show", show))
        if self.mesh.dim == 3:
            kb["modes"].append(("c", "Clipping", self._clipping_mode_bindings()))
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

    def toggle_wireframe(self):
        self.wireframe_visible.toggle()

    def toggle_elements_1d(self):
        self.elements1d_visible.toggle()

    def toggle_elements_2d(self):
        self.elements2d_visible.toggle()

    def toggle_elements_3d(self):
        self.elements3d_visible.toggle()

    def toggle_identifications(self):
        self.identifications_visible.toggle()

    def _toggle_numbers(self, entity):
        getattr(self, f"{entity}_numbers_visible").toggle()

    def update(self, title, mesh, settings):
        self.title = title
        if self.mesh == mesh:
            return
        self.mesh = mesh
        self.draw()

    def property_subtitle(self):
        return f"Mesh · {self.mesh.dim}D"

    def property_xref(self):
        return {"label": "Open geometry", "icon": "mdi-cube-outline",
                "callback": self._open_geometry}

    def property_actions(self):
        return [{"label": "Download mesh (.vol.gz)", "icon": "mdi-download",
                 "callback": self._download_mesh}]

    def _download_mesh(self):
        import os, tempfile
        from .file_saver import save_file_dialog
        filename = (self.title or "mesh") + ".vol.gz"
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, filename)
            self.mesh.ngmesh.Save(path)
            with open(path, "rb") as f:
                data = f.read()
        save_file_dialog(data, filename)

    def _open_geometry(self):
        try:
            geo = self.mesh.ngmesh.GetGeometry()
            from .geometry import GeometryComponent
            self.app_data.add_tab(
                "Geo_" + self.title, GeometryComponent, {"obj": geo}, self.app_data
            )
        except Exception as e:
            print(f"Could not extract geometry from mesh: {e}")

    # -- Element-type visibility (3D): isolate boundary-layer prisms etc. --

    def _el_types_array(self):
        if self._el_types_arr is None:
            import ngsolve as ngs
            self._el_types_arr = [el.type for el in self.mesh.Elements(ngs.VOL)]
        return self._el_types_arr

    def element_types_3d(self):
        """{element_type: count} over the 3D (VOL) elements (empty for 2D)."""
        if self.mesh.dim != 3:
            return {}
        from collections import Counter
        return dict(Counter(self._el_types_array()))

    def set_visible_element_types(self, visible):
        """Show only the given 3D element types (one composing volume filter)."""
        import numpy as np
        visible = set(visible)
        self._visible_el_types = visible
        all_types = set(self.element_types_3d().keys())
        if not all_types or visible >= all_types:
            mask = None
        else:
            mask = np.array([t in visible for t in self._el_types_array()], dtype=bool)
        self._set_visibility_filter("eltype", "vol", mask)

    # -- Composable visibility filters -------------------------------------
    # Each mode contributes a named bool mask; the effective bitarray is the
    # base AND of all active masks, so region/type/quality combine instead of
    # overriding one another. (Region visibility itself is alpha-based and so
    # composes independently of the bitarrays.)

    def _set_visibility_filter(self, key, kind, mask):
        """Register (mask) or clear (None) a named visibility filter and
        rebuild. ``kind`` is 'vol' (VOL elements) or 'surf' (2D elements)."""
        if mask is None:
            if key not in self._vis_filters:
                return
            self._vis_filters.pop(key, None)
        else:
            self._vis_filters[key] = (kind, mask)
        self._recompute_visibility()

    def _recompute_visibility(self):
        vol = self._base_el3d
        surf = self._base_el2d
        for kind, mask in self._vis_filters.values():
            if kind == "vol":
                vol = mask if vol is None else (vol & mask)
            else:
                surf = mask if surf is None else (surf & mask)
        self.el3d_bitarray = vol
        self.el2d_bitarray = surf
        self.draw()
        self.wgpu.scene.render()

    # -- Element quality (Jacobian condition number): isolate bad elements -

    def element_quality(self):
        """Per-element badness = max over the element of Norm(J)*Norm(J^-1)
        (Jacobian condition number; ~dim for ideal elements, large for bad
        ones). Computed over the codim-0 elements (VOL) and cached."""
        if self._quality_arr is None:
            import numpy as np
            from ngsolve import Norm, Inv, specialcf
            dim = self.mesh.dim
            cf = Norm(specialcf.JacobianMatrix(dim, dim)) * Norm(
                Inv(specialcf.JacobianMatrix(dim, dim))
            )
            et = ngs.ET.TET if dim == 3 else ngs.ET.TRIG
            intrule = ngs.IntegrationRule(et, 4)
            pnts = self.mesh.MapToAllElements(intrule, ngs.VOL).flatten()
            vals = cf(pnts).reshape((-1, len(intrule)))
            self._quality_arr = np.max(vals, axis=1)
        return self._quality_arr

    def set_quality_threshold(self, threshold):
        """Show only elements whose badness exceeds ``threshold`` (the worst
        ones); ``None`` clears the quality isolation."""
        import numpy as np
        self._quality_threshold = threshold
        if threshold is None:
            mask = None
        else:
            mask = self.element_quality() > threshold
        # 3D meshes filter the volume elements, 2D meshes the area elements.
        kind = "vol" if self.mesh.dim == 3 else "surf"
        self._set_visibility_filter("quality", kind, mask)

    def draw(self):
        curve_enabled = self.mesh_curvature_enabled.value
        curve_order = int(self.mesh_curvature_order.value)
        if curve_enabled:
            self.mesh.Curve(curve_order)

        if self.el2d_bitarray is not None or self.el3d_bitarray is not None:
            self.mdata = MeshData(
                self.region_or_mesh,
                el2d_bitarray=self.el2d_bitarray,
                el3d_bitarray=self.el3d_bitarray,
            )
        else:
            self.mdata = self.app_data.get_mesh_gpu_data(self.region_or_mesh)

        override = self._subdivision_override()
        if override is not None:
            self.mdata.subdivision = override
        else:
            actual_order = self.mesh.GetCurveOrder()
            if actual_order > 3:
                subdiv = (actual_order + 2) // 3 + 1
            elif actual_order > 1:
                subdiv = 3
            else:
                subdiv = 1
            self.mdata.subdivision = subdiv
        self.wireframe = MeshWireframe2d(self.mdata, clipping=self.clipping)
        self.wireframe.active = self.wireframe_visible.value
        saved_edge_colors = self.edge_colors.value
        if saved_edge_colors:
            edge_descriptors = list(self.mesh.ngmesh.EdgeDescriptors())
            edge_colors = [saved_edge_colors.get(ed.name, [0, 0, 0, 255]) for ed in edge_descriptors]
        else:
            edge_colors = None
        self.elements1d = MeshSegments(self.mdata, clipping=self.clipping, colors=edge_colors)
        self.elements1d.active = self.elements1d_visible.value
        self.identifications = MeshIdentifications(self.mdata, clipping=self.clipping)
        self.identifications.active = self.identifications_visible.value
        self.elements2d = MeshElements2d(self.mdata, clipping=self.clipping)
        self.elements2d.active = self.elements2d_visible.value
        if self.elements3d_visible.value:
            self.elements3d = MeshElements3d(self.mdata, clipping=self.clipping)
            self.elements3d.shrink = self.shrink_value.value
            self.elements3d.subdivision = self._elements3d_subdiv_override()
        else:
            self.elements3d = None

        self._entity_number_renderers = {}
        for entity in self.entity_number_entities:
            r = EntityNumbers(self.mdata, entity=entity, clipping=self.clipping, zero_based=not self.numbers_one_based.value)
            r.active = getattr(self, f"{entity}_numbers_visible").value
            self._entity_number_renderers[entity] = r

        render_objects = [
            obj
            for obj in [
                self.elements2d,
                self.wireframe,
                self.elements3d,
                self.elements1d,
                self.identifications,
                self.coordinate_axes,
                self.navigation_cube,
            ]
            if obj is not None
        ]
        render_objects += list(self._entity_number_renderers.values())
        self.wgpu.draw(render_objects, camera=self.camera)

        pickable = [(r, k) for r, k in [
            (self.elements2d, "surface"),
            (self.elements3d, "volume"),
        ] if r is not None]
        self.setup_picking(pickable, self.mesh)


# Register with the component registry
from .registry import register_component
from .sections import MeshDisplaySection, MeshColorSection, ClippingSection, EntityNumbersSection

MeshComponent.property_sections = [
    MeshDisplaySection, MeshColorSection, EntityNumbersSection,
]

register_component(
    "mesh",
    icon="mdi-vector-triangle",
    component_class=MeshComponent,
)
