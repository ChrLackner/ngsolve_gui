from ngapp.components import *

import ngsolve as ngs
from ngsolve_webgpu.mesh import *
from webgpu.labels import Labels

from .webgpu_tab import WebgpuTab
import netgen.occ as ngocc


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
        self.el2d_bitarray = data.get("el2d_bitarray", None)
        self.el3d_bitarray = data.get("el3d_bitarray", None)

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
        self.shrink_value = Observable(
            saved.get("shrink", 1.0), "shrink"
        )
        self.mesh_curvature_enabled = Observable(
            saved.get("mesh_curvature_enabled", False), "mesh_curvature_enabled"
        )
        self.mesh_curvature_order = Observable(
            saved.get("mesh_curvature_order", 2), "mesh_curvature_order"
        )
        self.edge_colors = Observable(
            saved.get("edge_colors", {}), "edge_colors"
        )

        super().__init__(name, data, app_data)

        # -- Wire GPU side-effects after draw() has created render objects --
        self.wireframe_visible.on_change(self._apply_wireframe)
        self.elements1d_visible.on_change(self._apply_elements1d)
        self.elements2d_visible.on_change(self._apply_elements2d)
        self.elements3d_visible.on_change(self._apply_elements3d)
        self.shrink_value.on_change(self._apply_shrink)
        self.mesh_curvature_enabled.on_change(self._apply_curvature)
        self.mesh_curvature_order.on_change(self._apply_curvature_order)

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
            self.draw()
        self.elements3d.active = val
        self.wgpu.scene.render()

    def _apply_shrink(self, val, _old):
        self.mdata.shrink = val
        if self.elements3d is not None:
            self.elements3d.shrink = val
        self.wgpu.scene.render()

    def _apply_curvature(self, val, _old):
        order = self.mesh_curvature_order.value
        if order > 3:
            subdiv = (order + 2) // 3 + 1
        elif order > 1:
            subdiv = 3
        else:
            subdiv = 1
        self.mdata.subdivision = subdiv
        self.mdata.set_needs_update()
        self.draw()

    def _apply_curvature_order(self, val, _old):
        self.mdata.set_needs_update()
        self.draw()

    # -- Keybinding support -------------------------------------------------

    def get_keybindings(self):
        kb = super().get_keybindings()
        show = [
            ("w", self.toggle_wireframe, "Toggle wireframe"),
            ("2", self.toggle_elements_2d, "Toggle elements 2D"),
            ("1", self.toggle_elements_1d, "Toggle elements 1D"),
        ]
        if self.mesh.dim == 3:
            show.append(("3", self.toggle_elements_3d, "Toggle elements 3D"))
        kb["flat"].append(("w", self.toggle_wireframe, "Toggle wireframe", "General"))
        kb["modes"].append(("s", "Show", show))
        if self.mesh.dim == 3:
            kb["modes"].append(("c", "Clipping", self._clipping_mode_bindings()))
        return kb

    def toggle_wireframe(self):
        self.wireframe_visible.toggle()

    def toggle_elements_1d(self):
        self.elements1d_visible.toggle()

    def toggle_elements_2d(self):
        self.elements2d_visible.toggle()

    def toggle_elements_3d(self):
        self.elements3d_visible.toggle()

    def update(self, title, mesh, settings):
        self.title = title
        if self.mesh == mesh:
            return
        self.mesh = mesh
        self.draw()

    def draw(self):
        curve_enabled = self.mesh_curvature_enabled.value
        curve_order = int(self.mesh_curvature_order.value)
        if curve_enabled:
            self.mesh.Curve(curve_order)
        else:
            self.mesh.Curve(1)

        if self.el2d_bitarray is not None or self.el3d_bitarray is not None:
            self.mdata = MeshData(
                self.region_or_mesh,
                el2d_bitarray=self.el2d_bitarray,
                el3d_bitarray=self.el3d_bitarray,
            )
        else:
            self.mdata = self.app_data.get_mesh_gpu_data(self.region_or_mesh)
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
        self.elements2d = MeshElements2d(self.mdata, clipping=self.clipping)
        self.elements2d.active = self.elements2d_visible.value
        if self.elements3d_visible.value:
            self.elements3d = MeshElements3d(self.mdata, clipping=self.clipping)
            self.elements3d.shrink = self.shrink_value.value
        self.mesh_info = Labels(
            [
                f"VOL: {self.mesh.GetNE(ngs.VOL)} BND: {self.mesh.GetNE(ngs.BND)} CD2: {self.mesh.GetNE(ngs.BBND)} CD3: {self.mesh.GetNE(ngs.BBBND)}"
            ],
            [(-0.99, -0.99)],
            font_size=14,
        )

        render_objects = [
            obj
            for obj in [
                self.elements2d,
                self.wireframe,
                self.elements3d,
                self.elements1d,
                self.mesh_info,
            ]
            if obj is not None
        ]
        self.wgpu.draw(render_objects, camera=self.camera)


# Register with the component registry
from .registry import register_component
from .sections import MeshViewSection, MeshColorSection, ClippingSection

register_component(
    "mesh",
    icon="mdi-vector-triangle",
    component_class=MeshComponent,
    sections=[MeshViewSection, MeshColorSection, ClippingSection],
)
