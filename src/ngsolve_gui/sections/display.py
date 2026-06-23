"""Display sections — visibility toggles for each scene type.

Always the FIRST section, always expanded. Toggles are rendered as option chips
(designer look) bound directly to the component's visibility Observables.
"""

from ngapp.components import *

from ..prop_widgets import Section, Chip, chip_row, Toggle, field
from ..cerbsim_style import prop_flab, input_tiny, gap_sm


class GeometryDisplaySection(Section):
    """Display section for geometry scenes."""

    section_key = "display"

    def __init__(self, comp):
        self.comp = comp
        chips = chip_row(
            Chip("Faces", "mdi-vector-square", comp.show_faces),
            Chip("Edges", "mdi-vector-line", comp.show_edges),
            Chip("Vertices", "mdi-vector-point", comp.show_vertices),
            Chip("Hover", "mdi-cursor-default-click", comp.picking_enabled),
        )
        super().__init__(chips, icon="mdi-eye", title="Display", opened=True)


class MeshDisplaySection(Section):
    """Display section for mesh scenes."""

    section_key = "display"

    def __init__(self, comp):
        self.comp = comp

        chips = [
            Chip("Wireframe", "mdi-grid", comp.wireframe_visible),
            Chip("Elements 2D", "mdi-triangle-outline", comp.elements2d_visible),
        ]
        if comp.mesh.dim == 3:
            chips.append(Chip("Elements 3D", "mdi-cube-outline", comp.elements3d_visible))
        chips.append(Chip("Elements 1D", "mdi-vector-line", comp.elements1d_visible))
        chips.append(Chip("Identifications", "mdi-link-variant", comp.identifications_visible))
        chips.append(Chip("Hover", "mdi-cursor-default-click", comp.picking_enabled))

        shrink = QSlider(
            ui_model_value=comp.shrink_value,
            ui_min=0.0, ui_max=1.0, ui_step=0.01, ui_label=True, ui_dense=True,
        )

        # Curved display: a master toggle plus the (disabled-until-on) order input.
        curve_order = QInput(
            ui_type="number", ui_model_value=comp.mesh_curvature_order,
            ui_dense=True, ui_class=input_tiny,
        )
        curve_order.ui_disable = not comp.mesh_curvature_enabled.value
        comp.mesh_curvature_enabled.on_change(
            lambda val, _old: setattr(curve_order, "ui_disable", not val)
        )

        super().__init__(
            chip_row(*chips),
            field("Shrink", shrink),
            Toggle("Curved display", comp.mesh_curvature_enabled),
            field("Curve order", curve_order),
            icon="mdi-eye", title="Display", opened=True,
        )


class FunctionDisplaySection(Section):
    """Display section for function/solution scenes."""

    section_key = "display"

    def __init__(self, comp):
        self.comp = comp

        primary = [Chip("Wireframe", "mdi-grid", comp.wireframe_visible)]
        if comp.draw_surf:
            primary.append(Chip("Surface", "mdi-square-outline", comp.elements2d_visible))
        if comp.mesh.dim == 3 and comp.clippingcf is not None:
            primary.append(Chip("Clipping Fn", "mdi-box-cutter", comp.clipping_visible))
        primary.append(Chip("Highlight", "mdi-cursor-default-click", comp.picking_enabled))

        items = [chip_row(*primary)]

        # Advanced (less-used) toggles behind an inline "More options" disclosure.
        advanced = []
        if comp.facet_renderer is not None:
            advanced.append(Chip("ElementBND", "mdi-vector-polyline", comp.facet_visible))
        if comp.contact is not None:
            advanced.append(Chip("Contact Pairs", "mdi-vector-intersection", comp.contact_enabled))

        if advanced:
            from ..prop_widgets import MoreDisclosure
            more_items = [chip_row(*advanced)]
            if comp.facet_renderer is not None:
                thickness = QSlider(
                    ui_model_value=comp.facet_thickness,
                    ui_min=0.001, ui_max=0.05, ui_step=0.001, ui_dense=True, ui_label=True,
                )
                more_items.append(field("ElementBND thickness", thickness))
            items.append(MoreDisclosure(*more_items))

        super().__init__(*items, icon="mdi-eye", title="Display", opened=True)
