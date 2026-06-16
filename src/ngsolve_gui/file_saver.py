from ngapp.utils import get_environment


def save_file_dialog(data, filename):
    """Open the browser's native "save as" dialog and write ``data`` to it.

    Uses the same File System Access API path as the "Save Project" button
    (``Environment.save_file_local``), so the user picks where the file goes.

    :param data: ``bytes`` (or ``str``) to write to disk.
    :param filename: Suggested file name, including extension.
    """
    try:
        get_environment().save_file_local(data, filename)
    except Exception:
        # showSaveFilePicker raises AbortError when the user cancels.
        pass
