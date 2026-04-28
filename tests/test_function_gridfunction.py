"""Visual regression tests for GridFunction rendering and function options."""

from __future__ import annotations

import ngsolve as ngs

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
def test_function_gridfunction(page: Page, app) -> None:
    """2D GridFunction x*y: auto-detects mesh from FESpace."""
    mesh = make_mesh_2d()
    fes = ngs.H1(mesh, order=2)
    gf = ngs.GridFunction(fes)
    gf.Set(ngs.x * ngs.y)
    _draw(app, gf, name="GF2D")
    comp = app.tab_panel.comp
    assert_matches_baseline(page, comp.wgpu, "func_gridfunction_2d_default.png")


@app_test("ngsolve_gui.appconfig")
def test_function_deformation_scale(page: Page, app) -> None:
    """2D scalar deformation scale: default → half → zero."""
    mesh = make_mesh_2d()
    cf = ngs.x**2 + ngs.y**2
    _draw(app, cf, mesh=mesh, name="DeformScale")
    comp = app.tab_panel.comp
    # 1. Default (auto deformation on for 2D scalar)
    assert_matches_baseline(page, comp.wgpu, "func_deformation_default.png")

    # 2. Set deformation scale to 0.5
    expand_section(page, "Deformation")
    set_slider(page, 0.5)
    assert_matches_baseline(page, comp.wgpu, "func_deformation_half_scale.png")

    # 3. Set deformation scale to 0.0
    set_slider(page, 0.0)
    assert_matches_baseline(page, comp.wgpu, "func_deformation_zero_scale.png")


@app_test("ngsolve_gui.appconfig")
def test_function_3d_options(page: Page, app) -> None:
    """3D scalar options: enable clipping, then toggle surface and clipping function visibility."""
    mesh = make_mesh_3d()
    cf = ngs.x + ngs.y + ngs.z
    _draw(app, cf, mesh=mesh, name="Options3D")
    comp = app.tab_panel.comp

    # 1. Enable clipping so the clipping plane is visible
    expand_section(page, "Clipping")
    click_checkbox(page, "Enable Clipping")
    assert_matches_baseline(page, comp.wgpu, "func_3d_options_clipped.png")

    # 2. Hide surface solution (clipping plane still visible)
    collapse_section(page, "Clipping")
    expand_section(page, "Options")
    click_checkbox(page, "Surface Solution Visible")
    assert_matches_baseline(page, comp.wgpu, "func_3d_options_no_surface.png")

    # 3. Re-show surface, hide clipping function
    click_checkbox(page, "Surface Solution Visible")
    click_checkbox(page, "Clipping Function")
    assert_matches_baseline(page, comp.wgpu, "func_3d_options_no_clipping_func.png")
