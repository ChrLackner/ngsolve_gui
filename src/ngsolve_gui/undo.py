"""Small generic undo stack for viewport actions.

Keeps the last few undoable actions (default 5) as (label, undo-callable)
pairs. Actions register how to revert themselves when they run; ``undo()``
pops and executes the most recent one. Used first by the region hide/isolate
feature so a wrong hide is one keypress away, but deliberately generic so
other tab actions (clipping changes, camera bookmarks, ...) can adopt it.
"""


class UndoStack:
    def __init__(self, limit=5):
        self._limit = limit
        self._items = []  # list of (label, undo_fn), newest last

    def push(self, label, undo_fn):
        """Register an undoable action. ``undo_fn`` takes no arguments and
        restores the state from before the action."""
        self._items.append((label, undo_fn))
        if len(self._items) > self._limit:
            del self._items[: len(self._items) - self._limit]

    @property
    def can_undo(self):
        return bool(self._items)

    def undo(self):
        """Revert the most recent action. Returns its label, or None if the
        stack was empty."""
        if not self._items:
            return None
        label, undo_fn = self._items.pop()
        undo_fn()
        return label

    def clear(self):
        self._items.clear()
