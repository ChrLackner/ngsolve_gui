import os
import threading
from contextlib import contextmanager
from pathlib import Path
import numpy as np
from typing import Any, Callable, Iterable

import netgen.occ as ngocc
import ngsolve as ngs

os.environ.setdefault("MPLBACKEND", "Agg")

from .app_data import AppData
from .function import FunctionComponent
from .geometry import GeometryComponent
from .mesh import MeshComponent
from .plot import PlotComponent
from ngapp.components import Component

_appdata: AppData
_redraw_func: Callable | None = None


def _file_extension_matches(path: Path, suffixes: Iterable[str]) -> bool:
    """Helper to check file endings including multi-part like .vol.gz."""
    lower_path = str(path).lower()
    return any(lower_path.endswith(suffix) for suffix in suffixes)


def _build_loader_snippet(filename: str, name: str) -> str:
    """Return the Python snippet used to load a supported file."""
    path = Path(filename)
    ext = path.suffix.lower()

    if _file_extension_matches(path, (".vol", ".vol.gz")):
        return f"""import ngsolve
mesh = ngsolve.Mesh('{filename}')
ngsolve.Draw(mesh, '{name}')"""

    if ext in {".step", ".iges", ".stp", ".brep"}:
        return f"""import netgen.occ
import ngsolve
geometry = netgen.occ.OCCGeometry("{filename}")
ngsolve.Draw(geometry, name='{name}')"""

    if ext == ".pkl":
        return f"""import netgen.occ
import ngsolve, pickle
obj = pickle.load(open("{filename}", "rb"))
ngsolve.Draw(obj, name='{name}')"""

    if ext == ".py":
        import tokenize
        with tokenize.open(filename) as f:
            return f.read()

    raise ValueError(f"Unsupported file type: {ext.lstrip('.')}")


def _build_progress_stdout():
    """Build a ``sys.stdout`` proxy that renders ``\\r`` progress in place.
    """
    from prompt_toolkit.patch_stdout import StdoutProxy

    class _ProgressStdoutProxy(StdoutProxy):
        _OVERWRITE = "\x1b[1A\r\x1b[2K"

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._cur = ""  # text accumulated since the last \n or \r
            self._progress_active = False

        def _emit(self, text, is_progress):
            prefix = self._OVERWRITE if is_progress and self._progress_active else ""
            self._flush_queue.put(prefix + text + "\n")
            self._progress_active = is_progress

        def _write(self, data):
            self._cur += data
            while "\n" in self._cur:
                before, self._cur = self._cur.split("\n", 1)
                self._emit(before.rsplit("\r", 1)[-1], is_progress=False)
            if "\r" in self._cur:
                *_segments, self._cur = self._cur.split("\r")
                self._emit(_segments[-1], is_progress=True)

    return _ProgressStdoutProxy(raw=True)


@contextmanager
def _progress_patch_stdout(raw: bool = True):
    """Drop-in replacement for prompt_toolkit's ``patch_stdout``.
    """
    import sys

    proxy = _build_progress_stdout()
    old_out, old_err = sys.stdout, sys.stderr
    sys.stdout = sys.stderr = proxy
    try:
        yield
    finally:
        sys.stdout, sys.stderr = old_out, old_err
        proxy.close()


