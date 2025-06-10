import netgen.occ as ngocc
import ngsolve as ngs
from .app_data import AppData
import threading

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
        assert name is not None, "Name must be provided for CoefficientFunction"
        _appdata.add_function(name, obj, mesh)


ngs.Draw = DrawImpl


def run_python(filename, app_data):
    global _appdata
    _appdata = app_data
    t = threading.Thread(
        target=exec, args=(open(filename).read(),), name="PythonRunner"
    )
    t.daemon = True
    t.start()
    return t
