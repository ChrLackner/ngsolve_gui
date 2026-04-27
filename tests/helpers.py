"""Shared helpers for ngsolve-gui e2e tests."""

from __future__ import annotations

from playwright.sync_api import Page


def _setup_file_loader(app):
    """Wire the file_loader globals to point at the running app."""
    import ngsolve_gui.file_loader as fl

    fl._appdata = app.app_data
    fl._redraw_func = app.redraw


def _draw(app, obj, **kwargs):
    """Draw an object into the app via the file_loader dispatch."""
    _setup_file_loader(app)
    from ngsolve_gui.file_loader import DrawImpl

    DrawImpl(obj, **kwargs)
    app._update()


def make_mesh_2d():
    import ngsolve as ngs
    import netgen.occ as occ

    rect = occ.Rectangle(1, 1).Face()
    rect.edges.Min(occ.X).name = "left"
    rect.edges.Max(occ.X).name = "right"
    rect.edges.Min(occ.Y).name = "bottom"
    rect.edges.Max(occ.Y).name = "top"
    geo = occ.OCCGeometry(rect, dim=2)
    return ngs.Mesh(geo.GenerateMesh(maxh=0.3))


def make_mesh_3d():
    import ngsolve as ngs
    import netgen.occ as occ

    box = occ.Box(occ.Pnt(0, 0, 0), occ.Pnt(1, 1, 1))
    box.faces.Min(occ.X).name = "left"
    box.faces.Max(occ.X).name = "right"
    box.faces.Min(occ.Y).name = "bottom"
    box.faces.Max(occ.Y).name = "top"
    box.faces.Min(occ.Z).name = "back"
    box.faces.Max(occ.Z).name = "front"
    geo = occ.OCCGeometry(box)
    return ngs.Mesh(geo.GenerateMesh(maxh=0.5))


def make_mesh_2d_circle():
    import ngsolve as ngs
    import netgen.occ as occ

    w = occ.Wire(occ.Circle(occ.Pnt(0, 0, 0), occ.Dir(0, 0, 1), 1))
    face = occ.Face(w)
    geo = occ.OCCGeometry(face, dim=2)
    return ngs.Mesh(geo.GenerateMesh(maxh=0.5))


def make_mesh_3d_sphere():
    import ngsolve as ngs
    import netgen.occ as occ

    sphere = occ.Sphere(occ.Pnt(0, 0, 0), 1)
    geo = occ.OCCGeometry(sphere)
    return ngs.Mesh(geo.GenerateMesh(maxh=0.8))


def make_geometry():
    import netgen.occ as occ

    box = occ.Box(occ.Pnt(0, 0, 0), occ.Pnt(1, 1, 1))
    return occ.OCCGeometry(box)


# ---------------------------------------------------------------------------
# Playwright UI interaction helpers
# ---------------------------------------------------------------------------

def expand_section(page: Page, name: str) -> None:
    """Expand a sidebar section by clicking its list item header."""
    page.get_by_role("listitem").filter(has_text=name).click()
    page.wait_for_timeout(300)


def collapse_section(page: Page, name: str) -> None:
    """Collapse a sidebar section (same click as expand — it's a toggle)."""
    expand_section(page, name)


def click_checkbox(page: Page, name: str) -> None:
    """Click a visible Quasar checkbox by its label text."""
    page.get_by_role("checkbox", name=name).click()
    page.wait_for_timeout(100)


def fill_input(page: Page, label: str, value: str) -> None:
    """Clear and fill a Quasar input field identified by its label."""
    field = page.get_by_label(label)
    field.clear()
    field.fill(value)
    field.press("Enter")
    page.wait_for_timeout(100)


def click_curving_checkbox(page: Page) -> None:
    """Click the unlabeled curving checkbox next to the 'Curve Order' text."""
    # The checkbox is inside a QItem row that also contains "Curve Order" text.
    # Use the listitem role to scope, then find the checkbox within it.
    row = page.get_by_role("listitem").filter(has_text="Curve Order")
    row.get_by_role("checkbox").click()
    page.wait_for_timeout(500)


def set_slider(page: Page, value: float, *, min_val: float = 0.0, max_val: float = 1.0) -> None:
    """Set a Quasar slider by clicking at the proportional position.

    Finds the first visible slider on the page and clicks at the position
    corresponding to the given value within [min_val, max_val].
    """
    slider = page.get_by_role("slider")
    box = slider.bounding_box()
    if box is None:
        raise AssertionError("Slider not visible")
    fraction = (value - min_val) / (max_val - min_val)
    x = box["x"] + box["width"] * fraction
    y = box["y"] + box["height"] / 2
    page.mouse.click(x, y)
    page.wait_for_timeout(100)
