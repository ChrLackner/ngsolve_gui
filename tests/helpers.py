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


def make_geometry_named():
    import netgen.occ as occ

    box = occ.Box(occ.Pnt(0, 0, 0), occ.Pnt(1, 1, 1))
    box.faces.Min(occ.X).name = "left"
    box.faces.Max(occ.X).name = "right"
    box.faces.Min(occ.Y).name = "front"
    box.faces.Max(occ.Y).name = "back"
    box.faces.Min(occ.Z).name = "bottom"
    box.faces.Max(occ.Z).name = "top"
    return occ.OCCGeometry(box)


# ---------------------------------------------------------------------------
# Playwright UI interaction helpers
# ---------------------------------------------------------------------------


def expand_section(page: Page, name: str) -> None:
    """Toggle a property section open/closed.

    Works for the designer "psec" sections (banded header) and for the inline
    "More options" / "Advanced" disclosures.
    """
    # Match a section header or an inline disclosure; click auto-waits for it.
    page.locator(".cb-psec-head, .cb-psec-more").filter(has_text=name).first.click()
    page.wait_for_timeout(300)


def collapse_section(page: Page, name: str) -> None:
    """Collapse a sidebar section (same click as expand — it's a toggle)."""
    expand_section(page, name)


def click_checkbox(page: Page, name: str) -> None:
    """Toggle a boolean control by its label.

    Matches the designer widgets in priority order: option chip, toggle switch,
    pick pill, then a plain Quasar checkbox.
    """
    chip = page.locator(".cb-opt-chip").filter(has_text=name)
    if chip.count() > 0:
        chip.first.click()
    else:
        tog = page.locator(".cb-toggle").filter(has_text=name)
        if tog.count() > 0:
            tog.first.locator(".cb-switch").click()
        else:
            pill = page.locator(".cb-chk-pill").filter(has_text=name)
            if pill.count() > 0:
                pill.first.click()
            else:
                page.get_by_role("checkbox", name=name, exact=True).click()
    page.wait_for_timeout(100)


def fill_input(page: Page, label: str, value: str) -> None:
    """Clear and fill a field input identified by its (designer) field label."""
    fld = page.locator(".cb-field").filter(has_text=label)
    inp = fld.first.locator("input") if fld.count() > 0 else page.get_by_label(label)
    inp.clear()
    inp.fill(value)
    inp.press("Enter")
    page.wait_for_timeout(100)


def click_curving_checkbox(page: Page) -> None:
    """Toggle the 'Curved display' switch in the mesh Display section."""
    page.locator(".cb-toggle").filter(has_text="Curved display").first \
        .locator(".cb-switch").click()
    page.wait_for_timeout(500)


def set_slider(
    page: Page, value: float, *, label: str | None = None, min_val: float = 0.0, max_val: float = 1.0
) -> None:
    """Set a Quasar slider by clicking at the proportional position.

    When *label* is given, targets the slider in the same field/row as that
    label text. Otherwise falls back to the first slider on the page.
    """
    if label:
        container = page.locator(".cb-field").filter(has_text=label)
        if container.count() == 0:
            container = page.locator(".row, [class*='row']").filter(has_text=label)
        slider = container.first.get_by_role("slider").first
    else:
        slider = page.get_by_role("slider").first
    box = slider.bounding_box()
    if box is None:
        raise AssertionError("Slider not visible")
    fraction = (value - min_val) / (max_val - min_val)
    x = box["x"] + box["width"] * fraction
    y = box["y"] + box["height"] / 2
    page.mouse.click(x, y)
    page.wait_for_timeout(100)
