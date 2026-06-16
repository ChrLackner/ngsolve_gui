"""Backend-side native "open file" dialog returning a real filesystem path.

The frontend runs in a browser whose File System Access API never exposes the
real path of a picked file (by design). Loading a ``.py`` script needs that real
path so it runs with the right ``__file__``/cwd/relative imports, so the load
dialog has to run in the backend process, which does have filesystem access.

We prefer the OS-native picker (``kdialog``/``zenity`` on Linux, ``osascript``
on macOS) for a native look, and fall back to tkinter where none is available.
"""

import os
import shutil
import subprocess
import sys

# ``(label, "ext ext ...")`` groups, mirroring tkinter's filetypes argument.
DEFAULT_FILTERS = [
    ("All Files", "*"),
    ("Mesh Files", "*.vol *.vol.gz"),
    ("Geometry Files", "*.step *.iges *.stp *.brep"),
    ("Python Files", "*.py"),
]


def open_file_dialog(title="Select a file", initialdir=None, filters=DEFAULT_FILTERS):
    """Open a native file-open dialog and return the chosen path, or ``None``."""
    initialdir = initialdir or os.path.expanduser("~")

    if sys.platform == "darwin":
        path = _osascript(title, initialdir)
    elif sys.platform.startswith("linux"):
        path = _kdialog(title, initialdir, filters) or _zenity(title, initialdir, filters)
    else:
        path = None

    if path is None:
        path = _tkinter(title, initialdir, filters)
    return path or None


def _run(cmd):
    """Run a dialog command; return stripped stdout, or None on cancel/error."""
    try:
        out = subprocess.run(cmd, capture_output=True, text=True)
    except (OSError, ValueError):
        return None
    if out.returncode != 0:
        return None  # non-zero == user cancelled (or tool missing)
    return out.stdout.strip() or None


def _kdialog(title, initialdir, filters):
    if not shutil.which("kdialog"):
        return None
    # kdialog filter syntax: "patterns|Label" entries joined by newlines.
    flt = "\n".join(f"{pats}|{label}" for label, pats in filters)
    return _run(["kdialog", "--title", title, "--getopenfilename", initialdir + "/", flt])


def _zenity(title, initialdir, filters):
    if not shutil.which("zenity"):
        return None
    cmd = ["zenity", "--file-selection", "--title", title,
           "--filename", initialdir + "/"]
    for label, pats in filters:
        cmd += ["--file-filter", f"{label} | {pats}"]
    return _run(cmd)


def _osascript(title, initialdir):
    script = (
        f'POSIX path of (choose file with prompt "{title}" '
        f'default location (POSIX file "{initialdir}"))'
    )
    return _run(["osascript", "-e", script])


def _tkinter(title, initialdir, filters):
    from tkinter import Tk, filedialog

    root = Tk()
    root.withdraw()
    try:
        return filedialog.askopenfilename(
            title=title,
            initialdir=initialdir,
            filetypes=[(label, pats) for label, pats in filters],
        )
    finally:
        root.destroy()
