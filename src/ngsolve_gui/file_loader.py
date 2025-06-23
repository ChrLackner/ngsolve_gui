import netgen.occ as ngocc
import ngsolve as ngs
import threading
from .app_data import AppData
import asyncio

_appdata: AppData


def DrawImpl(obj, mesh=None, name=None, **kwargs):
    if isinstance(obj, ngocc.TopoDS_Shape):
        obj = ngocc.OCCGeometry(obj)
    if isinstance(obj, ngocc.OCCGeometry):
        if name is None:
            name = "Geometry"
        _appdata.add_geometry(name, obj)
    if isinstance(obj, ngs.Mesh):
        if name is None:
            name = "Mesh"
        _appdata.add_mesh(name, obj)
    if isinstance(obj, ngs.CoefficientFunction):
        if mesh is None:
            assert isinstance(
                obj, ngs.GridFunction
            ), "Mesh must be provided for CoefficientFunction"
            mesh = obj.space.mesh
            if name is None:
                name = obj.name
        assert name is not None, "Name must be provided for CoefficientFunction"
        _appdata.add_function(name, obj, mesh, **kwargs)


ngs.Draw = DrawImpl


def load_file(filename, app):
    """
    Load a file and store its content in the provided AppData instance.

    :param filename: The path to the file to be loaded.
    :param appdata: An instance of AppData to store the loaded data.
    """
    global _appdata
    _appdata = app.app_data
    if filename is None:
        return
    filename = str(filename)
    file_ending = filename.split(".")[-1].lower()
    name = filename.split("/")[-1].split(".")[0]
    if filename.endswith(".vol") or filename.endswith(".vol.gz"):
        code = f"""import ngsolve
mesh = ngsolve.Mesh({filename})
ngsolve.Draw(mesh, '{name}')"""
    elif file_ending in ["step", "iges", "stp"]:
        code = f"""import netgen.occ
import ngsolve
geometry = netgen.occ.OCCGeometry("{filename}")
ngsolve.Draw(geometry, '{name}')"""
    elif file_ending == "py":
        with open(filename, "r") as f:
            code = f.read()
    script_globals = {"__name__": "__main__"}
    try:
        import termios
        import sys

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
