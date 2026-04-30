from ngapp.components import *

from .styles import sidebar_props, prop_title, section_content, section_border


class PropertyPanel(Div):
    def __init__(self):
        self._title = Div(
            "Properties",
            ui_class=str(prop_title),
        )
        self._sections = Div()
        super().__init__(
            self._title,
            QSeparator(),
            self._sections,
            ui_class=str(sidebar_props),
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
                section.ui_class = str(section_border)
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
        section.ui_children = [Div(*children, ui_class=str(section_content))]
