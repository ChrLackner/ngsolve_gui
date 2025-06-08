import ngsolve as ngs
from .run_python import run_python


def load_file(filename, appdata):
    """
    Load a file and store its content in the provided AppData instance.

    :param filename: The path to the file to be loaded.
    :param appdata: An instance of AppData to store the loaded data.
    """
    if filename is None:
        return
    filename = str(filename)
    file_ending = filename.split(".")[-1].lower()
    name = filename.split("/")[-1].split(".")[0]
    if filename.endswith(".vol") or filename.endswith(".vol.gz"):
        mesh = ngs.Mesh(filename)
        appdata.add_mesh(name, mesh)
    elif file_ending in ["step", "iges", "stp"]:
        from netgen.occ import OCCGeometry

        geometry = OCCGeometry(filename)
        appdata.add_geometry(name, geometry)
    elif file_ending == "py":
        run_python(filename, appdata)
