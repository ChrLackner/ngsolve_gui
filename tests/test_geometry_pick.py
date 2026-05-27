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
    # Recompute center since assert_matches_baseline resizes the canvas
    x, y = _canvas_center(page)
    page.mouse.click(x, y)
    page.wait_for_timeout(500)
    assert_matches_baseline(page, comp.wgpu, "geometry_pick_selected.png")

    # Verify component selection state
    assert len(comp._selected_items) == 1
    assert comp._selected_items[0][0] == "face"

    # 3. Click a different position (top-right corner, likely background)
    bx, by = _canvas_pos(page, 0.95, 0.95)
    page.mouse.click(bx, by)
    page.wait_for_timeout(500)
    assert_matches_baseline(page, comp.wgpu, "geometry_pick_deselected.png")

    # 4. Switch to solid pick mode, hover → solid highlight
    comp.pick_solid.value = True
    page.wait_for_timeout(300)
    x, y = _canvas_center(page)
    page.mouse.move(x, y)
    page.wait_for_timeout(500)
    assert_matches_baseline(page, comp.wgpu, "geometry_pick_solid_hover.png")

    # 5. Click solid → solid selected (all faces of solid highlighted)
    x, y = _canvas_center(page)
    page.mouse.click(x, y)
    page.wait_for_timeout(500)
    assert_matches_baseline(page, comp.wgpu, "geometry_pick_solid_selected.png")
    assert len(comp._selected_items) == 1
    assert comp._selected_items[0][0] == "solid"
