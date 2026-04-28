from ngapp.components import *


class FunctionOptionsSection(QExpansionItem):
    def __init__(self, comp):
        self.comp = comp
        self.wireframe_visible = QCheckbox(
            ui_label="Wireframe Visible",
            ui_model_value=comp.settings.get("wireframe_visible", True),
        )
        reset_camera = QBtn(
            ui_icon="mdi-refresh",
            ui_label="Reset Camera",
            ui_flat=True,
            ui_color="primary",
        )
        reset_camera.on_click(self.reset_camera)
        self.wireframe_visible.on_update_model_value(self.toggle_wireframe)
        items = [reset_camera, self.wireframe_visible]
        if comp.draw_surf:
            self.surface_solution_visible = QCheckbox(
                ui_label="Surface Solution Visible",
                ui_model_value=comp.settings.get("elements2d_visible", True),
            )
            self.surface_solution_visible.on_update_model_value(
                self.toggle_surface_solution
            )
            items.append(self.surface_solution_visible)
        if comp.mesh.dim == 3:
            self.clipping_plane_visible = QCheckbox(
                ui_label="Clipping Function",
                ui_model_value=comp.settings.get("clipping_visible", True),
            )
            items.append(self.clipping_plane_visible)
            self.clipping_plane_visible.on_update_model_value(
                self.toggle_clipping_function
            )
        if self.comp.contact is not None:
            self.contact_visible = QCheckbox(
                ui_label="Contact Pairs",
                ui_model_value=comp.settings.get("contact_enabled", True),
            )
            self.contact_visible.on_update_model_value(self.toggle_contact_pairs)
            items.append(self.contact_visible)

        draw_mesh = QBtn(
            ui_icon="mdi-vector-triangle",
            ui_label="Draw Mesh",
            ui_flat=True,
            ui_color="primary",
        )
        draw_mesh.on_click(self._draw_mesh)
        items.append(draw_mesh)

        super().__init__(
            *items,
            ui_icon="mdi-cog-outline",
            ui_label="Options",
        )

    def toggle_wireframe(self, event):
        self.comp.wireframe.active = self.wireframe_visible.ui_model_value
        self.comp.wgpu.scene.render()

    def toggle_clipping_function(self, event):
        self.comp.clippingcf.active = self.clipping_plane_visible.ui_model_value
        self.comp.wgpu.scene.render()

    def toggle_surface_solution(self, event):
        self.comp.settings.set(
            "elements2d_visible", self.surface_solution_visible.ui_model_value
        )
        self.comp.elements2d.active = self.surface_solution_visible.ui_model_value
        self.comp.wgpu.scene.render()

    def toggle_contact_pairs(self, event):
        enabled = self.contact_visible.ui_model_value
        self.comp.settings.set("contact_enabled", enabled)
        self.comp.contact_pairs.active = enabled
        self.comp.wgpu.scene.render()

    def reset_camera(self, event):
        pmin, pmax = self.comp.wgpu.scene.bounding_box
        camera = self.comp.wgpu.scene.options.camera
        camera.reset(pmin, pmax)
        self.comp.wgpu.scene.render()

    def _draw_mesh(self, *args):
        from ngsolve_gui.mesh import MeshComponent

        comp = self.comp
        comp.app_data.add_tab(
            "Mesh_" + comp.name, MeshComponent, {"obj": comp.mesh}, comp.app_data
        )
