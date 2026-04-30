from ngapp.components import *


class MeshViewSection(QExpansionItem):
    def __init__(self, comp):
        self.comp = comp
        wireframe = QCheckbox("Wireframe", ui_model_value=comp.wireframe_visible)

        options = [wireframe]

        element2d = QCheckbox("Elements 2D", ui_model_value=comp.elements2d_visible)
        options.append(element2d)

        if comp.mesh.dim == 3:
            elements3d = QCheckbox(
                "Elements 3D", ui_model_value=comp.elements3d_visible
            )
            options.append(elements3d)

        elements1d = QCheckbox("Elements 1D", ui_model_value=comp.elements1d_visible)
        options.append(elements1d)

        shrink = QSlider(
            ui_model_value=comp.shrink_value,
            ui_min=0.0,
            ui_max=1.0,
            ui_step=0.01,
            ui_label=True,
            ui_label_always=True,
        )

        curve_enabled = QCheckbox(
            "",
            ui_model_value=comp.mesh_curvature_enabled,
            ui_style="transform: scale(0.85);",
        )
        curve_order = QInput(
            ui_type="number",
            ui_model_value=comp.mesh_curvature_order,
            ui_dense=True,
        )
        curve_order.ui_disable = not comp.mesh_curvature_enabled.value
        comp.mesh_curvature_enabled.on_change(
            lambda val, _old: setattr(curve_order, "ui_disable", not val)
        )

        curving_row = Row(
            curve_enabled,
            Div("Curve Order"),
            Div(curve_order, ui_class="col-auto"),
            ui_class="items-center",
            ui_style="flex-wrap: nowrap; font-size: 0.95em;",
        )

        draw_geo_btn = QBtn(
            ui_icon="mdi-cube-outline",
            ui_label="Draw Geometry",
            ui_flat=True,
            ui_color="primary",
        )
        draw_geo_btn.on_click(self._draw_geometry)

        super().__init__(
            *options,
            Div("Shrink", ui_style="font-size: 0.85rem; padding-top: 8px;"),
            Div(shrink, ui_style="width: 100%; padding: 0 4px;"),
            curving_row,
            draw_geo_btn,
            ui_icon="mdi-eye",
            ui_label="View Options",
        )

    def _draw_geometry(self, *args):
        comp = self.comp
        try:
            geo = comp.mesh.ngmesh.GetGeometry()
            from ngsolve_gui.geometry import GeometryComponent

            comp.app_data.add_tab(
                "Geo_" + comp.title, GeometryComponent, {"obj": geo}, comp.app_data
            )
        except Exception as e:
            print(f"Could not extract geometry from mesh: {e}")
