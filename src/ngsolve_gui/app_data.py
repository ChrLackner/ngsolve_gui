import netgen.occ as ngocc
import ngsolve as ngs


class Settings:
    def __init__(self, data):
        self._data = data

    def get(self, key, default=None):
        return self._data.get(key, default)

    def set(self, key, value):
        self._data[key] = value


class AppData:
    data: dict

    def __init__(self):
        self._data = {"tabs": {}, "active_tab": None}
        self._update = None

    def get_settings(self, name: str):
        return Settings(self._data["tabs"][name]["settings"])

    def add_mesh(self, title: str, mesh: ngs.Mesh):
        _type = "mesh"
        name = _type + "_" + title.lower().replace(" ", "_")
        self._data["tabs"][name] = {
            "type": _type,
            "icon": "mdi-vector-triangle",
            "data": mesh,
            "name": name,
            "title": title,
            "settings": {},
        }
        self.active_tab = name
        if self._update is not None:
            self._update()

    def add_geometry(self, title: str, geometry: ngocc.OCCGeometry):
        _type = "geometry"
        name = _type + "_" + title.lower().replace(" ", "_")
        self._data["tabs"][name] = {
            "type": _type,
            "icon": "mdi-cube",
            "data": geometry,
            "name": name,
            "title": title,
            "settings": {},
        }
        self.active_tab = name
        if self._update is not None:
            self._update()

    def add_function(
        self, title: str, function: ngs.CoefficientFunction, mesh: ngs.Mesh
    ):
        _type = "function"
        print("add function")
        name = _type + "_" + title.lower().replace(" ", "_")
        self._data["tabs"][name] = {
            "type": _type,
            "icon": "mdi-function-variant",
            "data": {"function": function, "mesh": mesh},
            "name": name,
            "title": title,
            "settings": {},
        }
        self.active_tab = name
        if self._update is not None:
            self._update()

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
