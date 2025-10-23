import asyncio
import threading
import numpy as np
from typing import Callable

import netgen.occ as ngocc
import ngsolve as ngs

from .app_data import AppData
from .function import FunctionComponent
from .geometry import GeometryComponent
from .mesh import MeshComponent

_appdata: AppData
_redraw_func: Callable | None = None


def DrawImpl(obj, mesh=None, name=None, **kwargs):
    if isinstance(obj, ngocc.TopoDS_Shape):
        obj = ngocc.OCCGeometry(obj)
    if isinstance(obj, ngocc.OCCGeometry):
        if name is None:
            name = "Geometry"
        _appdata.add_tab(name, GeometryComponent, obj, _appdata)
    if isinstance(obj, ngs.Mesh):
        if name is None:
            name = "Mesh"
        _appdata.add_tab(name, MeshComponent, obj, _appdata, **kwargs)
    if isinstance(obj, ngs.CoefficientFunction):
        if mesh is None:
            assert isinstance(
                obj, ngs.GridFunction
            ), "Mesh must be provided for CoefficientFunction"
            mesh = obj.space.mesh
            if name is None:
                name = obj.name
        assert name is not None, "Name must be provided for CoefficientFunction"
        data = dict(**kwargs)
        data["function"] = obj
        data["mesh"] = mesh
        # _appdata.add_function(name, obj, mesh, **kwargs)
        _appdata.add_tab(name, FunctionComponent, data, _appdata)


def RedrawImpl(*args, **kwargs):
    if _redraw_func is not None:
        _redraw_func(*args, **kwargs)


ngs.Draw = DrawImpl
ngs.Redraw = RedrawImpl

_custom_loaders = []

def register_file_loader(loader: Callable):
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
    :param appdata: An instance of AppData to store the loaded data.
    """
    global _appdata, _redraw_func
    _appdata = app.app_data
    _redraw_func = app.redraw
    if filename is None:
        return
    filename = str(filename)
    for loader in _custom_loaders:
        if loader(filename, app):
            return
    file_ending = filename.split(".")[-1].lower()
    name = filename.split("/")[-1].split(".")[0]
    if filename.endswith(".vol") or filename.endswith(".vol.gz"):
        code = f"""import ngsolve
mesh = ngsolve.Mesh('{filename}')
ngsolve.Draw(mesh, '{name}')"""
    elif file_ending in ["step", "iges", "stp", "brep"]:
        code = f"""import netgen.occ
import ngsolve
geometry = netgen.occ.OCCGeometry("{filename}")
ngsolve.Draw(geometry, '{name}')"""
    elif file_ending == "pkl":
        code = f"""import netgen.occ
import ngsolve, pickle
obj = pickle.load(open("{filename}", "rb"))
ngsolve.Draw(obj, '{name}')"""
    elif file_ending == "py":
        with open(filename, "r") as f:
            code = f.read()
    else:
        raise ValueError(f"Unsupported file type: {file_ending}")
    script_globals = {"__name__": "__main__"}
    try:
        import sys
        import termios

        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        from IPython.terminal.embed import InteractiveShellEmbed

        ipshell = [None]

        def launch_shell():
            ipshell[0] = InteractiveShellEmbed(user_ns=script_globals)
            asyncio.run(ipshell[0].run_code(compile(code, "<embedded>", "exec")))
            ipshell[0].mainloop()

        t = threading.Thread(target=launch_shell, name="IPythonEmbedder")
        t.daemon = True
        t.start()

        def exit_shell():
            if ipshell[0] is not None:
                # Restore terminal settings
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
                sys.stdout.flush()
                sys.stderr.flush()
                ipshell[0].ask_exit()
                ipshell[0].run_cell("import os; os._exit(0)")

        app.on_exit(exit_shell)
    except ImportError:
        print("IPython is not installed, skipping interactive shell.")
        t = threading.Thread(
            target=exec, args=(code, script_globals), name="PythonRunner"
        )
        t.daemon = True
        t.start()


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
