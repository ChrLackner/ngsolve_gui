from ngapp.components import *


class ClippingSettings(QCard):
    def __init__(self, comp):
        self.comp = comp
        use_global = QCheckbox(
            "Use Global Clipping Plane",
            ui_model_value=comp.settings.get("use_global_clipping", True),
        )
        use_global.on_update_model_value(self.set_global_clipping)
        self.enable = enable = QCheckbox(
            "Enable Clipping",
            ui_model_value=comp.clipping.mode != comp.clipping.Mode.DISABLED,
        )
        enable.on_update_model_value(self.enable_clipping)
        clip = comp.clipping
        debounce_time = 300
        self.cx = QInput(
            ui_label="x",
            ui_model_value=clip.center[0],
            ui_debounce=debounce_time,
            ui_style="width: 100px; padding: 0px 10px;",
        )
        self.cx.on_update_model_value(self.set_cx)
        self.cy = QInput(
            ui_label="y",
            ui_model_value=clip.center[1],
            ui_debounce=debounce_time,
            ui_style="width: 100px; padding: 0px 10px;",
        )
        self.cy.on_update_model_value(self.set_cy)
        self.cz = QInput(
            ui_label="z",
            ui_model_value=clip.center[2],
            ui_debounce=debounce_time,
            ui_style="width: 100px; padding: 0px 10px;",
        )
        self.cz.on_update_model_value(self.set_cz)
        self.dx = QInput(
            ui_label="x",
            ui_model_value=clip.normal[0],
            ui_debounce=debounce_time,
            ui_style="width: 100px; padding: 0px 10px;",
        )
        self.dx.on_update_model_value(self.set_nx)
        self.dy = QInput(
            ui_label="y",
            ui_model_value=clip.normal[1],
            ui_debounce=debounce_time,
            ui_style="width: 100px; padding: 0px 10px;",
        )
        self.dy.on_update_model_value(self.set_ny)
        self.dz = QInput(
            ui_label="z",
            ui_model_value=clip.normal[2],
            ui_debounce=debounce_time,
            ui_style="width: 100px; padding: 0px 10px;",
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
        settings = QCardSection(
            Row(use_global), Row(enable), center, direction, offset_g
        )

        super().__init__(
            QCardSection(Heading("Clipping Settings", 5)), settings, ui_flat=True
        )
        self.on_mounted(self.update_fields)

    def get_offset_factor(self):
        try:
            bounding_box = self.comp.wgpu.scene.bounding_box
            print("found bounding box = ", bounding_box)
        except Exception as e:
            print(e)
            bounding_box = ((0, 0, 0), (1, 1, 1))
            print("default bounding_box")
        bb_diag = np.array(bounding_box[1]) - np.array(bounding_box[0])
        return np.linalg.norm(bb_diag) / 2.0

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
        self.comp.settings.set("clipping_enabled", event.value)
        self.comp.clipping.enable_clipping(event.value)
        self.comp.wgpu.scene.render()

    def set_global_clipping(self, event):
        self.comp.settings.set("use_global_clipping", event.value)

    def set_offset(self, event):
        if isinstance(event, int):
            value = event
            self.offset.ui_model_value = value
        else:
            value = event.value
        self.slider_badge.ui_children = [
            f"Offset value: {int(value*100)}% of Bounding Box"
        ]
        print("offset factor = ", self.get_offset_factor())
        self.comp.clipping.set_offset(value * self.get_offset_factor())
        self.comp.wgpu.scene.render()

    def set_cx(self, event):
        print("set cx")
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
        try:
            value = float(event.value)
        except:
            return
        print("set nx = ", value)
        self.comp.clipping.set_nx_value(value)
        self.comp.wgpu.scene.render()

    def set_ny(self, event):
        try:
            value = float(event.value)
        except:
            return
        self.comp.clipping.set_ny_value(value)
        self.comp.wgpu.scene.render()

    def set_nz(self, event):
        try:
            value = float(event.value)
        except:
            return
        self.comp.clipping.set_nz_value(value)
        self.comp.wgpu.scene.render()