def _launch_interactive_shell(
    code: str, script_globals: dict, app, done_event: threading.Event
) -> threading.Thread:
    """Start IPython in a background thread; clean up terminal on exit."""
    import sys
    import termios

    if not sys.stdin.isatty():
        raise ImportError("No TTY available for IPython shell.")

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    from IPython.terminal.embed import InteractiveShellEmbed

    ipshell = [None]

    def run_script():
        _lower_thread_priority()
        _force_headless_matplotlib()
        try:
            exec(compile(code, "<embedded>", "exec"), script_globals)
        except (SystemExit, KeyboardInterrupt):
            pass
        except Exception:
            import traceback

            traceback.print_exc()
        finally:
            done_event.set()

    worker = threading.Thread(target=run_script, name="PythonRunner", daemon=True)
    worker.start()

    def launch_shell():
        import IPython.terminal.interactiveshell as ipt

        ipt.patch_stdout = _progress_patch_stdout
        _force_headless_matplotlib()
        ipshell[0] = InteractiveShellEmbed(user_ns=script_globals)
        ipshell[0].mainloop()

    t = threading.Thread(target=launch_shell, name="IPythonEmbedder", daemon=True)
    t.start()

    def exit_shell():
        if ipshell[0] is None:
            return
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        sys.stdout.flush()
        sys.stderr.flush()
        ipshell[0].ask_exit()
        ipshell[0].run_cell("import os; os._exit(0)")

    app.on_exit(exit_shell)
    return worker


def _lower_thread_priority():
    """Lower the calling thread's scheduling priority.

    On Linux this sets per-thread niceness so the script thread yields
    CPU time more readily to the GUI / render threads.
    On Windows it uses SetThreadPriority to achieve the same effect.
    Silently ignored on platforms where it is not supported.
    """
    try:
        import sys

        if sys.platform == "win32":
            import ctypes

            THREAD_PRIORITY_BELOW_NORMAL = -1
            handle = ctypes.windll.kernel32.GetCurrentThread()
            ctypes.windll.kernel32.SetThreadPriority(
                handle, THREAD_PRIORITY_BELOW_NORMAL
            )
        else:
            import os
            import threading

            os.setpriority(
                os.PRIO_PROCESS, threading.get_native_id(), 10
            )
    except Exception:
        pass


def _force_headless_matplotlib():
    """Force matplotlib onto the headless ``Agg`` backend.
    """
    try:
        import matplotlib

        matplotlib.use("Agg", force=True)
    except Exception:
        pass


def _run_script(
    code: str, script_globals: dict, app
) -> tuple[threading.Thread, threading.Event]:
    """Run user code with optional IPython; fall back to plain exec.

    Returns ``(worker_thread, done_event)`` where *done_event* is set
    when the initial code execution finishes (or is cancelled).
    """
    done_event = threading.Event()
    try:
        thread = _launch_interactive_shell(code, script_globals, app, done_event)
    except ImportError:
        print("IPython is not installed, skipping interactive shell.")

        def _run_and_signal():
            _lower_thread_priority()
            _force_headless_matplotlib()
            try:
                exec(code, script_globals)
            except (SystemExit, KeyboardInterrupt):
                pass
            finally:
                done_event.set()

        thread = threading.Thread(
            target=_run_and_signal, name="PythonRunner", daemon=True
        )
        thread.start()
    return thread, done_event


# Dispatch table mapping types to default name + component
_DRAW_DISPATCH: dict[type, tuple[str, type]] = {
    ngocc.OCCGeometry: ("Geometry", GeometryComponent),
    ngs.Mesh: ("Mesh", MeshComponent),
    ngs.Region: ("Mesh", MeshComponent),
    ngs.CoefficientFunction: ("Function", FunctionComponent),
}


def _is_plot_candidate(obj: Any) -> bool:
    if isinstance(obj, (list, tuple)):
        return any(_is_plot_candidate(item) for item in obj)
    if isinstance(obj, dict):
        return any(key in obj for key in ("data", "layout", "frames"))
    mod = type(obj).__module__
    return mod.startswith("plotly.") or mod.startswith("matplotlib.")


