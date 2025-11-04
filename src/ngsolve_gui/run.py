from ngapp.cli.serve_standalone import host_local_app
import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "filename", help="Load the specified file", nargs="*", default=None
    )
    parser.add_argument("--dev", action="store_true", help="Run in development mode")
    # get absolute path of file from command line
    args = parser.parse_args()
    app_args = {}
    if args.filename:
        app_args["filename"] = [Path(f).resolve() for f in args.filename]
    host_local_app(
        "ngsolve_gui.appconfig",
        watch_code=args.dev,
        app_args=app_args,
    )
