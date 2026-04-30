from ngapp.components import *


class MeshViewSection(QExpansionItem):
    def __init__(self, comp):
        self.comp = comp
        wireframe = QCheckbox("Wireframe", ui_model_value=comp.wireframe_visible.value)
        bind(comp.wireframe_visible, wireframe)

        options = [wireframe]

        element2d = QCheckbox("Elements 2D", ui_model_value=comp.elements2d_visible.value)
        bind(comp.elements2d_visible, element2d)
        options.append(element2d)

        if comp.mesh.dim == 3:
            elements3d = QCheckbox(
                "Elements 3D", ui_model_value=comp.elements3d_visible.value
            )
            bind(comp.elements3d_visible, elements3d)
            options.append(elements3d)

        elements1d = QCheckbox("Elements 1D", ui_model_value=comp.elements1d_visible.value)
        bind(comp.elements1d_visible, elements1d)
        options.append(elements1d)

        shrink = QSlider(
            ui_model_value=comp.shrink_value.value,
            ui_min=0.0,
            ui_max=1.0,
            ui_step=0.01,
            ui_label=True,
            ui_label_always=True,
        )
        bind(comp.shrink_value, shrink)

        curve_enabled = QCheckbox(
            "",
            ui_model_value=comp.mesh_curvature_enabled.value,
            ui_style="transform: scale(0.85);",
        )
        self.curve_order = curve_order = QInput(
            ui_type="number",
            ui_model_value=comp.mesh_curvature_order.value,
            ui_dense=True,
        )
        curve_order.ui_disable = not comp.mesh_curvature_enabled.value
        bind(comp.mesh_curvature_enabled, curve_enabled)
        comp.mesh_curvature_enabled.on_change(
            lambda val, _old: setattr(curve_order, "ui_disable", not val)
        )
        # Curvature order needs int conversion, so we bind manually
        comp.mesh_curvature_order.on_change(
            lambda val, _old: setattr(curve_order, "ui_model_value", val)
        )
        curve_order.on_update_model_value(self._update_curvature_order)

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

    def _update_curvature_order(self, event):
        try:
            self.comp.mesh_curvature_order.value = int(event.value)
        except (TypeError, ValueError):
            pass

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
