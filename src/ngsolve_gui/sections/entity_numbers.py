"""Entity numbers section — show numeric labels on mesh entities.

Uses CSS Grid with auto-fill for responsive column count.
"""

from ngapp.components import *

from ..cerbsim_style import toggle_grid


class EntityNumbersSection(QExpansionItem):
    def __init__(self, comp):
        checkboxes = []
        for entity in comp.entity_number_entities:
            label = entity.replace("_", " ").title()
            label = label.replace("Surface Elements", "Surf. El.") \
                         .replace("Volume Elements", "Vol. El.") \
                         .replace("Surface Indices", "Surf. Idx") \
                         .replace("Segment Indices", "Seg. Idx") \
                         .replace("Volume Indices", "Vol. Idx")
            cb = QCheckbox(label, ui_model_value=getattr(comp, f"{entity}_numbers_visible"), ui_dense=True)
            checkboxes.append(cb)

        grid = Div(*checkboxes, ui_class=toggle_grid)

        one_based = QCheckbox("1-based indexing", ui_model_value=comp.numbers_one_based, ui_dense=True)

        super().__init__(
            grid,
            one_based,
            ui_icon="mdi-numeric",
            ui_label="Numbers",
            ui_dense=True,
        )
