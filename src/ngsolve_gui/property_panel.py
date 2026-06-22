"""Reusable, component-owned property panel.

A component carries its own property panel: set ``property_sections`` (a list of
``QExpansionItem`` subclasses) on the component class and optionally override
``property_actions()`` for header buttons, then call ``build_property_panel()``.
This lets another package reuse a component (e.g. ``GeometryComponent``) and get
its property panel for free, without going through the app or the registry.
"""

from ngapp.components import *

from . import cerbsim_style as cb
from .cerbsim_style import (
    sidebar_props,
    prop_title,
    prop_title_text,
    field_label,
    gap_xs,
)


# Section class name → stable key (used for the header accent color *and* for
# include/exclude filtering by other apps). A section class may also set its own
# ``section_key`` attribute (preferred for sections defined outside this package).
_SECTION_KEY_MAP = {
    "GeometryDisplaySection": "display",
    "MeshDisplaySection": "display",
    "FunctionDisplaySection": "display",
    "ColorbarSection": "colormap",
    "MeshColorSection": "colors",
    "ClippingSection": "clipping",
    "DeformationSection": "deformation",
    "VectorsFlowSection": "vectors",
    "LicSection": "lic",
    "ComplexSection": "complex",
    "GeometrySelectionSection": "selection",
    "MeshGenerationSection": "meshing",
    "EntityNumbersSection": "numbers",
}


def section_key(section_cls):
    """Stable string key for a section class.

    Other apps use these keys to hide sections, e.g.
    ``comp.build_property_panel(exclude=["selection"])``. A section can override
    its key with a ``section_key`` class attribute; otherwise it falls back to
    the built-in map, then to a lowercased class name.
    """
    return (
        getattr(section_cls, "section_key", None)
        or _SECTION_KEY_MAP.get(section_cls.__name__)
        or section_cls.__name__.lower()
    )


def _excluded_keys(comp, exclude):
    """Collect the set of section keys to hide for this panel build.

    Sources: the component's ``hidden_sections`` and the ``exclude`` argument.
    Each entry may be a key string or a section class.
    """
    items = list(getattr(comp, "hidden_sections", ()) or ())
    if exclude:
        items += list(exclude)
    return {it if isinstance(it, str) else section_key(it) for it in items}


class PropertyPanel(Div):
    """Self-contained property panel for a single component.

    Renders the component's title, its header actions, and the sections it
    declares in ``property_sections``. Build one via
    ``component.build_property_panel()``.
    """

    def __init__(self, comp, exclude=None):
        self._comp = comp
        header = Div(
            Div("Properties", ui_class=prop_title_text),
            Div(*self._actions(comp), ui_class="row items-center " + gap_xs),
            ui_class=prop_title,
        )

        children = [header, QSeparator()]
        try:
            summary = comp.property_summary()
        except Exception as e:
            print(f"Error building property summary: {e}")
            summary = None
        if summary is not None:
            children.append(summary)
        children.append(Div(*self._build_sections(comp, exclude)))
        super().__init__(*children, ui_class=sidebar_props)

    def _actions(self, comp):
        """Header action buttons — the cross-reference (Open as mesh/geometry)
        followed by any extra actions the component declares (e.g. downloads)."""
        specs = []
        try:
            xref = comp.property_xref()
        except Exception:
            xref = None
        if xref:
            specs.append(xref)
        try:
            specs += list(comp.property_actions() or [])
        except Exception:
            pass
        return [self._action_button(spec) for spec in specs]

    @staticmethod
    def _action_button(spec):
        children = [QTooltip(spec.get("label", "Action"))]
        menu = spec.get("menu")
        if menu:
            children.append(PropertyPanel._action_menu(menu))
        btn = QBtn(
            *children,
            ui_icon=spec.get("icon", "mdi-open-in-new"),
            ui_flat=True, ui_dense=True, ui_round=True, ui_size="sm",
            ui_class=str(cb.topbar_icon),
        )
        callback = spec.get("callback")
        if callback is not None and not menu:
            btn.on_click(lambda e=None: callback())
        return btn

    @staticmethod
    def _action_menu(items):
        rows = []
        for item in items:
            sections = []
            if item.get("icon"):
                sections.append(QItemSection(
                    QIcon(ui_name=item["icon"], ui_size="xs"), ui_avatar=True))
            sections.append(QItemSection(item.get("label", "")))
            row = QItem(*sections, ui_clickable=True, ui_dense=True)
            cb_ = item.get("callback")
            if cb_ is not None:
                row.on_click(lambda e=None, c=cb_: c())
            rows.append(row)
        return QMenu(QList(*rows, ui_dense=True))

    def _build_sections(self, comp, exclude=None):
        section_classes = getattr(comp, "property_sections", []) or []
        excluded = _excluded_keys(comp, exclude)
        sections = []
        for cls in section_classes:
            if section_key(cls) in excluded:
                continue
            try:
                sections.append(cls(comp))
            except ValueError:
                pass  # section opted out (e.g. not applicable for this object)
            except Exception as e:
                print(f"Error building section {cls.__name__}: {e}")
        if not sections:
            return [Div("No settings available.", ui_class=field_label + " q-pa-md")]
        return sections


def empty_property_panel():
    """Placeholder panel shown when no component is selected."""
    return Div(
        Div(Div("Properties", ui_class=prop_title_text), ui_class=prop_title),
        QSeparator(),
        Div("No item selected.", ui_class=field_label + " q-pa-md"),
        ui_class=sidebar_props,
    )


class PropertyPanelMixin:
    """Mix into a component to give it its own property panel.

    Set ``property_sections`` (a list of ``QExpansionItem`` subclasses) on the
    component class, and optionally override ``property_actions()`` to add header
    buttons. ``build_property_panel()`` returns a ready-to-mount panel.

    Other apps can hide sections by key, without importing section classes::

        # one-off:
        panel = geo.build_property_panel(exclude=["selection"])

        # or persistently for an instance / subclass:
        geo.hidden_sections = {"selection"}
        panel = geo.build_property_panel()

    Use :meth:`available_section_keys` to discover the keys a component offers.
    """

    #: Sections shown in this component's property panel (override per class).
    property_sections: list = []

    #: Section keys hidden for this component (strings or section classes).
    #: Set per-instance or override per-subclass; merged with build-time excludes.
    hidden_sections = ()

    def property_subtitle(self):
        """Type subtitle shown under the object name (e.g. 'Mesh · 3D')."""
        return ""

    def property_xref(self):
        """Cross-reference link row, or None.

        Return a dict ``{"label", "icon", "callback"}`` (e.g. open the mesh's
        geometry, or a function's mesh).
        """
        return None

    def property_actions(self):
        """Extra header action buttons, rendered after the cross-reference.

        Return a list of dicts ``{"label", "icon", "callback"}`` (e.g. download
        the mesh or geometry to a file).
        """
        return []

    def property_summary(self):
        """An always-visible summary block above the sections, or None
        (e.g. a function's colorbar / field summary)."""
        return None

    def build_property_panel(self, exclude=None):
        """Build a self-contained property panel for this component.

        ``exclude`` is an optional iterable of section keys (or section classes)
        to hide, merged with the component's ``hidden_sections``.
        """
        return PropertyPanel(self, exclude=exclude)

    @classmethod
    def available_section_keys(cls):
        """List the section keys this component offers (for use with ``exclude``)."""
        return [section_key(s) for s in cls.property_sections]
