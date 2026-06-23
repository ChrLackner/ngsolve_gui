"""Live surface-mesh preview during meshing.

How it works:

* `GenerateMesh` on the geometry classes is monkey-patched. Whenever it runs
  and a geometry tab is currently shown, a `MeshingPreview` is started for the
  duration of the call. This covers both the "Generate mesh" button (whose
  `create_mesh` calls `GenerateMesh`) *and* any user script that calls
  `geo.GenerateMesh(...)` after `Draw(geo)`.
"""

import threading

_app = None
_patched = False

_originals: dict = {}

_last_interaction = 0.0

def install(app):
    """Register the running app and monkey-patch GenerateMesh (idempotent)."""
    global _app, _patched
    _app = app
    if _patched:
        return
    _patch_generate_mesh()
    _patch_camera_interaction()
    _patched = True


def _patch_camera_interaction():
    """Record interaction time whenever the JS engine reports a camera move.

    Rotation/zoom is handled entirely JS-side (Scene._apply_camera_from_js only
    mirrors the matrix into Python, it does not re-render). We hook it to know
    when the user is actively interacting so the preview can hold its updates and
    not ship structural engine.update()s into the middle of a JS render frame —
    that race is what flickers between the geometry and the mesh while rotating.

    Patched at the class level at app startup, before any scene creates its
    camera-changed proxy, so the proxy binds this wrapped version.
    """
    try:
        from webgpu.scene import Scene
    except Exception:
        return
    if getattr(Scene, "_meshing_preview_cam_patched", False):
        return
    orig = Scene._apply_camera_from_js

    def wrapped(self, payload):
        global _last_interaction
        import time

        _last_interaction = time.monotonic()
        return orig(self, payload)

    Scene._apply_camera_from_js = wrapped
    Scene._meshing_preview_cam_patched = True


def get_app():
    return _app


def set_terminate(flag: bool):
    """Set netgen's global meshing terminate flag, if the binding is available.

    The binding (`_SetTerminate`) requires a netgen build that exposes it; until
    then this is a no-op and abort falls back to the footer's thread interrupt.
    """
    try:
        from netgen.libngpy._meshing import _SetTerminate

        _SetTerminate(bool(flag))
    except Exception:
        pass


def get_terminate() -> bool:
    """Whether a meshing abort has been requested (False if binding absent)."""
    try:
        from netgen.libngpy._meshing import _GetTerminate

        return bool(_GetTerminate())
    except Exception:
        return False


def _candidate_geometry_classes():
    """The geometry classes whose GenerateMesh we want to wrap."""
    classes = []
    try:
        import netgen.occ as ngocc

        classes.append(ngocc.OCCGeometry)
    except Exception:
        pass
    # Other geometry kinds share the same Python-level method name; wrap them too
    # when present so scripts using them also get a preview.
    for modname, clsname in (
        ("netgen.csg", "CSGeometry"),
        ("netgen.stl", "STLGeometry"),
        ("netgen.geom2d", "SplineGeometry"),
    ):
        try:
            mod = __import__(modname, fromlist=[clsname])
            cls = getattr(mod, clsname, None)
            if cls is not None and hasattr(cls, "GenerateMesh"):
                classes.append(cls)
        except Exception:
            pass
    return classes


def _patch_generate_mesh():
    for cls in _candidate_geometry_classes():
        orig = cls.__dict__.get("GenerateMesh", None) or getattr(cls, "GenerateMesh", None)
        if orig is None or cls in _originals:
            continue
        _originals[cls] = orig
        cls.GenerateMesh = _make_wrapper(cls, orig)


def _make_wrapper(cls, orig):
    def generate_mesh(self, *args, **kwargs):
        preview = _try_start_preview()
        if preview is None:
            return orig(self, *args, **kwargs)

        if args:
            preview.cancel()
            return orig(self, *args, **kwargs)

        mesh = kwargs.get("mesh")
        if mesh is None:
            import netgen.meshing as ngm

            mesh = ngm.Mesh()
            kwargs["mesh"] = mesh

        set_terminate(False)
        preview.bind(mesh)
        try:
            ret = orig(self, *args, **kwargs)
        finally:
            preview.stop()
        return ret if ret is not None else mesh

    generate_mesh.__name__ = getattr(orig, "__name__", "GenerateMesh")
    generate_mesh.__doc__ = getattr(orig, "__doc__", None)
    return generate_mesh


