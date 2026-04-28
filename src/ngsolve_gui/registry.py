_registry = {}


def register_component(type_key, *, icon, component_class, sections):
    """Register a component type with its property panel sections.

    Args:
        type_key: e.g. "mesh", "geometry", "function", "plot"
        icon: MDI icon name, e.g. "mdi-vector-triangle"
        component_class: the component class (WebgpuTab subclass or similar)
        sections: list of QExpansionItem subclasses to show in the property panel
    """
    _registry[type_key] = {
        "icon": icon,
        "cls": component_class,
        "sections": sections,
    }


def get_registry():
    return _registry


def get_component_info(type_key):
    return _registry.get(type_key, None)


def get_sections_for(type_key):
    return _registry.get(type_key, {}).get("sections", [])
