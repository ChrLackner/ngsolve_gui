_registry = {}


def register_component(type_key, *, icon, component_class):
    """Register a component type.

    Args:
        type_key: e.g. "mesh", "geometry", "function", "plot"
        icon: MDI icon name, e.g. "mdi-vector-triangle"
        component_class: the component class (WebgpuTab subclass or similar)

    The property panel for a type lives on the component itself (see
    ``PropertyPanelMixin.property_sections`` / ``build_property_panel``), so it
    is not part of the registry.
    """
    _registry[type_key] = {
        "icon": icon,
        "cls": component_class,
    }


def get_registry():
    return _registry


def get_component_info(type_key):
    return _registry.get(type_key, None)
