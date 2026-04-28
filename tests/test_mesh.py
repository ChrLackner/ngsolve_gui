"""Visual regression tests for mesh rendering.

Each test draws a mesh, then chains multiple UI interactions (toggle wireframe,
toggle elements, shrink, etc.) asserting a baseline after every step.
Interactions use Playwright to click actual UI controls.
"""

from __future__ import annotations

from playwright.sync_api import Page

from ngapp.e2e import app_test
from ngapp.e2e_webgpu import assert_matches_baseline

from .helpers import (
    _draw,
    make_mesh_2d,
    make_mesh_3d,
    expand_section,
    collapse_section,
    click_checkbox,
    set_slider,
)


@app_test("ngsolve_gui.appconfig")
def test_mesh_2d(page: Page, app) -> None:
    """2D mesh: default → no wireframe → wireframe only."""
    mesh = make_mesh_2d()
    _draw(app, mesh, name="Mesh2D")
    comp = app.tab_panel.comp
    # 1. Default rendering (wireframe + surface elements)
    assert_matches_baseline(page, comp.wgpu, "mesh_2d_default.png")

    # 2. Expand "View", turn wireframe off via UI
    expand_section(page, "View")
    click_checkbox(page, "Wireframe")
    assert_matches_baseline(page, comp.wgpu, "mesh_2d_no_wireframe.png")

    # 3. Turn wireframe back on, turn elements off → wireframe only
    click_checkbox(page, "Wireframe")
    click_checkbox(page, "Elements 2D")
    assert_matches_baseline(page, comp.wgpu, "mesh_2d_wireframe_only.png")


@app_test("ngsolve_gui.appconfig")
def test_mesh_3d(page: Page, app) -> None:
    """3D mesh: default → no wireframe → clipping → volume+shrink."""
    mesh = make_mesh_3d()
    _draw(app, mesh, name="Mesh3D")
    comp = app.tab_panel.comp
    # 1. Default rendering (wireframe + surface elements)
    assert_matches_baseline(page, comp.wgpu, "mesh_3d_default.png")

    # 2. Expand "View", turn wireframe off via UI
    expand_section(page, "View")
    click_checkbox(page, "Wireframe")
    assert_matches_baseline(page, comp.wgpu, "mesh_3d_no_wireframe.png")

    # 3. Wireframe back on, enable clipping plane via UI
    click_checkbox(page, "Wireframe")
    collapse_section(page, "View")
    expand_section(page, "Clipping")
    click_checkbox(page, "Enable Clipping")
    assert_matches_baseline(page, comp.wgpu, "mesh_3d_clipped.png")

    # 4. Enable volume elements (shrunk) via UI
    collapse_section(page, "Clipping")
    expand_section(page, "View")
    click_checkbox(page, "Elements 3D")
    set_slider(page, 0.8)
    assert_matches_baseline(page, comp.wgpu, "mesh_3d_volume_shrink.png")

    # 5. Change shrink to 0.5
    set_slider(page, 0.5)
    assert_matches_baseline(page, comp.wgpu, "mesh_3d_volume_shrink_low.png")