def DrawImpl(
    obj: Any,
    mesh: ngs.Mesh | ngs.Region | None = None,
    name: str | None = None,
    **kwargs,
):
    """
    Dispatch objects drawn by NGSolve into the GUI.

    Supported targets:
      - `TopoDS_Shape`/`OCCGeometry` → `GeometryComponent`
      - `Mesh`/`Region` → `MeshComponent`
      - `CoefficientFunction` (or `GridFunction`) → `FunctionComponent`

    Provide `mesh` for general coefficient functions; grid functions use their space
    mesh automatically. The function returns the created component instance.
    """
    data = dict(**kwargs)
    if isinstance(obj, ngocc.TopoDS_Shape):
        obj = ngocc.OCCGeometry(obj)
    if isinstance(obj, ngs.GridFunction):
        if mesh is None:
            mesh = obj.space.mesh
    if mesh is not None:
        data["mesh"] = mesh

    if _is_plot_candidate(obj):
        from .plot import PlotComponent

        data["obj"] = obj
        return _appdata.add_tab(name or "Plot", PlotComponent, data, _appdata)

    if type(obj) not in _DRAW_DISPATCH:
        try:
            # try to convert to CoefficientFunction
            obj = ngs.CF(obj)
            default_name, comp = _DRAW_DISPATCH[ngs.CF]
        except:
            raise TypeError(f"Unsupported object type for Draw: {type(obj)}")
    else:
        default_name, comp = _DRAW_DISPATCH[type(obj)]
    data["obj"] = obj
    return _appdata.add_tab(name or default_name, comp, data, _appdata)


def RedrawImpl(*args, **kwargs):
    if _redraw_func is not None:
        _redraw_func(*args, **kwargs)


ngs.Draw = DrawImpl
ngs.Redraw = RedrawImpl

_custom_loaders: list[Callable[[str, Any], bool]] = []


def register_file_loader(loader: Callable[[str, Any], bool]):
    """
    Register a custom file loader function.

    :param loader: A function that takes a filename and an NgApp instance,
                   and returns True if it successfully loaded the file.
    """
    _custom_loaders.append(loader)


def load_file(filename, app):
    """
    Load a file and store its content in the provided AppData instance.

    :param filename: The path to the file to be loaded.
    :param app: The running application instance providing app data and redraw hooks.
    :return: ``(thread, done_event)`` tuple, or ``None`` if no loading was started.
    """
    global _appdata, _redraw_func
    _appdata = app.app_data
    _redraw_func = app.redraw
    if filename is None:
        return None

    filename = str(filename)
    for loader in _custom_loaders:
        if loader(filename, app):
            return None

    path = Path(filename)
    name = path.stem
    code = _build_loader_snippet(filename, name)
    script_globals = {"__name__": "__main__"}
    return _run_script(code, script_globals, app)


def DrawBadElements(mesh: ngs.Mesh, threshold_3d=100, threshold_2d=20, intorder=4):
    from ngsolve import Norm, Inv, specialcf

    cf = Norm(specialcf.JacobianMatrix(3, 3)) * Norm(
        Inv(specialcf.JacobianMatrix(3, 3))
    )

    intrule = ngs.IntegrationRule(ngs.ET.TET, intorder)
    pnts = mesh.MapToAllElements(intrule, ngs.VOL).flatten()
    vals: np.ndarray = cf(pnts)
    n = len(intrule)
    vals = vals.reshape((-1, n))
    max_val = np.max(vals, axis=1)
    el3d_bitarray = max_val > threshold_3d

    print("maximum 3d badness:", np.max(max_val))

    cf = ngs.BoundaryFromVolumeCF(cf)
    intrule = ngs.IntegrationRule(ngs.ET.TRIG, intorder)
    pnts = mesh.MapToAllElements(intrule, ngs.BND).flatten()
    vals = cf(pnts)
    n = len(intrule)
    vals = vals.reshape((-1, n))
    max_val = np.max(vals, axis=1)
    el2d_bitarray = max_val > threshold_2d
    el2d_bitarray = None

    n3d = np.sum(el3d_bitarray) if el3d_bitarray is not None else 0
    print("Found", n3d, "bad 3D elements")
    if n3d == 0:
        print("No bad elements found.")
        return

    _appdata.add_tab(
        "Bad Elements",
        MeshComponent,
        mesh,
        _appdata,
        el2d_bitarray=el2d_bitarray,
        el3d_bitarray=el3d_bitarray,
    )


ngs.DrawBadElements = DrawBadElements
