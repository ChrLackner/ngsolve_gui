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
        super().__init__(name, data, app_data)

    def update(self, title, mesh, settings):
        self.title = title
        if self.mesh == mesh:
            return
        self.mesh = mesh
        self.settings = settings
        self.draw()

    def set_wireframe_visible(self, event):
        self.wireframe.active = event.value
        self.settings.set("wireframe_visible", event.value)
        self.scene.render()

    def set_elements1d_visible(self, event):
        self.settings.set("elements1d_visible", event.value)
        self.elements1d.active = event.value
        self.scene.render()

    def set_elements2d_visible(self, event):
        self.elements2d.active = event.value
        self.settings.set("elements2d_visible", event.value)
        self.scene.render()

    def set_elements3d_visible(self, event):
        self.settings.set("elements3d_visible", event.value)
        if self.elements3d is None:
            self.draw()
        self.elements3d.active = event.value
        self.scene.render()

    def set_shrink(self, event):
        self.mdata.shrink = event.value
        self.settings.set("shrink", event.value)
        if self.elements3d is not None:
            self.elements3d.shrink = event.value
        self.wgpu.scene.render()

    def set_mesh_curvature_enabled(self, event):
        if event.value != self.settings.get("mesh_curvature_enabled", False):
            order = self.settings.get("mesh_curvature_order", 2)
            if order > 3:
                subdiv = (order + 2) // 3 + 1
            elif order > 1:
                subdiv = 3
            else:
                subdiv = 1
            self.mdata.subdivision = subdiv
            self.mdata.set_needs_update()
        self.settings.set("mesh_curvature_enabled", event.value)
        self.draw()

    def set_mesh_curvature_order(self, event):
        try:
            if event.value != self.settings.get("mesh_curvature_order", 2):
                self.mdata.set_needs_update()
            self.settings.set("mesh_curvature_order", int(event.value))
        except (TypeError, ValueError):
            pass
        self.draw()

    # -- Keybinding support ---------------------------------------------

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
        self.wireframe.active = not self.wireframe.active
        self.settings.set("wireframe_visible", self.wireframe.active)
        self.wgpu.scene.render()

    def toggle_elements_1d(self):
        self.elements1d.active = not self.elements1d.active
        self.settings.set("elements1d_visible", self.elements1d.active)
        self.wgpu.scene.render()

    def toggle_elements_2d(self):
        self.elements2d.active = not self.elements2d.active
        self.settings.set("elements2d_visible", self.elements2d.active)
        self.wgpu.scene.render()

    def toggle_elements_3d(self):
        if self.elements3d is None:
            self.draw()
        self.elements3d.active = not self.elements3d.active
        self.settings.set("elements3d_visible", self.elements3d.active)
        self.wgpu.scene.render()

    def draw(self):
        curve_enabled = self.settings.get("mesh_curvature_enabled", False)
        curve_order = int(self.settings.get("mesh_curvature_order", 2))
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
        self.wireframe.active = self.settings.get("wireframe_visible", True)
        self.elements1d = MeshSegments(self.mdata, clipping=self.clipping)
        self.elements1d.active = self.settings.get("elements1d_visible", False)
        self.elements2d = MeshElements2d(self.mdata, clipping=self.clipping)
        self.elements2d.active = self.settings.get("elements2d_visible", True)
        if self.settings.get("elements3d_visible", False):
            self.elements3d = MeshElements3d(self.mdata, clipping=self.clipping)
            self.elements3d.shrink = self.settings.get("shrink", 1.0)
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
