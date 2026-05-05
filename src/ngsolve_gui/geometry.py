from collections import defaultdict

from ngapp.components import *

from ngsolve_webgpu import *
from ngsolve_webgpu.pick import GeoPickResult
import ngsolve as ngs
import netgen.occ as ngocc
from .webgpu_tab import WebgpuTab


class GeometryComponent(WebgpuTab):
    def __init__(self, name, data, app_data):
        self.geo = data["obj"]
        self.selected = None
        self._selected_items = []  # list of (kind, index) — ordered, no dups
        self._selection_section = None
        self._picking_always_active = True
        tab = app_data.get_tab(name)
        s = tab.get("settings", {}) if tab else {}
        self.show_edges = Observable(s.get("show_edges", True), "show_edges")
        self.show_vertices = Observable(s.get("show_vertices", False), "show_vertices")
        self.maxh = Observable(s.get("maxh", 1000), "maxh", converter=float)
        self.segments_per_edge = Observable(s.get("segments_per_edge", 0.2), "segments_per_edge", converter=float)
        self.curvaturesafety = Observable(s.get("curvaturesafety", 1.5), "curvaturesafety", converter=float)
        self.closeedgefac = Observable(s.get("closeedgefac", None), "closeedgefac")
        self.pick_solid = Observable(False, "pick_solid")
        self.pick_faces = Observable(True, "pick_faces")
        self.pick_edges = Observable(True, "pick_edges")
        self.pick_vertices = Observable(False, "pick_vertices")
        self._hidden_solids = set()  # set of hidden solid indices
        self._face_to_solids = defaultdict(set)  # face_idx -> set of solid indices
        super().__init__(name, data, app_data)
        self.show_edges.on_change(self._apply_show_edges)
        self.show_vertices.on_change(self._apply_show_vertices)
        self._updating_pick_modes = False
        self.pick_solid.on_change(self._on_pick_solid_change)
        self.pick_faces.on_change(self._on_pick_entity_change)
        self.pick_edges.on_change(self._on_pick_entity_change)
        self.pick_vertices.on_change(self._on_pick_entity_change)

    # -- Keybinding support ---------------------------------------------

    def get_keybindings(self):
        kb = super().get_keybindings()
        kb["modes"].append(
            (
                "s",
                "Show",
                [
                    ("e", self.toggle_edges, "Toggle edges"),
                    ("v", self.toggle_vertices, "Toggle vertices"),
                    ("h", self._hide_selected_shape, "Hide selected"),
                    ("u", self._show_all_shapes, "Unhide all"),
                ] + self._gizmo_show_bindings(),
            )
        )
        kb["modes"].append(("c", "Clipping", self._clipping_mode_bindings()))
        kb["modes"].append(
            (
                "p",
                "Pick",
                [
                    ("s", self.pick_solid.toggle, "Solids"),
                    ("f", self.pick_faces.toggle, "Faces"),
                    ("e", self.pick_edges.toggle, "Edges"),
                    ("v", self.pick_vertices.toggle, "Vertices"),
                ],
            )
        )
        return kb

    def toggle_edges(self):
        self.show_edges.toggle()

    def _apply_show_edges(self, val, _old):
        self.geo_renderer.edges.active = val
        self.scene.render()

    def toggle_vertices(self):
        self.show_vertices.toggle()

    def _apply_show_vertices(self, val, _old):
        self.geo_renderer.vertices.active = val or self.pick_vertices.value
        self.scene.render()

    def _create_meshing_geo(self):
        return ngocc.OCCGeometry(self.geo.shape)

    def _meshing_options(self):
        return {
            "maxh": self.maxh.value,
            "segmentsperedge": self.segments_per_edge.value,
            "curvaturesafety": self.curvaturesafety.value,
            "closeedgefac": self.closeedgefac.value,
        }

    def create_mesh(self):
        print("Generate mesh...")
        geo = self._create_meshing_geo()
        import netgen.meshing as ngm

        mesh = ngm.Mesh()
        try:
            geo.GenerateMesh(mesh=mesh, **self._meshing_options())
            mesh.Curve(5)
        except Exception as e:
            self.quasar.dialog(
                {
                    "title": "Error generating mesh",
                    "message": str(e),
                }
            )
        mesh = ngs.Mesh(mesh)
        from .mesh import MeshComponent

        self.app_data.add_tab(
            "Mesh_" + self.title, MeshComponent, {"obj": mesh}, self.app_data
        )

    @property
    def clipping(self):
        return self.app_data.clipping

    def _show_all_shapes(self):
        self._hidden_solids.clear()
        colors = self.geo_renderer.faces.colors
        for i in range(len(colors) // 4):
            colors[i * 4 + 3] = 1.0
        self.geo_renderer.faces.set_colors(colors)
        colors = self.geo_renderer.edges.colors
        for i in range(len(colors) // 4):
            colors[i * 4 + 3] = 1.0
        self.geo_renderer.edges.set_colors(colors)
        colors = self.geo_renderer.vertices.colors
        for i in range(len(colors) // 4):
            colors[i * 4 + 3] = 1.0
        self.geo_renderer.vertices.set_colors(colors)
        self.wgpu.scene.render()

    def _build_face_to_solids(self):
        """Build mapping from face index to set of solid indices that contain it."""
        if self._face_to_solids:
            return
        try:
            solids = list(self.geo.shape.solids)
            n_faces = len(self.geo.faces)
            for solid_idx, solid in enumerate(solids):
                centers = {tuple(round(c, 8) for c in f.center) for f in solid.faces}
                for fi in range(n_faces):
                    gc = tuple(round(c, 8) for c in self.geo.faces[fi].center)
                    if gc in centers:
                        self._face_to_solids[fi].add(solid_idx)
        except Exception:
            pass

    def _build_edge_to_faces(self):
        """Build mapping from edge index to set of face indices that contain it."""
        if hasattr(self, '_edge_to_faces') and self._edge_to_faces:
            return
        self._edge_to_faces = defaultdict(set)
        try:
            edge_centers = [tuple(round(c, 8) for c in e.center) for e in self.geo.edges]
            center_to_edge = {}
            for ei, ec in enumerate(edge_centers):
                center_to_edge[ec] = ei
            for fi, face in enumerate(self.geo.faces):
                for e in face.edges:
                    ec = tuple(round(c, 8) for c in e.center)
                    if ec in center_to_edge:
                        self._edge_to_faces[center_to_edge[ec]].add(fi)
        except Exception:
            pass

    def _build_vertex_to_faces(self):
        """Build mapping from vertex index to set of face indices that contain it."""
        if hasattr(self, '_vertex_to_faces') and self._vertex_to_faces:
            return
        self._vertex_to_faces = defaultdict(set)
        try:
            verts = list(set(self.geo.shape.vertices))
            vert_positions = [tuple(round(c, 8) for c in v.p) for v in verts]
            pos_to_vert = {}
            for vi, vp in enumerate(vert_positions):
                pos_to_vert[vp] = vi
            for fi, face in enumerate(self.geo.faces):
                for v in face.vertices:
                    vp = tuple(round(c, 8) for c in v.p)
                    if vp in pos_to_vert:
                        self._vertex_to_faces[pos_to_vert[vp]].add(fi)
        except Exception:
            pass

    def _update_edge_vertex_visibility(self):
        """Hide edges/vertices that have no visible faces attached."""
        face_colors = self.geo_renderer.faces.colors
        hidden_faces = {i for i in range(len(face_colors) // 4) if face_colors[i * 4 + 3] == 0.0}

        self._build_edge_to_faces()
        edge_colors = self.geo_renderer.edges.colors
        for ei, faces in self._edge_to_faces.items():
            if faces and faces.issubset(hidden_faces):
                edge_colors[ei * 4 + 3] = 0.0
            else:
                edge_colors[ei * 4 + 3] = 1.0
        self.geo_renderer.edges.set_colors(edge_colors)

        self._build_vertex_to_faces()
        vert_colors = self.geo_renderer.vertices.colors
        for vi, faces in self._vertex_to_faces.items():
            if faces and faces.issubset(hidden_faces):
                vert_colors[vi * 4 + 3] = 0.0
            else:
                vert_colors[vi * 4 + 3] = 1.0
        self.geo_renderer.vertices.set_colors(vert_colors)

    def _get_entity(self, kind, index):
        """Return the OCC shape object for a (kind, index) selection."""
        try:
            if kind == "face":
                return self.geo.faces[index]
            elif kind == "edge":
                return self.geo.edges[index]
            elif kind == "vertex":
                return list(self.geo.shape.vertices)[index]
            elif kind == "solid":
                return list(self.geo.shape.solids)[index]
        except (IndexError, Exception):
            pass
        return None

    def change_maxh(self, event):
        value = event.value
        try:
            if value is None or value == "":
                value = None
            else:
                value = float(value)
                if value <= 0:
                    raise ValueError("Max mesh size must be positive.")
            if self._selection_section:
                self._selection_section.meshsize_input.ui_error = False
            for kind, idx in self._selected_items:
                entity = self._get_entity(kind, idx)
                if entity is not None:
                    entity.maxh = value if value is not None else 1e99
        except ValueError as e:
            if self._selection_section:
                self._selection_section.meshsize_input.ui_error_message = str(e)
                self._selection_section.meshsize_input.ui_error = True

    def change_name(self, event):
        value = event.value
        try:
            if value == "":
                value = None
            for kind, idx in self._selected_items:
                entity = self._get_entity(kind, idx)
                if entity is not None:
                    entity.name = value
            if self._selection_section:
                self._selection_section.name_input.ui_error = False
        except ValueError as e:
            if self._selection_section:
                self._selection_section.name_input.ui_error_message = str(e)
                self._selection_section.name_input.ui_error = True

    def _hide_selected_shape(self, event=None):
        if not self._selected_items:
            return
        face_colors = self.geo_renderer.faces.colors
        for kind, idx in self._selected_items:
            if kind == "face":
                face_colors[idx * 4 + 3] = 0.0
            elif kind == "edge":
                edge_colors = self.geo_renderer.edges.colors
                edge_colors[idx * 4 + 3] = 0.0
                self.geo_renderer.edges.set_colors(edge_colors)
            elif kind == "solid":
                self._hidden_solids.add(idx)
        # For solids: hide faces only if ALL their solids are hidden
        if any(k == "solid" for k, _ in self._selected_items):
            self._build_face_to_solids()
            for face_idx, solids in self._face_to_solids.items():
                if solids and solids.issubset(self._hidden_solids):
                    face_colors[face_idx * 4 + 3] = 0.0
                elif not solids.issubset(self._hidden_solids):
                    face_colors[face_idx * 4 + 3] = 1.0
        self.geo_renderer.faces.set_colors(face_colors)
        self._update_edge_vertex_visibility()
        self._selected_items = []
        self._update_selection_buffers()
        self._update_selection_panel()
        self.scene.render()

    def draw(self):
        self.geo_renderer = GeometryRenderer(self.geo, clipping=self.clipping)
        self.geo_renderer.edges.active = self.show_edges.value
        scene = self.wgpu.draw([self.geo_renderer, self.coordinate_axes, self.navigation_cube], camera=self.app_data.camera)
        self.clipping.center = 0.5 * (scene.bounding_box[1] + scene.bounding_box[0])

        # Hover picking: overlay + highlight on mousemove
        self._geo_click_pending = False
        self.setup_picking(
            [(self.geo_renderer.faces, "face"), (self.geo_renderer.edges, "edge"), (self.geo_renderer.vertices, "vertex")],
            None,
        )
        self._update_pick_modes()

        # Left-click for selection, Ctrl+click for multi-select
        def on_click(event):
            if event["button"] == 0:
                self._geo_click_pending = True
                self._click_ctrl = event.get("ctrlKey", False)
                self.scene.select(event["canvasX"], event["canvasY"])
        scene.input_handler.on_click(on_click)

    def _on_pick_select(self, event, kind="face"):
        try:
            result = GeoPickResult(event, self.geo, self.scene.options.camera)
            pos = result.world_pos
            coords = f"({pos[0]:>9.4f}, {pos[1]:>9.4f}, {pos[2]:>9.4f})"
            hl = self._highlight

            if self.pick_solid.value and result.geo_type == 2:
                solid_idx = int(self.geo_renderer.faces._solid_ids[result.index])
                if solid_idx in self._hidden_solids:
                    self._clear_highlight()
                    self.pick_overlay.hide()
                    self.scene._render_highlight()
                    return
                solid_name = ""
                try:
                    solid_name = list(self.geo.shape.solids)[solid_idx].name or ""
                except Exception:
                    pass
                text = f"{'Solid':<8s}{solid_idx:<6d} {solid_name:<12s} {coords}"
                hl.renderer_id = event.obj_id
                hl.element_id = 0xFFFFFFFF
                hl.region_index = 0xFFFFFFFF
                hl.solid_index = solid_idx
            else:
                name = result.name or ""
                text = f"{result.kind_label:<8s}{result.index:<6d} {name:<12s} {coords}"
                hl.renderer_id = event.obj_id
                hl.element_id = 0xFFFFFFFF
                hl.region_index = result.index
                hl.solid_index = 0xFFFFFFFF

            self.pick_overlay.show_text(text)

            # Handle click → update selection
            if self._geo_click_pending:
                self._geo_click_pending = False
                if self.pick_solid.value and result.geo_type == 2:
                    sel_kind = "solid"
                    sel_index = solid_idx
                else:
                    sel_kind = {2: "face", 1: "edge", 0: "vertex"}.get(result.geo_type, "face")
                    sel_index = result.index
                item = (sel_kind, sel_index)
                if getattr(self, '_click_ctrl', False):
                    if item in self._selected_items:
                        self._selected_items.remove(item)
                    else:
                        self._selected_items.append(item)
                else:
                    self._selected_items = [item]
                self._update_selection_buffers()
                self._update_selection_panel()

            hl.update_buffer()
            self.scene._render_highlight()
        except Exception:
            self.pick_overlay.hide()

    def _on_pick_out(self, ev):
        self._clear_highlight()
        if self._selected_items:
            n = len(self._selected_items)
            self.pick_overlay.show_text(
                f"{n} selected" if n > 1 else self._describe_item(self._selected_items[0])
            )
        else:
            self.pick_overlay.hide()
        self.scene.render()

    def _on_pick_background(self, ev):
        if self._geo_click_pending:
            self._geo_click_pending = False
            self._selected_items = []
            self._update_selection_buffers()
            self._clear_highlight()
            self.pick_overlay.hide()
            if self._selection_section:
                self._selection_section.clear_selection()
        else:
            self._clear_highlight()
            if self._selected_items:
                n = len(self._selected_items)
                self.pick_overlay.show_text(
                    f"{n} selected" if n > 1 else self._describe_item(self._selected_items[0])
                )
            else:
                self.pick_overlay.hide()
        self.scene._render_highlight()

    def _describe_item(self, item):
        kind, idx = item
        if kind == "face":
            name = self.geo.faces[idx].name or ""
            return f"Face {idx}" + (f"  {name}" if name else "")
        elif kind == "edge":
            name = self.geo.edges[idx].name or ""
            return f"Edge {idx}" + (f"  {name}" if name else "")
        elif kind == "vertex":
            return f"Vertex {idx}"
        elif kind == "solid":
            try:
                name = list(self.geo.shape.solids)[idx].name or ""
            except Exception:
                name = ""
            return f"Solid {idx}" + (f"  {name}" if name else "")
        return f"{kind} {idx}"

    def _update_selection_buffers(self):
        """Update GPU selection buffers from _selected_items."""
        face_sel, edge_sel, vert_sel = [], [], []
        for kind, idx in self._selected_items:
            if kind == "face":
                face_sel.append(idx)
            elif kind == "edge":
                edge_sel.append(idx)
            elif kind == "vertex":
                vert_sel.append(idx)
        self.geo_renderer.faces.set_selection(face_sel)
        self.geo_renderer.edges.set_selection(edge_sel)
        self.geo_renderer.vertices.set_selection(vert_sel)

    def _update_selection_panel(self):
        if not self._selection_section:
            return
        if not self._selected_items:
            self.selected = None
            self._selection_section.clear_selection()
        elif len(self._selected_items) == 1:
            kind, idx = self._selected_items[0]
            self.selected = (kind, idx)
            self._selection_section.update_selection(kind, idx)
        else:
            kind, idx = self._selected_items[-1]
            self.selected = (kind, idx)
            self._selection_section.update_multi_selection(self._selected_items)

    def _on_pick_solid_change(self, val, _old):
        if self._updating_pick_modes:
            return
        self._updating_pick_modes = True
        if val:
            self.pick_faces.value = False
            self.pick_edges.value = False
            self.pick_vertices.value = False
        self._update_pick_modes()
        self._updating_pick_modes = False

    def _on_pick_entity_change(self, val, _old):
        if self._updating_pick_modes:
            return
        self._updating_pick_modes = True
        if val:
            self.pick_solid.value = False
        self._update_pick_modes()
        self._updating_pick_modes = False

    def _update_pick_modes(self):
        solid = self.pick_solid.value
        faces = self.pick_faces.value or solid
        edges = self.pick_edges.value
        vertices = self.pick_vertices.value
        self.geo_renderer.faces._select_active = faces
        self.geo_renderer.edges._select_active = edges
        self.geo_renderer.vertices._select_active = vertices
        self.geo_renderer.vertices.active = vertices or self.show_vertices.value
        if hasattr(self.scene, '_select_buffer_valid'):
            self.scene._select_buffer_valid = False
        self.scene.render()


# Register with the component registry
from .registry import register_component
from .sections import GeometryOptionsSection, GeometrySelectionSection, ClippingSection

register_component(
    "geometry",
    icon="mdi-cube",
    component_class=GeometryComponent,
    sections=[GeometryOptionsSection, GeometrySelectionSection, ClippingSection],
)
