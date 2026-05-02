from ngapp.components import *


class EntityNumbersSection(QExpansionItem):
    def __init__(self, comp):
        items = []
        for entity in comp.entity_number_entities:
            label = entity.replace("_", " ").title()
            cb = QCheckbox(label, ui_model_value=getattr(comp, f"{entity}_numbers_visible"))
            items.append(cb)
        one_based = QCheckbox("1-based", ui_model_value=comp.numbers_one_based)
        items.append(one_based)
        super().__init__(*items, ui_icon="mdi-numeric", ui_label="Entity Numbers")
