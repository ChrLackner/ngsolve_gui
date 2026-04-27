"""Visual regression tests for additional mesh features."""

from __future__ import annotations

import ngsolve as ngs

from playwright.sync_api import Page

from ngapp.e2e import app_test
from ngapp.e2e_webgpu import assert_matches_baseline

from .helpers import (
    _draw, make_mesh_2d, make_mesh_3d,
    make_mesh_2d_circle, make_mesh_3d_sphere,
    expand_section, click_checkbox, click_curving_checkbox,
)


@app_test("ngsolve_gui.appconfig")
def test_mesh_elements_1d(page: Page, app) -> None:
    """2D mesh: default (1D off) → toggle 1D elements on."""
    mesh = make_mesh_2d()
    _draw(app, mesh, name="Mesh1D")
    comp = app.tab_panel.comp

    assert_matches_baseline(page, comp.wgpu, "mesh_2d_elements1d_off.png")

    expand_section(page, "View")
    click_checkbox(page, "Elements 1D")
    assert_matches_baseline(page, comp.wgpu, "mesh_2d_elements1d_on.png")


@app_test("ngsolve_gui.appconfig")
def test_mesh_curving_2d(page: Page, app) -> None:
    """2D circle mesh: linear (default) → enable curving to see smooth boundary."""
    mesh = make_mesh_2d_circle()
    _draw(app, mesh, name="CurveCircle")
    comp = app.tab_panel.comp

    assert_matches_baseline(page, comp.wgpu, "mesh_circle_curved_off.png")

    click_curving_checkbox(page)
    assert_matches_baseline(page, comp.wgpu, "mesh_circle_curved_on.png")


@app_test("ngsolve_gui.appconfig")
def test_mesh_curving_3d(page: Page, app) -> None:
    """3D sphere mesh: linear (default) → enable curving to see smooth surface."""
    mesh = make_mesh_3d_sphere()
    _draw(app, mesh, name="CurveSphere")
    comp = app.tab_panel.comp

    assert_matches_baseline(page, comp.wgpu, "mesh_sphere_curved_off.png")

    click_curving_checkbox(page)
    assert_matches_baseline(page, comp.wgpu, "mesh_sphere_curved_on.png")


@app_test("ngsolve_gui.appconfig")
def test_mesh_region_boundary(page: Page, app) -> None:
    """Draw a volume region of a 3D mesh."""
    mesh = make_mesh_3d()
    region = mesh.Boundaries("left|right")
    _draw(app, region, name="BndRegion")
    comp = app.tab_panel.comp

    assert_matches_baseline(page, comp.wgpu, "mesh_region_boundary.png")
