"""Visual regression tests for PlotComponent rendering.

Uses Playwright element screenshots compared against baselines via
assert_matches_baseline, targeting the rendered plotly container in the DOM.
"""

from __future__ import annotations

from playwright.sync_api import Page

from ngapp.e2e import app_test
from ngapp.e2e_webgpu import assert_matches_baseline

from .helpers import _draw


@app_test("ngsolve_gui.appconfig")
def test_plot_single_figure(page: Page, app) -> None:
    """Single plotly scatter figure renders correctly."""
    import plotly.graph_objects as go
    from ngsolve_gui.plot import PlotComponent

    fig = go.Figure(data=go.Scatter(x=[1, 2, 3], y=[1, 4, 9]))
    _draw(app, fig, name="SinglePlot")

    comp = app.tab_panel.comp
    assert isinstance(comp, PlotComponent)

    page.wait_for_timeout(100)
    locator = page.locator(".js-plotly-plot").first
    assert_matches_baseline(page, locator, "plot_single_scatter.png")


@app_test("ngsolve_gui.appconfig")
def test_plot_bar_chart(page: Page, app) -> None:
    """Single plotly bar chart renders correctly."""
    import plotly.graph_objects as go

    fig = go.Figure(data=go.Bar(x=["A", "B", "C"], y=[10, 20, 15]))
    _draw(app, fig, name="BarPlot")

    page.wait_for_timeout(100)
    locator = page.locator(".js-plotly-plot").first
    assert_matches_baseline(page, locator, "plot_bar_chart.png")


@app_test("ngsolve_gui.appconfig")
def test_plot_with_layout(page: Page, app) -> None:
    """Plotly figure with title and axis labels renders correctly."""
    import plotly.graph_objects as go

    fig = go.Figure(
        data=go.Scatter(x=[0, 1, 2], y=[0, 1, 4], mode="lines+markers"),
        layout=go.Layout(
            title="Quadratic",
            xaxis_title="X",
            yaxis_title="Y",
        ),
    )
    _draw(app, fig, name="LayoutPlot")

    page.wait_for_timeout(100)
    locator = page.locator(".js-plotly-plot").first
    assert_matches_baseline(page, locator, "plot_with_layout.png")


@app_test("ngsolve_gui.appconfig")
def test_plot_dict_figure(page: Page, app) -> None:
    """A plain dict is accepted and rendered as a plotly figure."""
    fig_dict = {"data": [{"type": "scatter", "x": [1, 2, 3], "y": [2, 4, 6]}]}
    _draw(app, fig_dict, name="DictPlot")

    page.wait_for_timeout(100)
    locator = page.locator(".js-plotly-plot").first
    assert_matches_baseline(page, locator, "plot_dict_figure.png")


@app_test("ngsolve_gui.appconfig")
def test_plot_multiple_figures(page: Page, app) -> None:
    """Two figures produce two plotly containers; screenshot the page area."""
    import plotly.graph_objects as go

    fig1 = go.Figure(data=go.Scatter(x=[1, 2, 3], y=[1, 4, 9]))
    fig2 = go.Figure(data=go.Bar(x=["A", "B", "C"], y=[10, 20, 15]))
    _draw(app, [fig1, fig2], name="MultiPlot")

    page.wait_for_selector(".js-plotly-plot >> nth=1", timeout=10000)
    page.wait_for_timeout(500)
    plots = page.locator(".js-plotly-plot")
    assert_matches_baseline(page, plots.first, "plot_multi_first.png")
    assert_matches_baseline(page, plots.nth(1), "plot_multi_second.png")
