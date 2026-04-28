from ngapp.components import *


class VectorSection(QExpansionItem):
    def __init__(self, comp):
        self.comp = comp
        if comp.cf.dim <= 1:
            raise ValueError("Vector settings not applicable for scalar functions")
        options = ["Norm"] + [str(i) for i in range(1, comp.cf.dim + 1)]
        comps = []
        self.color_component = QSelect(
            ui_options=options,
            ui_model_value=options[0],
            ui_label="Color Component",
            ui_dense=True,
        )
        comps.append(self.color_component)
        self.color_component.on_update_model_value(self.update_color_component)
        if comp.mesh.dim == 3 and comp.cf.dim == 3:
            self.clipping_vectors = QCheckbox(
                ui_label="Show Clipping Vectors",
                ui_model_value=comp.settings.get("clipping_vectors", False),
            )
            self.clipping_vectors.on_update_model_value(self.update_clipping_vectors)
            comps.append(self.clipping_vectors)
        if (
            comp.mesh.dim == 2
            and comp.cf.dim == 2
            or comp.mesh.dim == 3
            and comp.cf.dim == 3
        ):
            self.surf_vectors = QCheckbox(
                ui_label="Show Surface Vectors",
                ui_model_value=comp.settings.get("surface_vectors", False),
            )
            self.surf_vectors.on_update_model_value(self.update_surface_vectors)
            comps.append(self.surf_vectors)
        grid_val = comp.settings.get("vector_grid_size", 200)
        self.grid_size = QInput(
            ui_label="Grid Size",
            ui_type="number",
            ui_model_value=grid_val,
            ui_dense=True,
            ui_debounce=500,
        )
        minus_btn = QBtn(
            ui_icon="mdi-minus",
            ui_flat=True,
            ui_dense=True,
            ui_round=True,
            ui_size="sm",
        )
        plus_btn = QBtn(
            ui_icon="mdi-plus", ui_flat=True, ui_dense=True, ui_round=True, ui_size="sm"
        )
        minus_btn.on_click(lambda e=None: self._step_grid(-50))
        plus_btn.on_click(lambda e=None: self._step_grid(50))
        self.grid_size.ui_slots["prepend"] = [minus_btn]
        self.grid_size.ui_slots["append"] = [plus_btn]
        self.grid_size.on_update_model_value(self.update_grid_size)
        comps.append(self.grid_size)

        super().__init__(
            *comps,
            ui_icon="mdi-arrow-top-right-thin",
            ui_label="Vector Settings",
        )

    def update_clipping_vectors(self, event):
        self.comp.clipping_vectors.active = self.clipping_vectors.ui_model_value
        self.comp.settings.set("clipping_vectors", self.clipping_vectors.ui_model_value)
        self.comp.wgpu.scene.render()

    def update_surface_vectors(self, event):
        self.comp.surface_vectors.active = self.surf_vectors.ui_model_value
        self.comp.settings.set("surface_vectors", self.surf_vectors.ui_model_value)
        self.comp.wgpu.scene.render()

    def _step_grid(self, delta):
        try:
            val = int(float(self.grid_size.ui_model_value or 200))
        except (ValueError, TypeError):
            val = 200
        val = max(1, val + delta)
        self.grid_size.ui_model_value = val
        from ngapp.components import Event

        self.update_grid_size(
            Event(name="update:modelValue", component=self.grid_size, value=val)
        )

    def update_grid_size(self, event):
        try:
            grid_size = int(float(event.value))
        except (ValueError, TypeError):
            return
        if grid_size < 1:
            return
        self.comp.settings.set("vector_grid_size", grid_size)
        if self.comp.clipping_vectors is not None:
            self.comp.clipping_vectors.set_grid_size(grid_size)
            self.comp.clipping_vectors.set_needs_update()
        if self.comp.surface_vectors is not None:
            self.comp.surface_vectors.set_grid_size(grid_size)
            self.comp.surface_vectors.set_needs_update()
        self.comp.wgpu.scene.render()

    def update_color_component(self, event):
        index = self.color_component.ui_options.index(
            self.color_component.ui_model_value
        )
        comp = self.comp
        if comp.elements2d is not None:
            comp.elements2d.set_component(index - 1)
        if comp.clippingcf is not None:
            comp.clippingcf.set_component(index - 1)
        comp.colorbar.set_needs_update()
        comp.wgpu.scene.render()
