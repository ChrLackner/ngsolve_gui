"""Entity numbers section — show numeric labels on mesh entities."""

from ngapp.components import *

from ..prop_widgets import Section, Chip, chip_row, Toggle


class EntityNumbersSection(Section):
    section_key = "numbers"

    def __init__(self, comp):
        chips = []
        for entity in comp.entity_number_entities:
            label = entity.replace("_", " ").title()
            label = label.replace("Surface Elements", "Surf. El.") \
                         .replace("Volume Elements", "Vol. El.") \
                         .replace("Surface Indices", "Surf. Idx") \
                         .replace("Segment Indices", "Seg. Idx") \
                         .replace("Volume Indices", "Vol. Idx")
            chips.append(Chip(
                label, observable=getattr(comp, f"{entity}_numbers_visible"), small=True,
            ))

        super().__init__(
            chip_row(*chips),
            Toggle("1-based indexing", comp.numbers_one_based),
            icon="mdi-numeric",
            title="Numbers",
            info="Overlay entity index labels directly in the scene.",
        )

