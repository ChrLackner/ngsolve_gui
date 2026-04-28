from ngapp.components import *

from .styles import sidebar_style

# Shared style applied to every section's content wrapper.
# Sections just provide their widgets — this padding makes them all look consistent.
SECTION_CONTENT_STYLE = "padding: 8px 12px;"


class PropertyPanel(Div):
    def __init__(self):
        self._title = Div(
            "Properties",
            ui_style="font-size: 0.75rem; letter-spacing: 0.05em; text-transform: uppercase;"
            " font-weight: 700; color: #78909c; padding: 12px 16px 8px;",
        )
        self._sections = Div()
        super().__init__(
            self._title,
            QSeparator(),
            self._sections,
            ui_style=sidebar_style(
                border_side="left", extra="width: 280px; min-width: 280px;"
            ),
        )

    def set_component(self, comp, type_key):
        """Rebuild the panel for the given component and type."""
        from .registry import get_sections_for

        if comp is None:
            self._title.ui_children = ["Properties"]
            self._sections.ui_children = [
                Div(
                    "No item selected.",
                    ui_class="text-grey-6",
                    ui_style="padding: 16px; font-size: 0.85rem;",
                )
            ]
            return

        # Show the component title
        title = getattr(comp, "title", type_key)
        self._title.ui_children = [title]

        section_classes = get_sections_for(type_key)
        sections = []
        for cls in section_classes:
            try:
                section = cls(comp)
                # Apply consistent content padding to every section
                section.ui_dense = True
                section.ui_expand_separator = True
                section.ui_style = "border-bottom: 1px solid #eee;"
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
                Div(
                    "No settings available.",
                    ui_class="text-grey-6",
                    ui_style="padding: 16px; font-size: 0.85rem;",
                )
            ]


def _apply_section_padding(section):
    """Wrap the section's positional children in a padded Div.

    QExpansionItem children are the expansion body. We wrap them so every
    section automatically gets consistent inner padding without the section
    author having to think about it.
    """
    children = list(section.ui_children) if section.ui_children else []
    if children:
        section.ui_children = [Div(*children, ui_style=SECTION_CONTENT_STYLE)]
