"""Visual regression tests for vector CoefficientFunction rendering."""

from __future__ import annotations

import numpy as np
import ngsolve as ngs

from playwright.sync_api import Page
from ngapp.e2e import app_test

from ngapp.e2e_webgpu import assert_matches_baseline

from .helpers import (
    _draw,
    make_mesh_2d,
    make_mesh_3d,
    click_in_section,
    toggle_clipping,
)


@app_test("ngsolve_gui.appconfig")
def test_function_vector_2d(page: Page, app) -> None:
    """2D vector CF: default → surface vectors."""
    mesh = make_mesh_2d()
    cf = ngs.CF((ngs.x, ngs.y))
    _draw(app, cf, mesh=mesh, name="Vec2D")
    comp = app.tab_panel.comp

    assert_matches_baseline(page, comp.wgpu, "func_vector_2d_default.png")

    click_in_section(page, "Vectors & Flow", "Surface")
    assert_matches_baseline(page, comp.wgpu, "func_vector_2d_surface_vectors.png")


@app_test("ngsolve_gui.appconfig")
def test_function_vector_3d(page: Page, app) -> None:
    """3D vector CF: enable clipping → clipping vectors → surface vectors."""
    mesh = make_mesh_3d()
    cf = ngs.CF((ngs.x, ngs.y, ngs.z))
    _draw(app, cf, mesh=mesh, name="Vec3D")
    comp = app.tab_panel.comp

    assert_matches_baseline(page, comp.wgpu, "func_vector_3d_default.png")

    # Enable clipping first so the clipping plane is visible
    toggle_clipping(page)
    assert_matches_baseline(page, comp.wgpu, "func_vector_3d_clipped.png")

    # Show clipping vectors (only meaningful with clipping enabled)
    click_in_section(page, "Vectors & Flow", "Clip")
    assert_matches_baseline(page, comp.wgpu, "func_vector_3d_clipping_vectors.png")

    # Switch to surface vectors
    click_in_section(page, "Vectors & Flow", "Clip")
    click_in_section(page, "Vectors & Flow", "Surface")
    assert_matches_baseline(page, comp.wgpu, "func_vector_3d_surface_vectors.png")


@app_test("ngsolve_gui.appconfig")
def test_function_fieldlines_2d(page: Page, app) -> None:
    """2D vector CF with field lines."""
    mesh = make_mesh_2d()
    cf = ngs.CF((ngs.y, -ngs.x))
    _draw(app, cf, mesh=mesh, name="FieldLines2D")
    comp = app.tab_panel.comp

    np.random.seed(42)
    click_in_section(page, "Vectors & Flow", "Streamlines")
    assert_matches_baseline(page, comp.wgpu, "func_fieldlines_2d.png")
