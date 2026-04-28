from __future__ import annotations

from ngapp.components import *
from ngapp.components.visualization import PlotlyComponent


class PlotComponent(Div):
    def __init__(self, name, data, app_data):
        self.name = name
        self.data = data
        self.app_data = app_data
        self.icon = "mdi-chart-line"
        self._figures = []
        self._plots = []
        self.debug = bool(data.get("debug", False)) if isinstance(data, dict) else False
        self.container = Div(
            ui_style="width: 100%; height: 100%; overflow: auto;"
        )
        super().__init__(
            self.container,
            ui_style="width: 100%; height: 100%;",
        )
        self.on_mounted(self.draw)  # defer until mounted

    @property
    def title(self):
        return self.app_data.get_tab(self.name)["title"]

    def _normalize_figures(self, obj):
        if obj is None:
            return []
        if isinstance(obj, (list, tuple)):
            figures = []
            for item in obj:
                if isinstance(item, (list, tuple)):
                    figures.extend(item)
                else:
                    figures.append(item)
            return figures
        return [obj]

    def _to_plotly(self, fig):
        try:
            import plotly.graph_objects as go

            if isinstance(fig, go.Figure):
                return fig
            if isinstance(fig, dict):
                return go.Figure(fig)
            if hasattr(fig, "to_plotly_json"):
                return go.Figure(fig.to_plotly_json())
        except Exception:
            pass

        try:
            import matplotlib.figure
            import matplotlib.axes

            if isinstance(fig, matplotlib.axes.Axes):
                fig = fig.figure
            if isinstance(fig, matplotlib.figure.Figure):
                try:
                    from plotly.io import from_matplotlib
                except Exception:
                    from plotly.tools import mpl_to_plotly

                    return mpl_to_plotly(fig)

                return from_matplotlib(fig)
        except Exception:
            pass

        return None

    def draw(self):
        obj = self.data.get("obj") if isinstance(self.data, dict) else self.data
        figures = self._normalize_figures(obj)

        self._figures = []
        self._plots = []
        plot_height = "100%" if len(figures) == 1 else "480px"
        if self.debug:
            print(f"[PlotComponent] figures={len(figures)}")
        for idx, fig in enumerate(figures):
            pfig = self._to_plotly(fig)
            if pfig is None:
                continue
            self._figures.append(pfig)
            plot = PlotlyComponent(id=f"{self.name}_plot_{idx}")
            plot.ui_style = f"width: 100%; height: {plot_height};"
            plot.on_mounted(lambda _=None, plot=plot, fig=pfig: plot.draw(fig))
            self._plots.append(plot)

        if not self._plots:
            self.container.ui_children = [
                Div("No supported plot data.", ui_class="text-grey-6")
            ]
        else:
            self.container.ui_children = self._plots

    def redraw(self):
        if not self._figures or not self._plots:
            self.draw()
            return
        for plot, fig in zip(self._plots, self._figures):
            plot.draw(fig)

    def set_component(self, comp):
        self.ui_children = [comp]


# Register with the component registry
from .registry import register_component

register_component("plot",
    icon="mdi-chart-line",
    component_class=PlotComponent,
    sections=[],
)