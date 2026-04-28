from ngapp.components import *
from webgpu import Scene


class WebgpuTab(Div):
    def __init__(self, name, data, app_data):
        self.name = name
        self._redraw_needed = False
        self.data = data
        self.app_data = app_data
        self.wgpu = WebgpuComponent()
        self.wgpu.ui_style = "width: 100%; height: 100%;"
        self.icon = "mdi-vector-triangle"

        self.reset_camera_btn = QBtn(
            QTooltip("Reset Camera"),
            ui_icon="mdi-refresh",
            ui_color="secondary",
            ui_style="position: absolute; top: 10px; right: 10px;",
            ui_fab=True,
            ui_flat=True,
        )
        self.reset_camera_btn.on_click(self.reset_camera)

        super().__init__(
            self.wgpu, self.reset_camera_btn,
            ui_style="position: relative; width: 100%; height: 100%;",
        )

        self.draw()
        self.reset_camera()
        self.clipping.center = 0.5 * (
            self.scene.bounding_box[1] + self.scene.bounding_box[0]
        )
        if "clipping" in data:
            clipping = data["clipping"]
            if bool(clipping):
                self.clipping.mode = self.clipping.Mode.PLANE
            if isinstance(clipping, dict):
                if "normal" in clipping:
                    self.clipping.normal = clipping["normal"]
                if "center" in clipping:
                    self.clipping.center = clipping["center"]
                if "offset" in clipping:
                    self.clipping.offset = clipping["offset"]

        self.scene.input_handler.on_dblclick(self._on_dblclick, ctrl=True)
        self.scene.input_handler.on_drag(self._on_mousemove, ctrl=True)
        self.scene.input_handler.on_wheel(self._on_wheel, ctrl=True)

        def redraw_if_needed():
            if self._redraw_needed:
                self.redraw()
        self.on_mounted(redraw_if_needed)

    def redraw(self):
        self._redraw_needed = False
        self.wgpu.scene.redraw()

    def _on_dblclick(self, ev):
        scene = self.scene
        x = ev["canvasX"]
        y = ev["canvasY"]

        p = scene.get_position(x, y)
        clipping = self.clipping
        clipping.set_x_value(float(p[0]))
        clipping.set_y_value(float(p[1]))
        clipping.set_z_value(float(p[2]))
        clipping.set_offset(0)
        self.scene.render()

    def _on_mousemove(self, ev):
        clipping = self.clipping
        if ev["buttons"] & 2:
            offset = clipping.offset
            offset += ev["movementY"] * 0.00002
            clipping.set_offset(offset)
            self.scene.render()
        if ev["buttons"] & 1:
            import numpy.linalg

            transform = self.scene.options.camera.transform.copy()
            inv_normal_mat = transform._mat.copy()[:3, :3].T
            normal_mat = numpy.linalg.inv(inv_normal_mat)

            transform._mat = numpy.identity(4)
            transform._mat[:3, :3] = normal_mat
            s = 0.3
            transform.rotate(s * ev["movementY"], s * ev["movementX"])
            n = inv_normal_mat @ (transform._mat[:3, :3] @ clipping.normal)

            clipping.set_nx_value(float(n[0]))
            clipping.set_ny_value(float(n[1]))
            clipping.set_nz_value(float(n[2]))

            self.scene.render()

    def _on_wheel(self, ev):
        clipping = self.clipping
        offset = clipping.offset
        offset += ev["deltaY"] * 0.0008
        clipping.set_offset(offset)
        self.scene.render()

    @property
    def scene(self) -> Scene:
        return self.wgpu.scene

    def reset_camera(self):
        if self.scene is not None:
            pmin, pmax = self.scene.bounding_box
            camera = self.scene.options.camera
            camera.reset(pmin, pmax)
            self.scene.render()

    @property
    def settings(self):
        return self.app_data.get_settings(self.name)

    @property
    def clipping(self):
        return self.app_data.clipping

    @property
    def camera(self):
        return self.app_data.camera

    @property
    def title(self):
        return self.app_data.get_tab(self.name)["title"]

    # -- Keybinding support ---------------------------------------------

    def get_keybindings(self):
        """Return keybinding spec for this component.

        Subclasses should call ``super().get_keybindings()`` and extend the
        returned dict.  Format::

            {"flat": [(key, cb, desc, group), ...],
             "modes": [(trigger, name, [(key, cb, desc), ...]), ...]}
        """
        flat = [
            ("r", self.reset_camera, "Reset camera", "General"),
        ]
        modes = [
            ("v", "View", [
                ("x", lambda: self.set_view("yz"), "View from X (YZ plane)"),
                ("y", lambda: self.set_view("xz"), "View from Y (XZ plane)"),
                ("z", lambda: self.set_view("xy"), "View from Z (XY plane)"),
                ("r", self.reset_camera, "Reset camera"),
            ]),
        ]
        return {"flat": flat, "modes": modes}

    def set_view(self, plane):
        """Set camera to a standard view (``"xy"``, ``"xz"``, or ``"yz"``)."""
        camera = self.scene.options.camera
        getattr(camera, f"reset_{plane}")()
        self.scene.render()

    def toggle_clipping(self):
        clip = self.clipping
        if clip.mode == clip.Mode.DISABLED:
            clip.enable_clipping(True)
            self.settings.set("clipping_enabled", True)
        else:
            clip.enable_clipping(False)
            self.settings.set("clipping_enabled", False)
        self.wgpu.scene.render()

    def clip_along_axis(self, axis):
        clip = self.clipping
        normal = [0.0, 0.0, 0.0]
        current = [clip.normal[i] for i in range(3)]
        if abs(current[axis]) > 0.9:
            normal[axis] = -1.0 if current[axis] > 0 else 1.0
        else:
            normal[axis] = 1.0
        clip.set_nx_value(normal[0])
        clip.set_ny_value(normal[1])
        clip.set_nz_value(normal[2])
        clip.set_offset(0)
        if clip.mode == clip.Mode.DISABLED:
            clip.enable_clipping(True)
            self.settings.set("clipping_enabled", True)
        self.wgpu.scene.render()

    def reset_clipping(self):
        clip = self.clipping
        clip.set_nx_value(0.0)
        clip.set_ny_value(0.0)
        clip.set_nz_value(1.0)
        clip.set_offset(0)
        bb = self.wgpu.scene.bounding_box
        center = [0.5 * (bb[0][i] + bb[1][i]) for i in range(3)]
        clip.set_x_value(center[0])
        clip.set_y_value(center[1])
        clip.set_z_value(center[2])
        self.wgpu.scene.render()

    def _clipping_mode_bindings(self):
        """Return clipping mode bindings list. Used by 3D subclasses."""
        return [
            ("c", self.toggle_clipping, "Toggle clipping on/off"),
            ("x", lambda: self.clip_along_axis(0), "Clip along X axis"),
            ("y", lambda: self.clip_along_axis(1), "Clip along Y axis"),
            ("z", lambda: self.clip_along_axis(2), "Clip along Z axis"),
            ("r", self.reset_clipping, "Reset clipping"),
        ]

    def draw(self):
        raise NotImplementedError("draw method must be implemented in subclass")

    def set_component(self, comp):
        self.ui_children = [comp]