def _try_start_preview():
    """Create a preview bound to the active geometry tab, or None if unavailable."""
    app = _app
    if app is None:
        return None
    try:
        app_data = app.app_data
        name = app_data.active_tab
        tab = app_data.get_tab(name) if name else None
        comp = tab.get("component") if tab else None
    except Exception:
        return None
    # Only overlay onto a drawn geometry scene.
    if comp is None or not hasattr(comp, "geo_renderer") or not hasattr(comp, "scene"):
        return None
    if getattr(comp, "geo_renderer", None) is None:
        return None
    return MeshingPreview(app, comp)


class MeshingPreview:
    """Overlays the growing surface mesh on the dimmed geometry of one tab."""

    _poll_interval = 0.15
    _interaction_quiet = 0.2

    def __init__(self, app, comp):
        self.app = app
        self.comp = comp
        self.mesh = None
        self._stop = threading.Event()
        self._cancelled = False
        self._thread = None
        self._attached = False
        self._frozen = False
        self._tris = None
        self._wire = None
        self._mdata = None
        self._faces_were_active = None

    def cancel(self):
        """Abandon before binding (e.g. unsupported call form)."""
        self._cancelled = True

    def bind(self, mesh):
        if self._cancelled:
            return
        self.mesh = mesh
        self._thread = threading.Thread(
            target=self._poll, name="MeshPreview", daemon=True
        )
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=1.0)
        self._detach()

    def _poll(self):
        try:
            from netgen.libngpy._meshing import _GetStatus
        except Exception:
            _GetStatus = None

        last_ts = None
        while not self._stop.is_set():
            try:
                n2d = len(self.mesh.Elements2D())
                nfd = len(self.mesh.FaceDescriptors())
                ts = self.mesh._timestamp
            except Exception:
                n2d, nfd, ts = 0, 0, None

            if not self._attached and n2d > 0 and nfd > 0:
                self._attach()
                last_ts = ts

            if self._attached and not self._frozen:
                status = ""
                if _GetStatus is not None:
                    try:
                        status, _ = _GetStatus()
                    except Exception:
                        status = ""
                if "volume" in (status or "").lower():
                    self._frozen = True
                    self._refresh()  # one last frame with the full surface mesh
                elif ts != last_ts and not self._interacting():
                    last_ts = ts
                    self._refresh()

            self._stop.wait(self._poll_interval)

    def _attach(self):
        try:
            from ngsolve_webgpu.mesh import MeshData, MeshElements2d, MeshWireframe2d

            clip = getattr(self.comp, "clipping", None)
            self._mdata = MeshData(self.mesh)
            self._mdata.subdivision = 1
            self._tris = MeshElements2d(self._mdata, clipping=clip)
            self._wire = MeshWireframe2d(self._mdata, clipping=clip)
            self._hide_faces()
            scene = self.comp.scene
            scene.render_objects = list(scene.render_objects) + [self._tris, self._wire]
            self._attached = True
            self._refresh()
        except Exception as e:
            print("mesh preview: attach failed:", e)
            self._stop.set()

    def _detach(self):
        try:
            scene = self.comp.scene
            drop = {id(self._tris), id(self._wire)}
            scene.render_objects = [
                ro for ro in scene.render_objects if id(ro) not in drop
            ]
            if self._faces_were_active is not None:
                self.comp.geo_renderer.faces.active = self._faces_were_active
        except Exception:
            pass
        self._render()

    def _hide_faces(self):
        try:
            faces = self.comp.geo_renderer.faces
            self._faces_were_active = faces.active
            faces.active = False
        except Exception:
            self._faces_were_active = None

    def _refresh(self):
        try:
            self._mdata.set_needs_update()
        except Exception:
            pass
        for ro in (self._tris, self._wire):
            try:
                ro.set_needs_update()
            except Exception:
                pass
        self._render()

    def _render(self):
        try:
            self.comp.scene.render()
        except Exception:
            pass

    def _interacting(self):
        import time
        return (time.monotonic() - _last_interaction) < self._interaction_quiet
