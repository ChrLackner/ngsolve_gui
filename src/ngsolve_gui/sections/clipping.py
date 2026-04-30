from ngapp.components import *
import math


class ClippingSection(QExpansionItem):
    def __init__(self, comp):
        self.comp = comp
        if hasattr(comp, "mesh") and comp.mesh.dim < 3:
            raise ValueError("Clipping not applicable for 2D")
        use_global = QCheckbox(
            "Use Global Clipping Plane",
            ui_model_value=comp.use_global_clipping.value,
        )
        bind(comp.use_global_clipping, use_global)
        self.enable = enable = QCheckbox(
            "Enable Clipping",
            ui_model_value=comp.clipping.mode != comp.clipping.Mode.DISABLED,
        )
        bind(comp.clipping_enabled, enable)
        clip = comp.clipping
        debounce_time = 300
        self.cx = QInput(
            ui_label="x",
            ui_model_value=clip.center[0],
            ui_debounce=debounce_time,
            ui_dense=True,
        )
        self.cx.on_update_model_value(self.set_cx)
        self.cy = QInput(
            ui_label="y",
            ui_model_value=clip.center[1],
            ui_debounce=debounce_time,
            ui_dense=True,
        )
        self.cy.on_update_model_value(self.set_cy)
        self.cz = QInput(
            ui_label="z",
            ui_model_value=clip.center[2],
            ui_debounce=debounce_time,
            ui_dense=True,
        )
        self.cz.on_update_model_value(self.set_cz)
        self.dx = QSlider(
            ui_model_value=clip.normal[0],
            ui_min=-1,
            ui_max=1,
            ui_step=0.1,
            ui_vertical=True,
            ui_style="height: 50px;",
        )
        self.dx.on(
            "dblclick",
            lambda e: (setattr(self.dx, "ui_model_value", 0), self.set_nx(0)),
        )
        self.dx.on_update_model_value(self.set_nx)
        self.dy = QSlider(
            ui_model_value=clip.normal[1],
            ui_min=-1,
            ui_max=1,
            ui_step=0.1,
            ui_vertical=True,
            ui_style="height: 50px;",
        )
        self.dy.on(
            "dblclick",
            lambda e: (setattr(self.dy, "ui_model_value", 0), self.set_ny(0)),
        )
        self.dy.on_update_model_value(self.set_ny)
        self.dz = QSlider(
            ui_model_value=clip.normal[2],
            ui_min=-1,
            ui_max=1,
            ui_step=0.1,
            ui_vertical=True,
            ui_style="height: 50px;",
        )
        self.dz.on(
            "dblclick",
            lambda e: (setattr(self.dz, "ui_model_value", 0), self.set_nz(0)),
        )
        self.dz.on_update_model_value(self.set_nz)

        self.offset = QSlider(ui_min=-1, ui_max=1, ui_step=0.01, ui_model_value=0.0)
        self.offset.on("dblclick", lambda e: self.set_offset(0))
        self.slider_badge = QBadge(
            f"Offset value: {int(self.offset.ui_model_value*100)}% of Bounding Box",
            ui_color="secondary",
        )
        self.offset.on_update_model_value(self.set_offset)
        offset_g = Row(
            Col(self.slider_badge, self.offset),
            ui_style="align-items: flex-start; padding-top: 10px;",
        )

        center = Row(
            Col(Div("Center")),
            Col(self.cx),
            Col(self.cy),
            Col(self.cz),
            ui_style="align-items: center;",
        )
        direction = Row(
            Col(Div("Direction")),
            Col(self.dx),
            Col(self.dy),
            Col(self.dz),
            ui_style="align-items: center;",
        )

        super().__init__(
            use_global,
            enable,
            center,
            direction,
            offset_g,
            ui_icon="mdi-cube-off-outline",
            ui_label="Clipping",
        )
        self.on_mounted(self.update_fields)

    def get_offset_factor(self):
        try:
            bounding_box = self.comp.wgpu.scene.bounding_box
        except Exception as e:
            print(e)
            bounding_box = ((0, 0, 0), (1, 1, 1))
        bb_diag = [bounding_box[1][i] - bounding_box[0][i] for i in range(3)]
        return math.sqrt(sum([d**2 for d in bb_diag])) / 2.0

    def update_fields(self):
        value = self.comp.clipping.offset / self.get_offset_factor()
        self.offset.ui_model_value = value
        self.slider_badge.ui_children = [
            f"Offset value: {int(value*100)}% of Bounding Box"
        ]
        self.enable.ui_model_value = (
            self.comp.clipping.mode != self.comp.clipping.Mode.DISABLED
        )
        self.cx.ui_model_value = self.comp.clipping.center[0]
        self.cy.ui_model_value = self.comp.clipping.center[1]
        self.cz.ui_model_value = self.comp.clipping.center[2]
        self.dx.ui_model_value = self.comp.clipping.normal[0]
        self.dy.ui_model_value = self.comp.clipping.normal[1]
        self.dz.ui_model_value = self.comp.clipping.normal[2]

    def enable_clipping(self, event):
        self.comp.clipping_enabled.value = event.value

    def set_global_clipping(self, event):
        self.comp.use_global_clipping.value = event.value

    def set_offset(self, event):
        if isinstance(event, int):
            value = event
            self.offset.ui_model_value = value
        else:
            value = event.value
        self.slider_badge.ui_children = [
            f"Offset value: {int(value*100)}% of Bounding Box"
        ]
        self.comp.clipping.set_offset(value * self.get_offset_factor())
        self.comp.wgpu.scene.render()

    def set_cx(self, event):
        try:
            value = float(event.value)
        except:
            return
        self.comp.clipping.set_x_value(value)
        self.comp.wgpu.scene.render()

    def set_cy(self, event):
        try:
            value = float(event.value)
        except:
            return
        self.comp.clipping.set_y_value(value)
        self.comp.wgpu.scene.render()

    def set_cz(self, event):
        try:
            value = float(event.value)
        except:
            return
        self.comp.clipping.set_z_value(value)
        self.comp.wgpu.scene.render()

    def set_nx(self, event):
        if isinstance(event, int):
            value = event
        else:
            try:
                value = float(event.value)
            except:
                return
        self.comp.clipping.set_nx_value(value)
        self.comp.wgpu.scene.render()

    def set_ny(self, event):
        if isinstance(event, int):
            value = event
        else:
            try:
                value = float(event.value)
            except:
                return
        self.comp.clipping.set_ny_value(value)
        self.comp.wgpu.scene.render()

    def set_nz(self, event):
        if isinstance(event, int):
            value = event
        else:
            try:
                value = float(event.value)
            except:
                return
        self.comp.clipping.set_nz_value(value)
        self.comp.wgpu.scene.render()
