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
        colors = self.geo_renderer.faces.colors
        for i in range(len(colors) // 4):
            colors[i * 4 + 3] = 1.0
        self.geo_renderer.faces.set_colors(colors)
        colors = self.geo_renderer.edges.colors
        for i in range(len(colors) // 4):
            colors[i * 4 + 3] = 1.0
        self.geo_renderer.edges.set_colors(colors)
        self.wgpu.scene.render()

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
            if self.selected[0] == "face":
                face = self.geo.faces[self.selected[1]]
                face.maxh = value if value is not None else 1e99
            elif self.selected[0] == "edge":
                edge = self.geo.edges[self.selected[1]]
                edge.maxh = value if value is not None else 1e99
        except ValueError as e:
            if self._selection_section:
                self._selection_section.meshsize_input.ui_error_message = str(e)
                self._selection_section.meshsize_input.ui_error = True

    def change_name(self, event):
        value = event.value
        try:
            if value == "":
                value = None
            if self.selected[0] == "face":
                face = self.geo.faces[self.selected[1]]
                face.name = value
            elif self.selected[0] == "edge":
                edge = self.geo.edges[self.selected[1]]
                edge.name = value
            if self._selection_section:
                self._selection_section.name_input.ui_error = False
        except ValueError as e:
            if self._selection_section:
                self._selection_section.name_input.ui_error_message = str(e)
                self._selection_section.name_input.ui_error = True

    def _hide_selected_shape(self, event=None):
        if self.selected[0] == "face":
            colors = self.geo_renderer.faces.colors
            colors[self.selected[1] * 4 + 3] = 0.0
            self.geo_renderer.faces.set_colors(colors)
        elif self.selected[0] == "edge":
            colors = self.geo_renderer.edges.colors
            colors[self.selected[1] * 4 + 3] = 0.0
            self.geo_renderer.edges.set_colors(colors)
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
            pos_str = f"({pos[0]:.4g}, {pos[1]:.4g}, {pos[2]:.4g})"
            hl = self._highlight

            if self.pick_solid.value and result.geo_type == 2:
                solid_idx = int(self.geo_renderer.faces._solid_ids[result.index])
                solid_name = ""
                try:
                    solid_name = list(self.geo.shape.solids)[solid_idx].name or ""
                except Exception:
                    pass
                name_part = f"  {solid_name}" if solid_name else ""
                text = f"Solid {solid_idx}{name_part}  {pos_str}"
                hl.renderer_id = event.obj_id
                hl.element_id = 0xFFFFFFFF
                hl.region_index = 0xFFFFFFFF
                hl.solid_index = solid_idx
            else:
                name_part = f"  {result.name}" if result.name else ""
                text = f"{result.kind_label} {result.index}{name_part}  {pos_str}"
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
        else:
            kind, idx = self._selected_items[-1]
            self.selected = (kind, idx)
            self._selection_section.update_selection(kind, idx)

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
