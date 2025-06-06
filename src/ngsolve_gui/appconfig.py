from ngapp import AppConfig

from . import __version__
from .app import NGSolveGui

_DESCRIPTION = """A short description"""

config = AppConfig(
    name="NGSolve GUI",
    version=__version__,
    python_class=NGSolveGui,
    frontend_pip_dependencies=["ngsolve", "ngsolve_webgpu"],
    description=_DESCRIPTION,
)
