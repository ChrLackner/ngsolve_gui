from ngapp.components import *

from .cerbsim_style import (
    sidebar_props,
    prop_title,
    prop_title_text,
    section_content,
    section_border,
    section_header,
    field_label,
    gap_xs,
    SECTION_COLORS,
)


# Section key → accent color mapping (for left-border on headers)
_SECTION_KEY_MAP = {
    "GeometryDisplaySection": "display",
    "MeshDisplaySection": "display",
    "FunctionDisplaySection": "display",
    "ColorbarSection": "colormap",
    "MeshColorSection": "colors",
    "ClippingSection": "clipping",
    "DeformationSection": "deformation",
    "VectorsFlowSection": "vectors",
    "ComplexSection": "complex",
    "GeometrySelectionSection": "selection",
    "MeshGenerationSection": "meshing",
    "EntityNumbersSection": "numbers",
}


def _section_header_border(section_cls):
    """Per-section accent color for the header left-border (data-driven)."""
    key = _SECTION_KEY_MAP.get(section_cls.__name__, "")
    color = SECTION_COLORS.get(key, "var(--fg-subtle)")
    return f"border-left: 3px solid {color};"


class PropertyPanel(Div):
    def __init__(self):
        self._title_text = Div("Properties", ui_class=prop_title_text)
        self._actions = Div(ui_class="row items-center " + gap_xs)
        self._title = Div(
            self._title_text,
            self._actions,
            ui_class=prop_title,
        )
        self._sections = Div()
        super().__init__(
            self._title,
            QSeparator(),
            self._sections,
            ui_class=sidebar_props,
        )

    def set_component(self, comp, type_key):
        """Rebuild the panel for the given component and type."""
        from .registry import get_sections_for

        if comp is None:
            self._title_text.ui_children = ["Properties"]
            self._actions.ui_children = []
            self._sections.ui_children = [
                Div("No item selected.", ui_class=field_label + " q-pa-md")
            ]
            return

        # Show the component title
        title = getattr(comp, "title", type_key)
        self._title_text.ui_children = [title]

        # Action buttons in header (Draw Mesh / Draw Geometry)
        self._actions.ui_children = self._build_actions(comp, type_key)

        section_classes = get_sections_for(type_key)
        sections = []
        for cls in section_classes:
            try:
                section = cls(comp)
                # Apply consistent styling to every section
                section.ui_dense = True
                section.ui_expand_separator = True
                section.ui_class = section_border
                section.ui_header_class = str(section_header)
                section.ui_header_style = _section_header_border(cls)
                # Wrap section content children in padded container
                _apply_section_padding(section)
                sections.append(section)
            except ValueError:
                pass
            except Exception as e:
                print(f"Error building section {cls.__name__}: {e}")

        if sections:
            self._sections.ui_children = sections
        else:
            self._sections.ui_children = [
                Div("No settings available.", ui_class=field_label + " q-pa-md")
            ]

    def _build_actions(self, comp, type_key):
        """Build header action buttons based on component type."""
        buttons = []
        if type_key == "function":
            btn = QBtn(
                QTooltip("Open as Mesh"),
                ui_icon="mdi-vector-triangle",
                ui_flat=True,
                ui_dense=True,
                ui_round=True,
                ui_size="sm",
                ui_color="grey-7",
            )
            btn.on_click(lambda *a: self._draw_mesh(comp))
            buttons.append(btn)
        elif type_key == "mesh":
            btn = QBtn(
                QTooltip("Open Geometry"),
                ui_icon="mdi-cube-outline",
                ui_flat=True,
                ui_dense=True,
                ui_round=True,
                ui_size="sm",
                ui_color="grey-7",
            )
            btn.on_click(lambda *a: self._draw_geometry(comp))
            buttons.append(btn)
        return buttons

    def _draw_mesh(self, comp):
        from .mesh import MeshComponent
        comp.app_data.add_tab(
            "Mesh_" + comp.name, MeshComponent, {"obj": comp.mesh}, comp.app_data
        )

    def _draw_geometry(self, comp):
        try:
            geo = comp.mesh.ngmesh.GetGeometry()
            from .geometry import GeometryComponent
            comp.app_data.add_tab(
                "Geo_" + comp.title, GeometryComponent, {"obj": geo}, comp.app_data
            )
        except Exception as e:
            print(f"Could not extract geometry from mesh: {e}")


def _apply_section_padding(section):
    """Wrap the section's positional children in a padded Div.

    QExpansionItem children are the expansion body. We wrap them so every
    section automatically gets consistent inner padding without the section
    author having to think about it.
    """
    children = list(section.ui_children) if section.ui_children else []
    if children:
        section.ui_children = [Div(*children, ui_class=section_content)]
