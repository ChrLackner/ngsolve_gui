from ngapp.components import *
from ngapp.utils import UserSettings
from webgpu import Scene, CoordinateAxes, NavigationCube

_usersettings = UserSettings(app_id="NGSolve GUI")
from webgpu import Scene
from ngsolve_webgpu.pick import MeshPickResult
from webgpu.webgpu_api import Color
from webgpu.camera import Camera
from webgpu import Background
from webgpu.labels import Labels
import copy
import math

from .pick_overlay import PickOverlay
from .property_panel import PropertyPanelMixin
from .prop_widgets import Segmented
from .undo import UndoStack
from . import cerbsim_style as cb
from .cerbsim_style import overlay_tr, VIEWPORT_CLEAR, VIEWPORT_TEXT


def sync_default_viewport_clear():
    """Set the webgpu Canvas default clear color from the active theme so a new
    scene renders the right background on its very first frame (no flash)."""
    from webgpu.canvas import set_default_clear_color
    key = "dark" if cb._active_theme == "dark" else "light"
    set_default_clear_color(Color(*VIEWPORT_CLEAR[key], 1))


def _unregister_observer(camera, callback):
    """Drop *callback* from the camera's observers.

    ``Camera.unregister_observer`` compares with ``is``, which never matches a
    freshly bound method, so removing ``scene._on_camera_changed`` needs equality.
    """
    with camera._observers_lock:
        camera._observers = [cb for cb in camera._observers if cb != callback]


def _theme_scene(scene, bg_rgb, text_rgb):
    """Recursively theme a scene's overlays: Background backdrops match the
    viewport clear color; default-colored Labels (mesh stats, colorbar ticks)
    use the in-viewport text color. Per-label colored Labels are left alone."""
    def _walk(ro):
        if isinstance(ro, Background):
            ro.bg_color = bg_rgb
        elif isinstance(ro, Labels) and ro.colors is None:
            ro.text_color = text_rgb
        for sub in getattr(ro, "render_objects", []):
            _walk(sub)

    for ro in getattr(scene, "render_objects", []):
        _walk(ro)


