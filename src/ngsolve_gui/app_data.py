from ngsolve_webgpu import *
from webgpu.camera import Camera


class Settings:
    def __init__(self, data):
        self._data = data

    def get(self, key, default=None):
        return self._data.get(key, default)

    def set(self, key, value):
        self._data[key] = value


class AppData:
    _data: dict
    _gpu_cache: dict
    _clipping: Clipping
    _camera: Camera

    def __init__(self):
        self._data = {"tabs": {}, "active_tab": None}
        self._update = None
        self._gpu_cache = {}
        self._clipping = Clipping()
        self._camera = Camera()

    @property
    def clipping(self):
        return self._clipping

    @property
    def camera(self):
        return self._camera

    def get_mesh_gpu_data(self, mesh):
        key = repr(mesh)
        if key not in self._gpu_cache:
            self._gpu_cache[key] = MeshData(mesh)
        return self._gpu_cache[key]

    def get_function_gpu_data(self, cf, mesh, **kwargs):
        key = hash((repr(cf), repr(mesh), tuple(sorted(kwargs.items()))))
        if key not in self._gpu_cache:
            mdata = self.get_mesh_gpu_data(mesh)
            self._gpu_cache[key] = FunctionData(mdata, cf, **kwargs)
        return self._gpu_cache[key]

    def set_needs_redraw(self):
        for tab in self._data["tabs"].values():
            if "component" in tab:
                tab["component"]._redraw_needed = True

    def get_settings(self, name: str):
        return Settings(self._data["tabs"][name]["settings"])

    def get_save_data(self):
        data_copy = {"tabs": {}, "active_tab": self._data["active_tab"]}
        for name, tab in self._data["tabs"].items():
            tab_copy = tab.copy()
            if "component" in tab_copy:
                # Resolve type key from registry if not already set
                if "type" not in tab_copy or tab_copy["type"] == "unknown":
                    from .registry import get_registry

                    cls = type(tab_copy["component"])
                    for key, info in get_registry().items():
                        if info["cls"] is cls:
                            tab_copy["type"] = key
                            break
                tab_copy["data"] = tab_copy["component"].data
                del tab_copy["component"]
            data_copy["tabs"][name] = tab_copy
        return data_copy

    def add_tab(self, title: str, cls: type, *args, **kwargs):
        name = title.lower().replace(" ", "_")
        # Resolve type key and icon from registry
        from .registry import get_registry

        type_key = "unknown"
        icon = "mdi-vector-triangle"
        for key, info in get_registry().items():
            if info["cls"] is cls:
                type_key = key
                icon = info["icon"]
                break
        self._data["tabs"][name] = {
            "type": type_key,
            "icon": icon,
            "data": {},
            "name": name,
            "title": title,
            "settings": {},
        }
        component = cls(name, *args, **kwargs)
        self._data["tabs"][name]["component"] = component
        self.active_tab = name
        if self._update is not None:
            self._update()
        return component

    def get_tabs(self):
        """
        Get the tabs stored in the AppData instance.

        :return: A dictionary of tabs.
        """
        return self._data["tabs"]

    def get_tab(self, name):
        return self._data["tabs"].get(name, None)

    def delete_tab(self, name):
        """
        Delete a tab by name.

        :param name: The name of the tab to delete.
        """
        if name in self._data["tabs"]:
            del self._data["tabs"][name]
            if self.active_tab == name:
                self.active_tab = (
                    list(self._data["tabs"].keys())[0] if self._data["tabs"] else None
                )
            if self._update is not None:
                self._update()

    @property
    def active_tab(self):
        """
        Get the currently active tab name.
        """
        return self._data["active_tab"]

    @active_tab.setter
    def active_tab(self, name):
        """
        Set the currently active tab by name.

        :param name: The name of the tab to set as active.
        """
        self._data["active_tab"] = name
