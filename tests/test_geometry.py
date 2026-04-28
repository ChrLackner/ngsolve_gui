"""Visual regression tests for OCC geometry rendering.

Single chained test: default → hide edges → enable clipping.
Interactions use Playwright to click actual UI controls.
"""

from __future__ import annotations

from playwright.sync_api import Page

from ngapp.e2e import app_test
from ngapp.e2e_webgpu import assert_matches_baseline

from .helpers import (
    _draw,
    make_geometry,
    expand_section,
    click_checkbox,
)


@app_test("ngsolve_gui.appconfig")
def test_geometry_box(page: Page, app) -> None:
    """Box geometry: default → no edges → clipped."""
    geo = make_geometry()
    _draw(app, geo, name="Geometry")
    comp = app.tab_panel.comp
    # 1. Default rendering (faces + edges)
    assert_matches_baseline(page, comp.wgpu, "geometry_box_default.png")

    # 2. Hide edges via UI checkbox
    click_checkbox(page, "Show Edges")
    assert_matches_baseline(page, comp.wgpu, "geometry_box_no_edges.png")

    # 3. Re-enable edges, enable clipping plane via UI
    click_checkbox(page, "Show Edges")
    expand_section(page, "Clipping")
    click_checkbox(page, "Enable Clipping")
    assert_matches_baseline(page, comp.wgpu, "geometry_box_clipped.png")
