"""Visual regression tests for CoefficientFunction rendering.

Three chained tests:
- 2D scalar: default (with auto z-deformation) → no wireframe → deformation off
- 3D scalar: default → clipping enabled
- Colormap: default → discrete → custom range

Interactions use Playwright to click actual UI controls.
"""

from __future__ import annotations

import ngsolve as ngs

from playwright.sync_api import Page
from ngapp.e2e import app_test

from ngapp.e2e_webgpu import assert_matches_baseline

from .helpers import (
    _draw,
    make_mesh_2d,
    make_mesh_3d,
    click_checkbox,
    toggle_clipping,
    toggle_deformation,
    open_colorbar_options,
    toggle_autoscale,
    set_colorbar_range,
)


@app_test("ngsolve_gui.appconfig")
def test_function_scalar_2d(page: Page, app) -> None:
    """2D scalar x*y: default (deformed) → no wireframe → deformation off."""
    mesh = make_mesh_2d()
    cf = ngs.x * ngs.y
    _draw(app, cf, mesh=mesh, name="Scalar2D")
    comp = app.tab_panel.comp
    # 1. Default rendering (colormap + wireframe + auto z-deformation)
    assert comp.deformation is not None
    assert_matches_baseline(page, comp.wgpu, "func_scalar_2d_default.png")

    # 2. Turn wireframe off via UI
    click_checkbox(page, "Wireframe")
    assert_matches_baseline(page, comp.wgpu, "func_scalar_2d_no_wireframe.png")

    # 3. Turn wireframe back on, disable deformation via UI (the Deformation
    #    section header is itself the on/off switch in the redesign)
    click_checkbox(page, "Wireframe")
    toggle_deformation(page)
    assert_matches_baseline(page, comp.wgpu, "func_scalar_2d_flat.png")


@app_test("ngsolve_gui.appconfig")
def test_function_scalar_3d(page: Page, app) -> None:
    """3D scalar x+y+z: default → clipping enabled."""
    mesh = make_mesh_3d()
    cf = ngs.x + ngs.y + ngs.z
    _draw(app, cf, mesh=mesh, name="Scalar3D")
    comp = app.tab_panel.comp
    # 1. Default rendering
    assert_matches_baseline(page, comp.wgpu, "func_scalar_3d_default.png")

    # 2. Enable clipping plane via the viewport tool
    toggle_clipping(page)
    assert_matches_baseline(page, comp.wgpu, "func_scalar_3d_clipped.png")


@app_test("ngsolve_gui.appconfig")
def test_function_colormap(page: Page, app) -> None:
    """3D scalar with colormap changes: default → discrete → custom range."""
    mesh = make_mesh_3d()
    cf = ngs.x + ngs.y + ngs.z
    _draw(app, cf, mesh=mesh, name="ColormapTest")
    comp = app.tab_panel.comp
    # 1. Default colormap (jet, autoscale)
    assert_matches_baseline(page, comp.wgpu, "func_colormap_default.png")

    # 2. Enable discrete mode via the colorbar legend's options popover
    open_colorbar_options(page)
    click_checkbox(page, "Discrete")
    assert_matches_baseline(page, comp.wgpu, "func_colormap_discrete.png")

    # 3. Disable discrete, disable autoscale, set custom min/max via the
    #    in-viewport colorbar legend
    click_checkbox(page, "Discrete")
    toggle_autoscale(page)
    set_colorbar_range(page, minval=0.5, maxval=2.0)
    assert_matches_baseline(page, comp.wgpu, "func_colormap_custom_range.png")
