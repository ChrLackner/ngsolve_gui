"""Display sections — visibility toggles for each scene type.

These are always the FIRST section in the property panel, always expanded.
Toggles use a compact 2-column grid layout to minimize vertical space.
"""

from ngapp.components import *


def _toggle_grid(*checkboxes):
    """Arrange checkboxes in a responsive grid (2-3 columns based on width)."""
    return Div(
        *checkboxes,
        ui_style="display: grid; grid-template-columns: repeat(auto-fill, minmax(110px, 1fr)); gap: 0;",
    )


class GeometryDisplaySection(QExpansionItem):
    """Display section for geometry scenes."""

    def __init__(self, comp):
        self.comp = comp
        show_edges = QCheckbox("Edges", ui_model_value=comp.show_edges, ui_dense=True)
        show_verts = QCheckbox("Vertices", ui_model_value=comp.show_vertices, ui_dense=True)
        picking = QCheckbox("Highlight on Hover", ui_model_value=comp.picking_enabled, ui_dense=True)

        grid = _toggle_grid(show_edges, show_verts, picking)

        super().__init__(
            grid,
            ui_icon="mdi-eye",
            ui_label="Display",
            ui_default_opened=True,
            ui_dense=True,
        )


class MeshDisplaySection(QExpansionItem):
    """Display section for mesh scenes."""

    def __init__(self, comp):
        self.comp = comp

        wireframe = QCheckbox("Wireframe", ui_model_value=comp.wireframe_visible, ui_dense=True)
        el2d = QCheckbox("Elements 2D", ui_model_value=comp.elements2d_visible, ui_dense=True)
        el1d = QCheckbox("Elements 1D", ui_model_value=comp.elements1d_visible, ui_dense=True)
        picking = QCheckbox("Highlight on Hover", ui_model_value=comp.picking_enabled, ui_dense=True)

        toggles = [wireframe, el2d]
        if comp.mesh.dim == 3:
            el3d = QCheckbox("Elements 3D", ui_model_value=comp.elements3d_visible, ui_dense=True)
            toggles.append(el3d)
        toggles.extend([el1d, picking])
        grid = _toggle_grid(*toggles)

        # Shrink
        shrink_row = Row(
            Div("Shrink", ui_style="font-size: 0.8rem; color: #546e7a; min-width: 42px;"),
            QSlider(
                ui_model_value=comp.shrink_value,
                ui_min=0.0, ui_max=1.0, ui_step=0.01,
                ui_label=True, ui_label_always=True,
                ui_dense=True,
            ),
            ui_class="items-center",
            ui_style="gap: 8px; padding-top: 4px;",
        )

        # Curve order
        curve_enabled = QCheckbox(
            "", ui_model_value=comp.mesh_curvature_enabled,
            ui_dense=True, ui_style="transform: scale(0.85);",
        )
        curve_order = QInput(
            ui_type="number", ui_model_value=comp.mesh_curvature_order,
            ui_dense=True, ui_style="max-width: 50px;",
        )
        curve_order.ui_disable = not comp.mesh_curvature_enabled.value
        comp.mesh_curvature_enabled.on_change(
            lambda val, _old: setattr(curve_order, "ui_disable", not val)
        )
        curve_row = Row(
            curve_enabled,
            Div("Curve Order", ui_style="font-size: 0.8rem; white-space: nowrap;"),
            curve_order,
            ui_class="items-center",
            ui_style="flex-wrap: nowrap; gap: 4px;",
        )

        super().__init__(
            grid,
            shrink_row,
            curve_row,
            ui_icon="mdi-eye",
            ui_label="Display",
            ui_default_opened=True,
            ui_dense=True,
        )


class FunctionDisplaySection(QExpansionItem):
    """Display section for function/solution scenes."""

    def __init__(self, comp):
        self.comp = comp

        # Primary toggles (always visible)
        wireframe = QCheckbox("Wireframe", ui_model_value=comp.wireframe_visible, ui_dense=True)
        primary = [wireframe]

        if comp.draw_surf:
            primary.append(QCheckbox("Surface", ui_model_value=comp.elements2d_visible, ui_dense=True))

        if comp.mesh.dim == 3 and comp.clippingcf is not None:
            primary.append(QCheckbox("Clipping Fn", ui_model_value=comp.clipping_visible, ui_dense=True))

        if comp.surface_vectors is not None:
            primary.append(QCheckbox("Surf. Vectors", ui_model_value=comp.surface_vectors_visible, ui_dense=True))

        if comp.clipping_vectors is not None:
            primary.append(QCheckbox("Clip. Vectors", ui_model_value=comp.clipping_vectors_visible, ui_dense=True))

        primary.append(QCheckbox("Highlight", ui_model_value=comp.picking_enabled, ui_dense=True))

        grid = _toggle_grid(*primary)
        items = [grid]

        # Advanced toggles (nested expander for less-used things)
        advanced_toggles = []
        if comp.facet_renderer is not None:
            advanced_toggles.append(QCheckbox("ElementBND", ui_model_value=comp.facet_visible, ui_dense=True))
        if comp.fieldlines is not None:
            advanced_toggles.append(QCheckbox("Field Lines", ui_model_value=comp.field_lines_visible, ui_dense=True))
        if comp.contact is not None:
            advanced_toggles.append(QCheckbox("Contact Pairs", ui_model_value=comp.contact_enabled, ui_dense=True))

        if advanced_toggles:
            adv_items = [_toggle_grid(*advanced_toggles)]
            # ElementBND thickness slider (only if facets exist)
            if comp.facet_renderer is not None:
                adv_items.append(
                    Row(
                        Div("ElementBND thickness", ui_style="font-size: 0.75rem; color: #546e7a; white-space: nowrap;"),
                        QSlider(
                            ui_model_value=comp.facet_thickness,
                            ui_min=0.001, ui_max=0.05, ui_step=0.001,
                            ui_dense=True, ui_label=True,
                        ),
                        ui_class="items-center",
                        ui_style="gap: 6px;",
                    )
                )
            advanced = QExpansionItem(
                *adv_items,
                ui_label="More",
                ui_dense=True,
                ui_dense_toggle=True,
                ui_header_style="font-size: 0.75rem; color: #78909c; min-height: 28px; padding: 0;",
            )
            items.append(advanced)

        super().__init__(
            *items,
            ui_icon="mdi-eye",
            ui_label="Display",
            ui_default_opened=True,
            ui_dense=True,
        )
