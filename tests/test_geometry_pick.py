"""Tests for geometry hover highlighting and click selection."""

from __future__ import annotations

from playwright.sync_api import Page

from ngapp.e2e import app_test
from ngapp.e2e_webgpu import assert_matches_baseline

from .helpers import _draw, make_geometry_named


def _canvas_center(page):
    box = page.locator("canvas").bounding_box()
    return box["x"] + box["width"] / 2, box["y"] + box["height"] / 2


def _canvas_pos(page, rx, ry):
    box = page.locator("canvas").bounding_box()
    return box["x"] + box["width"] * rx, box["y"] + box["height"] * ry


@app_test("ngsolve_gui.appconfig")
def test_geometry_pick(page: Page, app) -> None:
    """Hover highlights, click selects with panel update, background click deselects."""
    geo = make_geometry_named()
    _draw(app, geo, name="GeoPick")
    comp = app.tab_panel.comp

    # 1. Hover over center face → highlight
    x, y = _canvas_center(page)
    page.mouse.move(x, y)
    page.wait_for_timeout(500)
    assert_matches_baseline(page, comp.wgpu, "geometry_pick_hover.png")

    # 2. Click face → selection
    page.mouse.click(x, y)
    page.wait_for_timeout(500)
    assert_matches_baseline(page, comp.wgpu, "geometry_pick_selected.png")

    # Verify selection panel is active with correct content
    sel = comp._selection_section
    assert sel.meshsize_input.ui_disable is False
    assert sel.name_input.ui_disable is False
    assert "Face" in sel._heading.ui_children[0]
    assert sel.name_input.ui_model_value != ""

    # 3. Click background → deselect
    bx, by = _canvas_pos(page, 0.05, 0.05)
    page.mouse.click(bx, by)
    page.wait_for_timeout(500)
    assert_matches_baseline(page, comp.wgpu, "geometry_pick_deselected.png")

    assert sel.meshsize_input.ui_disable is True
    assert sel.name_input.ui_disable is True
