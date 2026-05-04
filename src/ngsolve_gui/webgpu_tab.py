from ngapp.components import *
from ngapp.utils import UserSettings
from webgpu import Scene, CoordinateAxes, NavigationCube

_usersettings = UserSettings(app_id="NGSolve GUI")
from webgpu import Scene
from ngsolve_webgpu.pick import MeshPickResult, HighlightUniforms
from .pick_overlay import PickOverlay


class WebgpuTab(Div):
    def __init__(self, name, data, app_data):
        self.name = name
        self._redraw_needed = False
        self.data = data
        self.app_data = app_data
        self.wgpu = WebgpuComponent()
        self.wgpu.ui_style = "width: 100%; height: 100%;"
        self.icon = "mdi-vector-triangle"

        # -- Gizmo visibility (persisted in user settings) --
        self.axes_visible = Observable(
            _usersettings.get("axes_visible", True), "axes_visible"
        )
        self.navcube_visible = Observable(
            _usersettings.get("navcube_visible", False), "navcube_visible"
        )

        self.coordinate_axes = CoordinateAxes()
        self.coordinate_axes.active = self.axes_visible.value
        self.navigation_cube = NavigationCube()
        self.navigation_cube.active = self.navcube_visible.value

        # Observable for clipping state
        if not hasattr(self, 'clipping_enabled'):
            tab = app_data.get_tab(name)
            saved = tab.get("settings", {}) if tab else {}
            self.clipping_enabled = Observable(
                saved.get("clipping_enabled", False), "clipping_enabled"
            )
            self.use_global_clipping = Observable(
                saved.get("use_global_clipping", True), "use_global_clipping"
            )

        self.reset_camera_btn = QBtn(
            QTooltip("Reset Camera"),
            ui_icon="mdi-refresh",
            ui_color="secondary",
            ui_style="position: absolute; top: 10px; right: 10px;",
            ui_fab=True,
            ui_flat=True,
        )
        self.reset_camera_btn.on_click(self.reset_camera)

        self.pick_overlay = PickOverlay()

        super().__init__(
            self.wgpu,
            self.reset_camera_btn,
            self.pick_overlay,
            ui_style="position: relative; width: 100%; height: 100%;",
        )

        self.draw()
        self.reset_camera()

        # Enable selection on right-click (needed for nav cube)
        def _on_click_select(event):
            if event["button"] == 2:
                self.scene.select(event["canvasX"], event["canvasY"])
        self.scene.input_handler.on_click(_on_click_select)

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

        # Wire gizmo visibility
        self.axes_visible.on_change(self._apply_axes_visible)
        self.navcube_visible.on_change(self._apply_navcube_visible)

        # Wire nav cube face selection
        self.navigation_cube.faces.on_select(self._on_navcube_select)

        # Wire clipping observable after scene is ready
        self.clipping_enabled.on_change(self._apply_clipping_enabled)

        def redraw_if_needed():
            if self._redraw_needed:
                self.redraw()

        self.on_mounted(redraw_if_needed)

    # -- Gizmo visibility handlers --

    def _apply_axes_visible(self, val, _old):
        self.coordinate_axes.active = val
        _usersettings.set("axes_visible", val)
        self.scene.render()

    def _apply_navcube_visible(self, val, _old):
        self.navigation_cube.active = val
        _usersettings.set("navcube_visible", val)
        self.scene.render()

    def toggle_axes(self):
        self.axes_visible.toggle()

    def toggle_navcube(self):
        self.navcube_visible.toggle()

    # -- Nav cube click-to-view --

    def _on_navcube_select(self, event):
        face_id = event.uint32[1]
        views = NavigationCube.FACE_VIEWS
        if face_id >= len(views):
            return
        view = views[face_id]
        camera = self.scene.options.camera
        if view.endswith("_flip"):
            getattr(camera, f"reset_{view[:-5]}")(flip=True)
        else:
            getattr(camera, f"reset_{view}")()
        self.scene.render()

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

    # -- Picking support ---------------------------------------------------

    def setup_picking(self, renderers, mesh):
        """Register hover picking on the given renderers.

        Call this at the end of draw() in subclasses.
        Args:
            renderers: list of (Renderer, kind) tuples where kind is
                       "surface", "volume", or "clipping"
            mesh: the ngsolve/netgen mesh for interpreting results
        """
        self._pick_mesh = mesh
        self._pick_renderers = renderers
        self._highlight = HighlightUniforms()
        self.scene.options.add_bindings(self._highlight)
        for r, kind in renderers:
            r.on_select(lambda ev, k=kind: self._on_pick_select(ev, k))
        self.scene.on_click_background(self._on_pick_background)
        self.scene.input_handler.on_mousemove(self._on_pick_hover, shift=None)
        self.scene.input_handler.on_mouseout(self._on_pick_out, shift=None)

    def _on_pick_hover(self, ev):
        if ev["buttons"] == 0 and self.scene.canvas is not None:
            self._shift_hover = ev.get("shiftKey", False)
            self.scene.select(ev["canvasX"], ev["canvasY"])

    def _on_pick_out(self, ev):
        if not hasattr(self, '_pick_mesh'):
            return
        self._clear_highlight()
        self.pick_overlay.hide()
        self.scene.render()

    def _on_pick_background(self, ev):
        self._clear_highlight()
        self.pick_overlay.hide()
        self.scene._render_highlight()

    def _on_pick_select(self, event, kind="surface"):
        try:
            result = MeshPickResult(event, self._pick_mesh, self.scene.options.camera, kind=kind)
            text = self._format_pick_result(result)
            if text:
                self.pick_overlay.show_text(text)
            else:
                self.pick_overlay.hide()
            hl = self._highlight
            hl.renderer_id = event.obj_id
            if getattr(self, '_shift_hover', False):
                # Shift+hover: highlight entire region
                hl.element_id = 0xFFFFFFFF
                hl.region_index = result.region_index
            else:
                # Normal hover: highlight single element
                hl.element_id = result.element_nr
                hl.region_index = 0xFFFFFFFF
            hl.update_buffer()
            self.scene._render_highlight()
        except Exception:
            self.pick_overlay.hide()

    def _clear_highlight(self):
        hl = self._highlight
        hl.renderer_id = 0
        hl.element_id = 0xFFFFFFFF
        hl.region_index = 0xFFFFFFFF
        hl.update_buffer()



    def _format_pick_result(self, result):
        """Format pick result for display. Override in subclasses."""
        pos = result.world_pos
        return (
            f"{result.kind_label} El {result.element_nr}  {result.region_name}  "
            f"({pos[0]:.4g}, {pos[1]:.4g}, {pos[2]:.4g})"
        )

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
            (
                "v",
                "View",
                [
                    ("x", lambda: self.set_view("yz"), "View from X (YZ plane)"),
                    ("y", lambda: self.set_view("xz"), "View from Y (XZ plane)"),
                    ("z", lambda: self.set_view("xy"), "View from Z (XY plane)"),
                    ("r", self.reset_camera, "Reset camera"),
                ],
            ),
        ]
        return {"flat": flat, "modes": modes}

    def _gizmo_show_bindings(self):
        """Return show-mode bindings for gizmo toggles. Subclasses append to their 'Show' mode."""
        return [
            ("a", self.toggle_axes, "Toggle axes"),
            ("n", self.toggle_navcube, "Toggle nav cube"),
        ]

    def set_view(self, plane):
        """Set camera to a standard view (``"xy"``, ``"xz"``, or ``"yz"``)."""
        camera = self.scene.options.camera
        getattr(camera, f"reset_{plane}")()
        self.scene.render()

    def _apply_clipping_enabled(self, val, _old):
        self.clipping.enable_clipping(val)
        self.wgpu.scene.render()

    def toggle_clipping(self):
        self.clipping_enabled.toggle()

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
            self.clipping_enabled.value = True
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