class WebgpuTab(PropertyPanelMixin, Div):
    def __init__(self, name, data, app_data):
        self.name = name
        self.data = data
        self.app_data = app_data
        self.wgpu = WebgpuComponent()
        self.wgpu.ui_class = "fit"
        self.icon = "mdi-vector-triangle"

        self.undo_stack = UndoStack()
        self._last_pick = None

        tab = app_data.get_tab(name)
        saved_settings = tab.get("settings", {}) if tab else {}
        detached = bool(data.get("detached_camera", False)) if isinstance(data, dict) else False
        self.camera_shared = Observable(
            saved_settings.get("camera_shared", not detached), "camera_shared"
        )
        get_shared = getattr(app_data, "get_shared_camera", None)
        if get_shared is None:
            self._camera_group = None
            self._shared_camera = getattr(app_data, "camera", None) or Camera()
            fresh = True
        else:
            self._camera_group = self._resolve_camera_group()
            self._shared_camera, fresh = get_shared(self._camera_group)
        self._own_camera = None if self.camera_shared.value else Camera()
        self._camera_needs_fit = fresh or not self.camera_shared.value

        # -- Gizmo visibility (persisted in user settings) --
        self.axes_visible = Observable(
            _usersettings.get("axes_visible", True), "axes_visible"
        )
        self.navcube_visible = Observable(
            _usersettings.get("navcube_visible", False), "navcube_visible"
        )

        # -- Picking (persisted; geometry overrides via _picking_always_active) --
        if getattr(self, '_picking_always_active', False):
            self.picking_enabled = Observable(True, "picking_enabled")
        else:
            self.picking_enabled = Observable(
                _usersettings.get("picking_enabled", False), "picking_enabled"
            )

        self.coordinate_axes = CoordinateAxes()
        self.coordinate_axes.active = self.axes_visible.value
        self.navigation_cube = NavigationCube()
        self.navigation_cube.active = self.navcube_visible.value

        # Observable for clipping state
        if not hasattr(self, 'clipping_enabled'):
            self.clipping_enabled = Observable(
                saved_settings.get("clipping_enabled", False), "clipping_enabled"
            )
            self.use_global_clipping = Observable(
                saved_settings.get("use_global_clipping", True), "use_global_clipping"
            )

        self.pick_overlay = PickOverlay()

        # -- Floating viewport overlays (designer): tool dock, clip toolbar,
        #    camera cluster (reset + bookmarks), and the field probe panel. --
        self._probe_active = False
        self._probe_mode = "points"   # or "line"
        self._probe_points = []       # list of (np.array point, value-or-None)
        self._probe_screen = []       # parallel screen (x, y) for the line preview
        self._tool_dock = self._build_tool_dock()
        self._clip_toolbar = self._build_clip_toolbar()  # None if not 3D
        self._probe_panel = self._build_probe_panel()  # None if no field
        self._probe_preview = Div(ui_class=str(cb.vp_preview)) if self._supports_probe() else None
        self._legend = self._build_viewport_legend()  # None except for fields

        overlays = [self.wgpu, self._tool_dock, self.pick_overlay]
        if self._clip_toolbar is not None:
            overlays.insert(2, self._clip_toolbar)
        if self._legend is not None:
            overlays.append(self._legend)
        if self._probe_panel is not None:
            overlays.append(self._probe_preview)
            overlays.append(self._probe_panel)
        super().__init__(*overlays, ui_class="relative-position fit")

        self.draw()
        if self._camera_needs_fit:
            self.reset_camera()
        self._sync_clip_ui(self.clipping_enabled.value, None)
        self._sync_camera_link_ui(self.camera_shared.value, None)

        # Enable selection on right-click (needed for nav cube)
        def _on_click_select(event):
            if event["button"] == 2:
                try:
                    self.scene.select(event["canvasX"], event["canvasY"])
                except AttributeError:
                    pass
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
        if self._supports_probe():
            self.scene.input_handler.on_click(self._on_probe_click)

        # Wire gizmo visibility
        self.axes_visible.on_change(self._apply_axes_visible)
        self.navcube_visible.on_change(self._apply_navcube_visible)
        self.picking_enabled.on_change(self._apply_picking_enabled)
        self.camera_shared.on_change(self._apply_camera_shared)
        self.camera_shared.on_change(self._sync_camera_link_ui)

        # Wire nav cube face selection
        self.navigation_cube.faces.on_select(self._on_navcube_select)

        # Wire clipping observable after scene is ready
        self.clipping_enabled.on_change(self._apply_clipping_enabled)
        # Keep the viewport tool dock / clip toolbar in sync.
        self.clipping_enabled.on_change(self._sync_clip_ui)
        self.use_global_clipping.on_change(
            lambda v, _o: self._set_tool_active(self._clip_global_tool, v)
        )
        if hasattr(self, "wireframe_visible") and self._wf_tool is not None:
            self.wireframe_visible.on_change(
                lambda v, _o: self._set_tool_active(self._wf_tool, v)
            )

        def redraw_if_needed():
            self.apply_viewport_theme()

        self.on_mounted(redraw_if_needed)
        # The WebGPU canvas is created in the component's own "mounted" handler;
        # ours runs after it, so the canvas is ready when we set the clear color.
        self.wgpu.on("mounted", lambda *a: self.apply_viewport_theme())

    def apply_viewport_theme(self):
        """Set the scene background (clear color + overlays) from the active theme.

        Reads the ``data-theme`` attribute, which ``install``/``set_theme`` set
        from the stored preference (resolving "system" via the OS) — the single
        source of truth, available by the time the canvas mounts.
        """
        def _apply(js):
            scene = self.scene
            canvas = getattr(scene, "canvas", None) if scene is not None else None
            if canvas is None:
                return
            key = "dark" if cb.is_dark(js) else "light"
            canvas.clear_color = Color(*VIEWPORT_CLEAR[key], 1)
            _theme_scene(scene, VIEWPORT_CLEAR[key], VIEWPORT_TEXT[key])
            scene.render()

        self.call_js(_apply)

    # -- Gizmo visibility handlers --

    def _apply_axes_visible(self, val, _old):
        self.coordinate_axes.active = val
        self.scene.render()

    def _apply_navcube_visible(self, val, _old):
        self.navigation_cube.active = val
        self.scene.render()

    def toggle_axes(self):
        self.axes_visible.toggle()

    def toggle_navcube(self):
        self.navcube_visible.toggle()

    def toggle_picking(self):
        self.picking_enabled.toggle()

    def undo_last(self):
        """Revert the most recent undoable action (region hides etc.)."""
        label = self.undo_stack.undo()
        if label:
            self.pick_overlay.show_info("Undone", [("action", label)])

    def _apply_picking_enabled(self, val, _old):
        if not getattr(self, '_picking_always_active', False):
            _usersettings.set("picking_enabled", val)
        if not val and hasattr(self, '_highlights'):
            self._clear_highlight()
            self.pick_overlay.hide()
            self.scene.render()

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
        self._highlights = [ro._highlight_uniforms for ro in self.scene.render_objects if hasattr(ro, "_highlight_uniforms")]
        for ro in self.scene.render_objects:
            if hasattr(ro, "render_objects"):
                self._highlights += [sub._highlight_uniforms for sub in ro.render_objects if hasattr(sub, "_highlight_uniforms")]
        for r, kind in renderers:
            r.on_select(lambda ev, k=kind: self._on_pick_select(ev, k))
        self.scene.on_click_background(self._on_pick_background)
        self.scene.input_handler.on_mousemove(self._on_pick_hover)
        self.scene.input_handler.on_mouseout(self._on_pick_out)

    def _add_pickable(self, renderer, kind):
        """Register one more pickable renderer on the already-set-up live scene
        (used when a renderer is spliced in without a full draw()/setup_picking).
        Only the per-renderer select + highlight are added; the scene-level
        hover/background handlers are already wired."""
        if not hasattr(self, "_pick_renderers"):
            return
        self._pick_renderers.append((renderer, kind))
        if hasattr(renderer, "_highlight_uniforms"):
            self._highlights.append(renderer._highlight_uniforms)
        renderer.on_select(lambda ev, k=kind: self._on_pick_select(ev, k))

    def _on_pick_hover(self, ev):
        if ev["buttons"] == 0 and self.scene.canvas is not None and self.scene.canvas.select_texture is not None:
            self._shift_hover = ev.get("shiftKey", False)
            try:
                self.scene.select(ev["canvasX"], ev["canvasY"])
            except AttributeError:
                pass

    def _on_pick_out(self, ev):
        if not hasattr(self, '_pick_mesh'):
            return
        self._last_pick = None
        self._clear_highlight()
        self.pick_overlay.hide()
        self.scene.render()

    def _on_pick_background(self, ev):
        self._last_pick = None
        self._clear_highlight()
        self.pick_overlay.hide()
        self.scene._render_highlight()

    def _on_pick_select(self, event, kind="surface"):
        try:
            result = MeshPickResult(event, self._pick_mesh, self.scene.options, kind=kind)
            self._last_pick = result
            header, rows, accent = self._pick_info(result)
            if rows:
                self.pick_overlay.show_info(header, rows, accent_last=accent)
            else:
                self.pick_overlay.hide()
            if not self.picking_enabled.value:
                return
            for hl in self._highlights:
                hl.renderer_id = event.obj_id
                if getattr(self, "_shift_hover", False):
                    hl.element_id = 0xFFFFFFFF
                    hl.region_index = result.region_index
                else:
                    hl.element_id = result.element_nr
                    hl.region_index = 0xFFFFFFFF
                hl.update_buffer()
            self.scene._render_highlight()
        except Exception:
            self.pick_overlay.hide()

    def _clear_highlight(self):
        for hl in self._highlights:
            hl.renderer_id = 0
            hl.element_id = 0xFFFFFFFF
            hl.region_index = 0xFFFFFFFF
            hl.solid_index = 0xFFFFFFFF
            hl.update_buffer()



    def _kind_label(self, result):
        """Element kind label. The 'surface' renderer draws codim-0 (VOL)
        elements on a 2D mesh, but boundary (BND) elements on a 3D mesh."""
        dim = getattr(getattr(self, "mesh", None), "dim", 3)
        if result.kind == "surface":
            return "vol el." if dim == 2 else "surf el."
        if result.kind == "volume":
            return "vol el."
        if result.kind == "clipping":
            return "clip"
        return f"{result.kind} el."

    def _pick_info(self, result):
        """Structured pick info: (header, [(label, value), ...], accent_last)."""
        pos = result.world_pos
        rows = [
            ("kind", self._kind_label(result)),
            ("element", f"#{result.element_nr}"),
            ("region", result.region_name or "—"),
            ("xyz", f"{pos[0]:.5f}, {pos[1]:.5f}, {pos[2]:.5f}"),
        ]
        return ("Picked element", rows, False)

    def _probe_mesh_point(self, Q):
        """Map a picked world point back to the *undeformed* mesh point.

        With deformation on, picking returns the deformed surface position; the
        coefficient function lives on the undeformed mesh. Recover the original
        point P with Q = P + scale·deform(P) via fixed-point iteration.
        """
        import numpy as np
        Q = np.array([float(Q[0]), float(Q[1]), float(Q[2])], dtype=float)
        deform = getattr(self, "deformation", None)
        enabled = getattr(self, "deformation_enabled", None)
        if deform is None or enabled is None or not enabled.value:
            return Q
        try:
            scale = float(self.deformation_scale.value) * float(self.deformation_scale2.value)
        except Exception:
            return Q
        if scale == 0.0:
            return Q
        P = Q.copy()
        for _ in range(12):
            try:
                mip = self.mesh(*[float(P[i]) for i in range(self.mesh.dim)])
                d = np.asarray(deform(mip), dtype=float).ravel()
            except Exception:
                return Q
            dv = np.zeros(3)
            dv[:min(3, d.size)] = d[:3]
            newP = Q - scale * dv
            if np.linalg.norm(newP - P) < 1e-10:
                P = newP
                break
            P = newP
        return P

    @property
    def clipping(self):
        return self.app_data.clipping

    @property
    def camera(self):
        """The camera driving this view: the mesh/geometry-wide one, or — when
        detached — this view's own."""
        if self.camera_shared.value:
            return self._shared_camera
        if self._own_camera is None:
            self._own_camera = Camera()
        return self._own_camera

    def _resolve_camera_group(self):
        """The object all views sharing this camera have in common: the geometry
        a mesh was generated from, else the mesh itself (``None`` = no sharing).
        """
        geo = getattr(self, "geo", None)
        if geo is not None:
            return geo
        mesh = getattr(self, "mesh", None)
        if mesh is None:
            return None
        try:
            from netgen.meshing import NetgenGeometry

            geo = mesh.ngmesh.GetGeometry()
            # Meshes without a geometry all report the same dummy base object.
            if geo is not None and type(geo) is not NetgenGeometry:
                return geo
        except Exception:
            pass
        return mesh

    def toggle_camera_link(self):
        """Link this view's camera to the other views on this mesh, or detach it."""
        self.camera_shared.toggle()

    def _apply_camera_shared(self, val, _old):
        if not val:
            # Detach from the current view, not from wherever the own camera was.
            cam = Camera()
            cam.transform = self._shared_camera.transform.copy()
            cam.orthographic = self._shared_camera.orthographic
            self._own_camera = cam
        self._swap_scene_camera(self.camera)

    def _swap_scene_camera(self, camera):
        """Point the live scene at *camera* (moving observers and input wiring)."""
        scene = self.scene
        if scene is None or scene.options.camera is camera:
            return
        old = scene.options.camera
        old.unregister_callbacks(scene.input_handler)
        _unregister_observer(old, scene._on_camera_changed)
        scene.options.camera = camera
        camera.register_observer(scene._on_camera_changed)
        scene._wire_input(camera)
        self.sync_camera()

    def sync_camera(self):
        """Push this view's camera state into its live scene.

        While a scene is visible the JS engine owns the camera, so moves made in
        one tab only reach the other views sharing that camera when they are
        shown again — the app calls this on tab activation.
        """
        scene = self.scene
        if scene is None or scene.canvas is None:
            return
        camera = self.camera
        if scene.options.camera is not camera:
            self._swap_scene_camera(camera)
            return
        if scene._render_mutex is not None:
            with scene._render_mutex:
                scene._select_buffer_valid = False
        engine = getattr(scene, "_js_engine", None)
        if engine is None:
            scene.options.update_buffers()
            return
        camera.register_observer(scene._on_camera_changed)
        scene._wire_input(camera)
        import webgpu.platform as platform

        t = camera.transform
        center = t._center.tolist() if hasattr(t._center, "tolist") else list(t._center)
        try:
            engine.setCameraTransform(
                platform.toJS(t._mat.flatten().tolist()), platform.toJS(list(center))
            )
            engine.setProjection(camera.orthographic)
        except Exception as e:
            print(f"warning: camera sync failed: {e}")

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
            ("u", self.undo_last, "Undo last action", "General"),
        ]
        modes = [
            (
                "v",
                "View",
                [
                    ("x", lambda: self.set_view("yz"), "Look along X"),
                    ("y", lambda: self.set_view("xz"), "Look along Y"),
                    ("z", lambda: self.set_view("xy"), "Look along Z"),
                    ("o", lambda: self.set_orthographic(True), "Orthographic"),
                    ("p", lambda: self.set_orthographic(False), "Perspective"),
                    ("r", self.reset_camera, "Reset"),
                    ("l", self.toggle_camera_link, "Share/detach camera"),
                ],
            ),
        ]
        if not getattr(self, '_picking_always_active', False):
            modes.append(
                ("p", "Pick", [("a", self.toggle_picking, "Toggle highlight")])
            )
        return {"flat": flat, "modes": modes}

    def _gizmo_show_bindings(self):
        """Return show-mode bindings for gizmo toggles. Subclasses append to their 'Show' mode."""
        return [
            ("a", self.toggle_axes, "Toggle axes"),
            ("n", self.toggle_navcube, "Toggle nav cube"),
        ]

    def set_view(self, plane):
        """Set camera to a standard view (``"xy"``, ``"xz"``, or ``"yz"``).

        Repeating the same view flips to look from the opposite side, like the
        clipping-plane axis shortcuts.
        """
        camera = self.scene.options.camera
        if getattr(self, "_last_view_plane", None) == plane:
            flip = not getattr(self, "_last_view_flip", False)
        else:
            flip = False
        getattr(camera, f"reset_{plane}")(flip=flip)
        self._last_view_plane = plane
        self._last_view_flip = flip
        self.scene.render()

    def set_orthographic(self, value):
        """Switch between orthographic and perspective camera projection."""
        camera = self.scene.options.camera
        if camera.orthographic == value:
            return
        camera.set_orthographic(value)
        self.scene.render()

    def _apply_clipping_enabled(self, val, _old):
        self.clipping.enable_clipping(val)
        self.wgpu.scene.render()

    def toggle_clipping(self):
        self.clipping_enabled.toggle()

    # -- Viewport tool dock + inline clipping toolbar ----------------------

    def _vtool(self, icon, tip, handler):
        """A single floating viewport tool button."""
        btn = Div(QIcon(ui_name=icon), QTooltip(tip), ui_class=str(cb.vp_tool))
        btn.on("click", lambda e=None: handler())
        return btn

    def _set_tool_active(self, btn, on):
        if btn is not None:
            btn.ui_class = str(cb.vp_tool) + (" " + str(cb.vp_tool_on) if on else "")

    def _supports_clipping(self):
        return not hasattr(self, "mesh") or self.mesh.dim == 3

    def toggle_wireframe(self):
        if hasattr(self, "wireframe_visible"):
            self.wireframe_visible.toggle()

    def _build_tool_dock(self):
        self._wf_tool = None
        self._clip_tool = None
        tools = [self._vtool("mdi-overscan", "Fit view  ·  r", self.reset_camera)]
        self._link_tool = self._build_camera_link_tool()
        if self._link_tool is not None:
            tools.append(self._link_tool)
        if hasattr(self, "wireframe_visible"):
            self._wf_tool = self._vtool("mdi-grid", "Wireframe  ·  w", self.toggle_wireframe)
            self._set_tool_active(self._wf_tool, self.wireframe_visible.value)
            tools.append(self._wf_tool)
        if self._supports_clipping():
            tools.append(Div(ui_class=str(cb.vp_sep)))
            self._clip_tool = self._vtool("mdi-content-cut", "Clipping plane  ·  c",
                                          self.toggle_clipping)
            tools.append(self._clip_tool)
        self._probe_tool = None
        if self._supports_probe():
            tools.append(Div(ui_class=str(cb.vp_sep)))
            self._probe_tool = self._vtool(
                "mdi-crosshairs-gps", "Line / point probe  →  plot", self.toggle_probe)
            tools.append(self._probe_tool)
        # View tools: fullscreen + view bookmarks.
        tools.append(Div(ui_class=str(cb.vp_sep)))
        tools.append(self._vtool("mdi-fullscreen", "Fullscreen viewport",
                                  self._toggle_fullscreen))
        tools.append(self._build_bookmark_tool())
        return Div(*tools, ui_class=str(cb.vp_dock))

    def _build_camera_link_tool(self):
        """Toggle between the mesh/geometry-wide camera and one just for this view."""
        if self._camera_group is None:
            return None
        self._link_icon = QIcon(ui_name="mdi-link-variant")
        self._link_tip = QTooltip("")
        btn = Div(self._link_icon, self._link_tip, ui_class=str(cb.vp_tool))
        btn.on("click", lambda e=None: self.toggle_camera_link())
        return btn

    def _sync_camera_link_ui(self, val, _old):
        if getattr(self, "_link_tool", None) is None:
            return
        self._link_icon.ui_name = "mdi-link-variant" if val else "mdi-link-variant-off"
        self._link_tip.ui_children = [
            "Camera shared with other views of this mesh  ·  click to detach"
            if val else "Camera detached  ·  click to share again"
        ]
        self._set_tool_active(self._link_tool, val)

    def _build_bookmark_tool(self):
        self._bookmarks = []  # list of (name, camera-transform snapshot)
        self._bm_pop = Div(ui_class=str(cb.bm_pop))
        self._bm_pop.ui_hidden = True
        self._bm_pop.on("mouseleave", lambda e=None: self._close_bookmarks())
        btn = Div(
            QIcon(ui_name="mdi-bookmark-outline"), QTooltip("Saved views"), self._bm_pop,
            ui_class=str(cb.vp_tool) + " relative-position",
        )
        btn.on("click", lambda e=None: self._toggle_bookmarks())
        self._rebuild_bookmark_menu()
        return btn

    def _build_clip_toolbar(self):
        if not self._supports_clipping():
            self._clip_global_tool = None
            return None
        axis = self._current_clip_axis()
        self._clip_axis_seg = Segmented(
            [("0", "X"), ("1", "Y"), ("2", "Z")], str(axis), self._on_clip_axis)
        flip = self._vtool("mdi-flip-horizontal", "Flip side", self._flip_clip)
        self._clip_offset = QSlider(
            ui_min=-1, ui_max=1, ui_step=0.01, ui_model_value=0.0,
            ui_dense=True, ui_class=str(cb.vc_slider))
        self._clip_offset.on_update_model_value(self._on_clip_offset)
        self._clip_offset_val = Div("0.00", ui_class=str(cb.vc_o_val))
        self._clip_global_tool = self._vtool(
            "mdi-earth", "Clip all objects (global)", self.use_global_clipping.toggle)
        self._set_tool_active(self._clip_global_tool, self.use_global_clipping.value)
        close = self._vtool("mdi-close", "Close clipping  ·  esc",
                            lambda: setattr(self.clipping_enabled, "value", False))
        toolbar = Div(
            Div(QIcon(ui_name="mdi-content-cut"), "Clip", ui_class=str(cb.vc_lab)),
            Div(self._clip_axis_seg, ui_class=str(cb.vc_axis)),
            flip,
            Div(self._clip_offset, self._clip_offset_val, ui_class=str(cb.vc_offset)),
            self._clip_global_tool,
            close,
            ui_class=str(cb.vp_clip),
        )
        toolbar.ui_hidden = True
        return toolbar

    def _sync_clip_ui(self, val, _old):
        """Reflect clipping_enabled on the dock button + toolbar visibility."""
        self._set_tool_active(self._clip_tool, val)
        if self._clip_toolbar is not None:
            self._clip_toolbar.ui_hidden = not val

    def _current_clip_axis(self):
        n = [abs(self.clipping.normal[i]) for i in range(3)]
        return n.index(max(n))

    def _on_clip_axis(self, val):
        self.clip_along_axis(int(val))

    def _flip_clip(self):
        self.clip_along_axis(self._current_clip_axis())

    def _clip_factor(self):
        try:
            bb = self.wgpu.scene.bounding_box
        except Exception:
            bb = ((0, 0, 0), (1, 1, 1))
        d = [bb[1][i] - bb[0][i] for i in range(3)]
        return math.sqrt(sum(x * x for x in d)) / 2.0 or 1.0

    def _on_clip_offset(self, ev):
        v = ev.value if hasattr(ev, "value") else ev
        try:
            v = float(v)
        except (ValueError, TypeError):
            return
        self._clip_offset_val.ui_children = [f"{v:.2f}"]
        self.clipping.set_offset(v * self._clip_factor())
        self.wgpu.scene.render()

    # -- Fullscreen + view bookmarks (in the tool dock) --------------------

    def _toggle_fullscreen(self):
        """Toggle browser fullscreen on the viewport container."""
        def _go(js):
            try:
                el = self.scene.canvas.canvas.parentElement
                doc = js.document
                if doc.fullscreenElement is not None:
                    doc.exitFullscreen()
                else:
                    el.requestFullscreen()
            except Exception:
                pass
        self.call_js(_go)

    def _toggle_bookmarks(self):
        if self._bm_pop.ui_hidden:
            self._rebuild_bookmark_menu()
            self._bm_pop.ui_hidden = False
        else:
            self._bm_pop.ui_hidden = True

    def _close_bookmarks(self):
        self._bm_pop.ui_hidden = True

    def _rebuild_bookmark_menu(self):
        rows = [Div("Saved views", ui_class=str(cb.bm_title))]
        if not self._bookmarks:
            rows.append(Div("No saved views", ui_class=str(cb.bm_empty)))
        for name, snap in self._bookmarks:
            row = Div(QIcon(ui_name="mdi-camera-outline"), name, ui_class=str(cb.bm_row))
            row.on("click", lambda e=None, s=snap: self._recall_bookmark(s))
            rows.append(row)
        add = Div(QIcon(ui_name="mdi-plus"), "Save current view", ui_class=str(cb.bm_add))
        add.on("click", lambda e=None: self._save_bookmark())
        rows.append(add)
        self._bm_pop.ui_children = rows

    def _save_bookmark(self):
        cam = self.scene.options.camera
        self._bookmarks.append((f"View {len(self._bookmarks) + 1}", cam.transform.copy()))
        self._rebuild_bookmark_menu()

    def _recall_bookmark(self, snap):
        cam = self.scene.options.camera
        cam.transform = snap.copy()
        cam._notify_observers()   # push the new camera uniform (as reset() does)
        self.scene.render()
        self._close_bookmarks()

    # -- Field probe: click points → values, ≥2 points → 1D line plot ------

    def _supports_probe(self):
        return hasattr(self, "cf")

    def _build_viewport_legend(self):
        """Override to return an in-viewport colorbar legend (fields only)."""
        return None

    def toggle_probe(self):
        self._probe_active = not self._probe_active
        self._set_tool_active(self._probe_tool, self._probe_active)
        if self._probe_panel is not None:
            self._probe_panel.ui_hidden = not self._probe_active

    def _build_probe_panel(self):
        if not self._supports_probe():
            return None
        panel = Div(ui_class=str(cb.vp_probe))
        panel.ui_hidden = True
        self._probe_panel = panel
        self._rebuild_probe_panel()
        return panel

    def _set_probe_mode(self, mode):
        self._probe_mode = mode
        self._clear_probe()

    def _on_probe_click(self, event):
        if not self._probe_active or event.get("button", 0) != 0:
            return
        p = self.scene.get_position(event["canvasX"], event["canvasY"])
        if p is None:
            return
        import numpy as np
        pt = np.array([float(p[0]), float(p[1]), float(p[2])])
        # CSS client coords (event x/y) for fixed-position overlay markers.
        screen = (float(event.get("x", 0)), float(event.get("y", 0)))
        # In line mode, a 3rd click starts a fresh segment.
        if self._probe_mode == "line" and len(self._probe_points) >= 2:
            self._probe_points = []
            self._probe_screen = []
        self._probe_points.append((pt, self._probe_value(pt)))
        self._probe_screen.append(screen)
        self._update_preview()
        self._rebuild_probe_panel()

    def _update_preview(self):
        """Draw screen-space marker dots + connecting segment for the probe points."""
        if self._probe_preview is None:
            return
        import math
        children = []
        pts = self._probe_screen
        for i in range(len(pts) - 1):
            (ax, ay), (bx, by) = pts[i], pts[i + 1]
            length = math.hypot(bx - ax, by - ay)
            angle = math.degrees(math.atan2(by - ay, bx - ax))
            children.append(Div(ui_class=str(cb.vp_preview_line),
                                ui_style=f"left:{ax}px;top:{ay}px;width:{length}px;"
                                         f"transform:rotate({angle}deg);"))
        for (x, y) in pts:
            children.append(Div(ui_class=str(cb.vp_preview_dot),
                                ui_style=f"left:{x}px;top:{y}px;"))
        self._probe_preview.ui_children = children

    def _probe_value(self, pt):
        """Evaluate the field at a picked world point (norm for vectors), mapping
        back through any active deformation. None if outside the mesh."""
        try:
            import numpy as np
            P = self._probe_mesh_point(pt)
            mip = self.mesh(*[float(P[i]) for i in range(self.mesh.dim)])
            v = self.cf(mip)
            if isinstance(v, (tuple, list, np.ndarray)):
                return float(np.linalg.norm(np.real(np.asarray(v, dtype=complex))))
            return float(np.real(v))
        except Exception:
            return None

    def _rebuild_probe_panel(self):
        rows = [Div(QIcon(ui_name="mdi-crosshairs-gps"), "Field probe",
                    ui_class=str(cb.vp_probe_head))]
        rows.append(Segmented(
            [("points", "Points"), ("line", "Line")], self._probe_mode, self._set_probe_mode))
        if not self._probe_points:
            hint = ("Click two points to define a cut line." if self._probe_mode == "line"
                    else "Click points on the field. Add 2 or more for a line plot.")
            rows.append(Div(hint, ui_class=str(cb.vp_probe_hint)))
        for i, (pt, val) in enumerate(self._probe_points):
            vtxt = "—" if val is None else f"{val:.4g}"
            label = ("AB"[i] if self._probe_mode == "line" and i < 2 else f"P{i+1}")
            delx = Div(QIcon(ui_name="mdi-close"), ui_class=str(cb.probe_del))
            delx.on("click", lambda e=None, idx=i: self._remove_probe_point(idx))
            rows.append(Div(
                Div(f"{label}  ({pt[0]:.2f}, {pt[1]:.2f}, {pt[2]:.2f})", ui_class=str(cb.grow)),
                Div(vtxt, ui_class=str(cb.vp_probe_val)),
                delx,
                ui_class=str(cb.vp_probe_pt),
            ))
        plot_btn = QBtn(
            ui_label="Plot line", ui_icon="mdi-chart-line", ui_color="primary",
            ui_dense=True, ui_no_caps=True, ui_size="sm", ui_class="full-width")
        plot_btn.ui_disable = len(self._probe_points) < 2
        plot_btn.on_click(lambda e=None: self._plot_probe_line())
        clear_btn = QBtn(ui_label="Clear", ui_flat=True, ui_dense=True,
                         ui_no_caps=True, ui_size="sm")
        clear_btn.on_click(lambda e=None: self._clear_probe())
        rows.append(Div(plot_btn, clear_btn, ui_class="row items-center " + str(cb.gap_sm)))
        self._probe_panel.ui_children = rows

    def _remove_probe_point(self, i):
        if 0 <= i < len(self._probe_points):
            del self._probe_points[i]
            if i < len(self._probe_screen):
                del self._probe_screen[i]
            self._update_preview()
            self._rebuild_probe_panel()

    def _clear_probe(self):
        self._probe_points = []
        self._probe_screen = []
        if self._probe_preview is not None:
            self._probe_preview.ui_children = []
        self._rebuild_probe_panel()

    def _plot_probe_line(self):
        if len(self._probe_points) < 2:
            return
        import numpy as np
        pts = [p for p, _ in self._probe_points]
        xs, ys = [], []
        total, per_seg = 0.0, 48
        for a, b in zip(pts[:-1], pts[1:]):
            seg = float(np.linalg.norm(b - a))
            for k in range(per_seg + 1):
                t = k / per_seg
                v = self._probe_value(a + (b - a) * t)
                xs.append(total + seg * t)
                ys.append(float("nan") if v is None else v)
            total += seg
        fig = self._probe_figure(xs, ys)
        if fig is None:
            return
        from .plot import PlotComponent
        self.app_data.add_tab(
            f"{self.title} — line probe", PlotComponent, {"obj": fig}, self.app_data)

    def _probe_figure(self, xs, ys):
        try:
            import plotly.graph_objects as go
        except Exception:
            return None
        fig = go.Figure(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color="#2f6fe5", width=2)))
        fig.update_layout(
            title=f"Line probe — {self.title}",
            xaxis_title="arc length", yaxis_title="value",
            template="plotly_white", margin=dict(l=55, r=20, t=44, b=44),
        )
        return fig

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
