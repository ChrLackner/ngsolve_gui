from ngapp.components import *

from ..prop_widgets import Section, PickPill, field
from ..cerbsim_style import chk_inline, field_label, gap_sm


class GeometrySelectionSection(Section):
    section_key = "selection"

    def __init__(self, comp):
        self.comp = comp

        pick_row = Div(
            PickPill("S", comp.pick_solid, "Solids"),
            PickPill("F", comp.pick_faces, "Faces"),
            PickPill("E", comp.pick_edges, "Edges"),
            PickPill("V", comp.pick_vertices, "Vertices"),
            ui_class=chk_inline,
        )

        self._heading = Div("No selection", ui_class=field_label)

        self.meshsize_input = QInput(
            ui_type="number", ui_debounce=500, ui_dense=True, ui_disable=True,
        )
        self.meshsize_input.on_update_model_value(comp.change_maxh)
        self.name_input = QInput(
            ui_type="text", ui_debounce=500, ui_dense=True, ui_disable=True,
        )
        self.name_input.on_update_model_value(comp.change_name)

        hide_btn = QBtn("Hide", ui_icon="mdi-eye-off-outline", ui_outline=True,
                        ui_dense=True, ui_no_caps=True, ui_size="sm")
        hide_btn.on_click(comp._hide_selected_shape)
        showall_btn = QBtn("Show all", ui_icon="mdi-eye-outline", ui_flat=True,
                           ui_dense=True, ui_no_caps=True, ui_size="sm")
        showall_btn.on_click(lambda: comp._show_all_shapes())

        super().__init__(
            field("Pick targets", pick_row),
            self._heading,
            field("Local mesh size", self.meshsize_input),
            field("Name", self.name_input),
            Row(hide_btn, showall_btn, ui_class=gap_sm),
            icon="mdi-cursor-default-click",
            title="Selection",
            info="Pick entities in the scene to set local mesh size or rename them.",
        )

        comp._selection_section = self

    def _entity_name_maxh(self, kind, index):
        entity = self.comp._get_entity(kind, index)
        if entity is None:
            return ("", None)
        raw_maxh = entity.maxh
        return (entity.name or "", None if raw_maxh >= 1e99 else raw_maxh)

    def update_selection(self, kind, index):
        label = {"face": "Face", "edge": "Edge", "vertex": "Vertex", "solid": "Solid"}.get(kind, kind)
        self._heading.ui_children = [f"Selected: {label} {index}"]
        name, maxh = self._entity_name_maxh(kind, index)
        self.meshsize_input.ui_model_value = maxh
        self.meshsize_input.ui_hint = ""
        self.name_input.ui_model_value = name
        self.name_input.ui_hint = ""
        self.meshsize_input.ui_disable = False
        self.name_input.ui_disable = False
        self._set_open(True)

    def update_multi_selection(self, items):
        self._heading.ui_children = [f"Selected: {len(items)} entities"]
        names = set()
        maxhs = set()
        for kind, idx in items:
            name, maxh = self._entity_name_maxh(kind, idx)
            names.add(name)
            maxhs.add(maxh)
        if len(names) == 1:
            self.name_input.ui_model_value = names.pop()
            self.name_input.ui_hint = ""
        else:
            self.name_input.ui_model_value = ""
            self.name_input.ui_hint = "Multiple values"
        if len(maxhs) == 1:
            self.meshsize_input.ui_model_value = maxhs.pop()
            self.meshsize_input.ui_hint = ""
        else:
            self.meshsize_input.ui_model_value = None
            self.meshsize_input.ui_hint = "Multiple values"
        self.meshsize_input.ui_disable = False
        self.name_input.ui_disable = False
        self._set_open(True)

    def clear_selection(self):
        self._heading.ui_children = ["No selection"]
        self.meshsize_input.ui_model_value = None
        self.meshsize_input.ui_hint = ""
        self.name_input.ui_model_value = ""
        self.name_input.ui_hint = ""
        self.meshsize_input.ui_disable = True
        self.name_input.ui_disable = True
