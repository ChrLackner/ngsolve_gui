from ngapp.cli.serve_standalone import host_local_app
import argparse
from pathlib import Path


def _apply_nthreads():
    """Read nthreads from user settings and apply before TaskManager starts."""
    try:
        import os
        from ngapp.utils import UserSettings

        settings = UserSettings(app_id="NGSolve GUI")
        nthreads = int(settings.get("nthreads", 0))
        if nthreads > 0:
            import ngsolve as ngs

            ngs.SetNumThreads(nthreads)
            os.environ["MKL_NUM_THREADS"] = str(nthreads)
    except Exception:
        pass


def _apply_gpu_preference():
    """Read GPU preference from user settings and set env var before webgpu is imported."""
    try:
        import os
        from ngapp.utils import UserSettings

        settings = UserSettings(app_id="NGSolve GUI")
        pref = settings.get("gpu_power_preference", "high-performance")
        os.environ["WEBGPU_POWER_PREFERENCE"] = pref
    except Exception:
        pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "filename", help="Load the specified file", nargs="*", default=None
    )
    parser.add_argument("--dev", action="store_true", help="Run in development mode")
    parser.add_argument(
        "--dev-frontend", action="store_true", help="Run frontend in development mode"
    )
    parser.add_argument(
        "-m",
        dest="module",
        metavar="MODULE",
        nargs=argparse.REMAINDER,
        help="Run a module as `python -m MODULE ...`; remaining args are passed to it",
    )
    # get absolute path of file from command line
    args = parser.parse_args()
    app_args = {}
    if args.filename:
        app_args["filename"] = [Path(f).resolve() for f in args.filename]
    if args.module:
        app_args["module"] = args.module[0]
        app_args["module_args"] = args.module[1:]
    _apply_gpu_preference()
    _apply_nthreads()
    from ngsolve import TaskManager
    with TaskManager():
        host_local_app(
            "ngsolve_gui.appconfig",
            watch_code=args.dev,
            dev_frontend=args.dev_frontend,
            app_args=app_args,
        )
