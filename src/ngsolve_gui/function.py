from ngapp.components import *
from ngsolve_webgpu import *
from .clipping import ClippingSettings
from .webgpu_tab import WebgpuTab
import ngsolve as ngs
from webgpu.canvas import debounce
import copy


class ColorbarSettings(QCard):
    def __init__(self, comp):
        self.comp = comp
        autoscale, discrete, minval, maxval = comp.settings.get(
            "colormap", (True, False, 0.0, 1.0)
        )
        ncolors = comp.settings.get("ncolors_colormap", 8)
        color_map_name = comp.settings.get("colormap_name", "matlab:jet")
        self.colormap = QSelect(
            ui_label="Colormap",
            ui_options=[
                "viridis",
                "plasma",
                "cet_l20",
                "matlab:jet",
                "matplotlib:coolwarm",
            ],
            ui_model_value=color_map_name,
        )
        self.discrete = QCheckbox(
            ui_label="Discrete",
            ui_model_value=discrete,
        )
        self.ncolors = QInput(
            ui_label="Number of Colors",
            ui_type="number",
            ui_model_value=ncolors,
            ui_style="width: 100px;",
        )
        self.ncolors.on_change(self.update_ncolors)
        self.discrete.on_update_model_value(self.update_discrete)
        self.colormap.on_update_model_value(self.update_colormap)
        self.minval = QInput(
            ui_label="Min Value",
            ui_type="number",
            ui_dense=True,
            ui_model_value=minval,
            ui_style="width: 100px;",
        )
        self.maxval = QInput(
            ui_label="Max Value",
            ui_type="number",
            ui_dense=True,
            ui_model_value=maxval,
            ui_style="padding-left: 20px; width: 100px;",
        )
        self.minval.on_change(self.update_min)
        self.maxval.on_change(self.update_max)
        self.autoscale = QCheckbox(ui_label="Autoscale", ui_model_value=autoscale)
        self.autoscale.on_update_model_value(self.update_autoscale)
        super().__init__(
            QCardSection(
                Heading("Colorbar", 5),
                self.autoscale,
                self.discrete,
                Row(self.minval, self.maxval),
                Row(self.colormap, self.ncolors),
            )
        )
        self.on_mounted(self._update)

    def update_colormap(self, event):
        self.comp.colormap.set_colormap(self.colormap.ui_model_value)
        self.comp.redraw()
        self.comp.wgpu.scene.render()

    def update_ncolors(self, event):
        try:
            ncolors = int(self.ncolors.ui_model_value)
            if ncolors < 1:
                ncolors = 1
            if ncolors > 32:
                ncolors = 32
            self.comp.colormap.set_n_colors(ncolors)
            self.comp.wgpu.scene.render()
            self.comp.settings.set("ncolors_colormap", ncolors)
        except ValueError:
            pass

    def update_autoscale(self, event):
        if self.autoscale.ui_model_value:
            self.comp.colormap.autoscale = True
            self.comp.wgpu.scene.redraw(blocking=True)
            self.minval.ui_model_value = self.comp.colormap.minval
            self.maxval.ui_model_value = self.comp.colormap.maxval
        else:
            self.comp.colormap.autoscale = False
        self.update_settings()

    def update_settings(self):
        self.comp.settings.set(
            "colormap",
            (
                self.comp.colormap.autoscale,
                self.comp.colormap.discrete,
                self.comp.colormap.minval,
                self.comp.colormap.maxval,
            ),
        )

    def update_min(self, event):
        try:
            self.comp.colormap.set_min(float(self.minval.ui_model_value))
            self.autoscale.ui_model_value = False
            self.comp.wgpu.scene.render()
            self.update_settings()
        except ValueError:
            pass

    def update_max(self, event):
        try:
            self.comp.colormap.set_max(float(self.maxval.ui_model_value))
            self.autoscale.ui_model_value = False
            self.comp.wgpu.scene.render()
            self.update_settings()
        except ValueError:
            pass

    def update_discrete(self, event):
        self.comp.colormap.set_discrete(self.discrete.ui_model_value)
        self.comp.wgpu.scene.render()
        self.update_settings()

    def _update(self):
        self.autoscale.ui_model_value = self.comp.colormap.autoscale
        self.minval.ui_model_value = self.comp.colormap.minval
        self.maxval.ui_model_value = self.comp.colormap.maxval
        self.discrete.ui_model_value = bool(self.comp.colormap.discrete)


class DeformationSettings(QCard):
    def __init__(self, comp):
        self.comp = comp
        self._enable = QCheckbox(
            ui_label="Enable Deformation",
            ui_model_value=comp.settings.get("deformation_enabled", False),
        )
        self._enable.on_update_model_value(self.enable)
        self._deform_scale = QInput(
            ui_label="Deformation Scale",
            ui_type="number",
            ui_model_value=comp.settings.get("deformation_scale", 1.0),
        )
        self._deform_scale2 = QSlider(
            ui_model_value=comp.settings.get("deformation_scale2", 1.0),
            ui_min=0.0,
            ui_max=1.0,
            ui_step=0.01,
        )
        self._deform_scale.on_change(self.change_scale)
        self._deform_scale2.on_update_model_value(self.change_scale)
        super().__init__(
            QCardSection(
                Heading("Deformation Settings", 5),
                self._enable,
                self._deform_scale2,
                self._deform_scale,
            )
        )

    def enable(self, event):
        self.comp.settings.set("deformation_enabled", self._enable.ui_model_value)
        if hasattr(self.comp, "mdata"):
            scale = 0.0
            if self._enable.ui_model_value:
                try:
                    scale = float(self._deform_scale.ui_model_value) * float(
                        self._deform_scale2.ui_model_value
                    )
                except ValueError:
                    scale = 1.0
            self.comp.mdata.deformation_scale = scale
        self.comp.wgpu.scene.render()

    @debounce
    def change_scale(self, event):
        try:
            self.comp.settings.set(
                "deformation_scale", float(self._deform_scale.ui_model_value)
            )
            self.comp.settings.set(
                "deformation_scale2", float(self._deform_scale2.ui_model_value)
            )
            scale = float(self._deform_scale.ui_model_value) * float(
                self._deform_scale2.ui_model_value
            )
            self.comp.mdata.deformation_scale = scale
            self.comp.wgpu.scene.render()
        except ValueError:
            pass


class Options(QCard):
    def __init__(self, comp):
        self.comp = comp
        self.wireframe_visible = QCheckbox(
            ui_label="Wireframe Visible",
            ui_model_value=comp.settings.get("wireframe_visible", True),
        )
        reset_camera = QBtn(
            ui_icon="mdi-refresh",
            ui_label="Reset Camera",
            ui_flat=True,
            ui_color="primary",
        )
        reset_camera.on_click(self.reset_camera)
        self.wireframe_visible.on_update_model_value(self.toggle_wireframe)
        items = [Heading("Options", 5), reset_camera, self.wireframe_visible]
        if comp.draw_surf:
            self.surface_solution_visible = QCheckbox(
                ui_label="Surface Solution Visible",
                ui_model_value=comp.settings.get("elements2d_visible", True),
            )
            self.surface_solution_visible.on_update_model_value(
                self.toggle_surface_solution
            )
            items.append(self.surface_solution_visible)
        if comp.mesh.dim == 3:
            self.clipping_plane_visible = QCheckbox(
                ui_label="Clipping Function",
                ui_model_value=comp.settings.get("clipping_visible", True),
            )
            items.append(self.clipping_plane_visible)
            self.clipping_plane_visible.on_update_model_value(
                self.toggle_clipping_function
            )
        if self.comp.contact is not None:
            self.contact_visible = QCheckbox(
                ui_label="Contact Pairs",
                ui_model_value=comp.settings.get("contact_enabled", True),
            )
            self.contact_visible.on_update_model_value(self.toggle_contact_pairs)
            items.append(self.contact_visible)
        super().__init__(QCardSection(*items))

    def toggle_wireframe(self, event):
        self.comp.wireframe.active = self.wireframe_visible.ui_model_value
        self.comp.wgpu.scene.render()

    def toggle_clipping_function(self, event):
        self.comp.clippingcf.active = self.clipping_plane_visible.ui_model_value
        self.comp.wgpu.scene.render()

    def toggle_surface_solution(self, event):
        self.comp.settings.set(
            "elements2d_visible", self.surface_solution_visible.ui_model_value
        )
        self.comp.elements2d.active = self.surface_solution_visible.ui_model_value
        self.comp.wgpu.scene.render()

    def toggle_contact_pairs(self, event):
        enabled = self.contact_visible.ui_model_value
        # persist setting
        self.comp.settings.set("contact_enabled", enabled)
        # toggle visualization object if it exists
        self.comp.contact_pairs.active = enabled
        self.comp.wgpu.scene.render()

    def reset_camera(self, event):
        pmin, pmax = self.comp.wgpu.scene.bounding_box
        camera = self.comp.wgpu.scene.options.camera
        camera.reset(pmin, pmax)
        self.comp.wgpu.scene.render()


class VectorSettings(QCard):
    def __init__(self, comp):
        self.comp = comp
        options = ["Norm"] + [str(i) for i in range(1, comp.cf.dim + 1)]
        comps = []
        self.color_component = QSelect(
            ui_options=options, ui_model_value=options[0], ui_label="Color Component"
        )
        comps.append(self.color_component)
        self.color_component.on_update_model_value(self.update_color_component)
        if comp.mesh.dim == 3 and comp.cf.dim == 3:
            self.clipping_vectors = QCheckbox(
                ui_label="Show Clipping Vectors",
                ui_model_value=comp.settings.get("clipping_vectors", False),
            )
            self.clipping_vectors.on_update_model_value(self.update_clipping_vectors)
            comps.append(self.clipping_vectors)
        if comp.mesh.dim == 2 and comp.cf.dim == 2 or comp.mesh.dim == 3 and comp.cf.dim == 3:
            self.surf_vectors = QCheckbox(
                ui_label="Show Surface Vectors",
                ui_model_value=comp.settings.get("surface_vectors", False),
            )
            self.surf_vectors.on_update_model_value(self.update_surface_vectors)
            comps.append(self.surf_vectors)
        self.grid_size = QInput(
            ui_label="Grid Size",
            ui_type="number",
            ui_model_value=comp.settings.get("vector_grid_size", 20.0),
        )
        self.grid_size.on_change(self.update_grid_size)
        comps.append(self.grid_size)
        super().__init__(
            QCardSection(
                Heading("Vector Settings", 5),
                *comps
            )
        )

    def update_clipping_vectors(self, event):
        self.comp.clipping_vectors.active = self.clipping_vectors.ui_model_value
        self.comp.settings.set("clipping_vectors", self.clipping_vectors.ui_model_value)
        self.comp.wgpu.scene.render()

    def update_surface_vectors(self, event):
        self.comp.surface_vectors.active = self.surf_vectors.ui_model_value
        self.comp.settings.set("surface_vectors", self.surf_vectors.ui_model_value)
        self.comp.wgpu.scene.render()

    def update_grid_size(self, event):
        try:
            grid_size = float(self.grid_size.ui_model_value)
            self.comp.settings.set("vector_grid_size", grid_size)
            if self.comp.clipping_vectors is not None:
                self.comp.clipping_vectors.set_grid_size(grid_size)
                self.comp.clipping_vectors.set_needs_update()
            if self.comp.surface_vectors is not None:
                self.comp.surface_vectors.set_grid_size(grid_size)
                self.comp.surface_vectors.set_needs_update()
            self.comp.wgpu.scene.render()
        except ValueError:
            pass

    def update_color_component(self, event):
        index = self.color_component.ui_options.index(
            self.color_component.ui_model_value
        )
        comp = self.comp
        if comp.elements2d is not None:
            comp.elements2d.set_component(index - 1)
        if comp.clippingcf is not None:
            comp.clippingcf.set_component(index - 1)
        comp.colorbar.set_needs_update()
        comp.wgpu.scene.render()


class FieldLinesSettings(QCard):
    def __init__(self, comp):
        self.comp = comp
        self.show_fieldlines = QCheckbox(
            ui_label="Show Field Lines",
            ui_model_value=comp.settings.get("field_lines", False),
        )
        self.show_fieldlines.on_update_model_value(self.update_show)

        self.num_lines = QInput(
            ui_label="Num Lines",
            ui_type="number",
            ui_model_value=comp.settings.get("fieldlines_num_lines", 100),
        )
        self.num_lines.on_change(self.update_option)

        self.length = QInput(
            ui_label="Length",
            ui_type="number",
            ui_model_value=comp.settings.get("fieldlines_length", 0.5),
        )
        self.length.on_change(self.update_option)

        self.thickness = QInput(
            ui_label="Thickness",
            ui_type="number",
            ui_model_value=comp.settings.get("fieldlines_thickness", 0.0015),
        )
        self.thickness.on_change(self.update_option)

        direction_options = ["Both", "Forward", "Backward"]
        self.direction = QSelect(
            ui_options=direction_options,
            ui_model_value=direction_options[comp.settings.get("fieldlines_direction", 0)],
            ui_label="Direction",
        )
        self.direction.on_update_model_value(self.update_option)

        self.recalc_btn = QBtn(ui_label="Recalculate", ui_color="primary", ui_flat=True)
        self.recalc_btn.on_click(self.recalculate)

        super().__init__(
            QCardSection(
                Heading("Field Lines", 5),
                self.show_fieldlines,
                self.num_lines,
                self.length,
                self.thickness,
                self.direction,
                self.recalc_btn,
            )
        )

    def update_show(self, event):
        self.comp.settings.set("field_lines", self.show_fieldlines.ui_model_value)
        if self.comp.fieldlines is not None:
            self.comp.fieldlines.active = self.show_fieldlines.ui_model_value
        self.comp.wgpu.scene.render()

    def _get_options(self):
        direction_map = {"Both": 0, "Forward": 1, "Backward": -1}
        return {
            "num_lines": int(float(self.num_lines.ui_model_value)),
            "length": float(self.length.ui_model_value),
            "thickness": float(self.thickness.ui_model_value),
            "direction": direction_map[self.direction.ui_model_value],
        }

    def update_option(self, event):
        try:
            opts = self._get_options()
        except (ValueError, KeyError):
            return
        self.comp.settings.set("fieldlines_num_lines", opts["num_lines"])
        self.comp.settings.set("fieldlines_length", opts["length"])
        self.comp.settings.set("fieldlines_thickness", opts["thickness"])
        self.comp.settings.set("fieldlines_direction", opts["direction"])

    def recalculate(self, event):
        try:
            opts = self._get_options()
        except (ValueError, KeyError):
            return
        if self.comp.fieldlines is not None:
            self.comp.fieldlines.fieldline_options.update(opts)
            self.comp.fieldlines.set_needs_update()
            self.comp.wgpu.scene.render()

class Sidebar(QDrawer):
    def __init__(self, comp):
        self.comp = comp
        colorbar_menu = QMenu(ColorbarSettings(comp), ui_anchor="top right")
        items = [
            QItem(
                QItemSection(QIcon(ui_name="mdi-palette-outline"), ui_avatar=True),
                QItemSection("Colorbar"),
                colorbar_menu,
                ui_clickable=True,
            ),
        ]
        if self.comp.mesh.dim == 3:
            items.append(ClippingSettings(comp))

        if self.comp.deformation is not None or (
            self.comp.cf.dim == 1 and self.comp.mesh.dim < 3
        ):
            deformation_menu = QMenu(DeformationSettings(comp), ui_anchor="top right")
            items.append(
                QItem(
                    QItemSection(QIcon(ui_name="mdi-arrow-expand-all"), ui_avatar=True),
                    QItemSection("Deformation"),
                    deformation_menu,
                    ui_clickable=True,
                )
            )
        if comp.cf.dim > 1:
            vector_menu = QMenu(VectorSettings(comp), ui_anchor="top right")
            items.append(
                QItem(
                    QItemSection(
                        QIcon(ui_name="mdi-arrow-top-right-thin"), ui_avatar=True
                    ),
                    QItemSection("Vector Settings"),
                    vector_menu,
                    ui_clickable=True,
                )
            )
        if comp.cf.dim == comp.mesh.dim:
            fieldlines_menu = QMenu(FieldLinesSettings(comp), ui_anchor="top right")
            items.append(
                QItem(
                    QItemSection(QIcon(ui_name="mdi-chart-timeline-variant"), ui_avatar=True),
                    QItemSection("Field Lines"),
                    fieldlines_menu,
                    ui_clickable=True,
                )
            )
        option_menu = QMenu(Options(comp), ui_anchor="top right")
        items.append(
            QItem(
                QItemSection(QIcon(ui_name="mdi-cog-outline"), ui_avatar=True),
                QItemSection("Options"),
                option_menu,
                ui_clickable=True,
            )
        )
        self.qlist = QList(*items, ui_padding=True, ui_class="menu-list")
        super().__init__(
            self.qlist, ui_width=200, ui_bordered=True, ui_model_value=True
        )

    def append_component(self, *args):
        self.qlist.ui_children = self.qlist.ui_children + [
            QItem(*[QItemSection(a) for a in args])
        ]


class FunctionComponent(WebgpuTab):
    def __init__(self, name, data, app_data):
        self.app_data = app_data
        cf = data["obj"]
        self.name = name
        self.mdata = None
        self.cf = cf
        self.region_or_mesh = data["mesh"]
        self.draw_vol = data.get("draw_vol", True)
        self.draw_surf = data.get("draw_surf", True)
        self.mesh = self.region_or_mesh.mesh if isinstance(self.region_or_mesh, ngs.Region) else self.region_or_mesh
        self.order = data.get("order", None)
        if self.order is None:
            self.order = 2
            if isinstance(cf, ngs.GridFunction):
                self.order = min(2, cf.space.globalorder)
        self.deformation = data.get("deformation", None)
        self.contact = data.get("contact", None)
        self.contact_pairs = None
        minval = data.get("min", 0.0)
        maxval = data.get("max", 1.0)
        autoscale = not ("min" in data or "max" in data) and not data.get("autoscale", False)
        discrete_colormap = data.get("discrete_colormap", False)
        if any([v in data for v in ("min", "max", "discrete_colormap", "autoscale")]):
            self.settings.set(
                "colormap", (autoscale, discrete_colormap, minval, maxval)
            )
        if self.deformation is None and not "deformation" in data and self.cf.dim == 1 and self.mesh.dim < 3:
            self.deformation = ngs.CF((0, 0, self.cf))
        if data.get("deformation", None) is not None:
            self.settings.set("deformation_enabled", True)
        cv = data.get("clipping_vectors", False)
        if cv:
            if isinstance(cv, bool):
                self.settings.set("clipping_vectors", cv)
            else:
                self.settings.set("clipping_vectors", True)
                self.settings.set("vector_grid_size", cv)
        sv = data.get("surface_vectors", False)
        if sv:
            if isinstance(sv, bool):
                self.settings.set("surface_vectors", sv)
            else:
                self.settings.set("surface_vectors", True)
                self.settings.set("vector_grid_size", sv)
        fl = data.get("field_lines", False)
        if fl:
            self.settings.set("field_lines", True)
        if "clipping_function" in data:
            self.settings.set("clipping_visible", data["clipping_function"])
        super().__init__(name, data, app_data)

    def create_sidebar(self):
        return Sidebar(self)

    def draw(self):
        func_data = self.app_data.get_function_gpu_data(
            self.cf, self.region_or_mesh, order=self.order
        )
        mdata = func_data.mesh_data

        if self.deformation is not None:
            deform_data = self.app_data.get_function_gpu_data(
                self.deformation, self.region_or_mesh, order=1
            )
            mdata = copy.copy(deform_data.mesh_data)
            self.mdata = mdata
            deform_data.mesh_data = mdata
            mdata.deformation_data = deform_data
            mdata.deformation_scale = self.settings.get(
                "deformation_scale", 1.0
            ) * self.settings.get("deformation_scale2", 1.0)
            if not self.settings.get("deformation_enabled", False):
                mdata.deformation_scale = 0.0
            func_data.mesh_data = mdata
        self.wireframe = MeshWireframe2d(mdata, clipping=self.clipping)
        self.wireframe.active = self.settings.get("wireframe_visible", True)

        autoscale, discrete, minval, maxval = self.settings.get(
            "colormap", (True, False, 0.0, 1.0)
        )
        self.colormap = Colormap(minval=minval, maxval=maxval)
        self.colormap.autoscale = autoscale
        self.colormap.discrete = discrete
        self.clipping_vectors = None
        if self.cf.dim == self.mesh.dim:
            vec3 = self.cf
            if self.cf.dim == 2:
                vec3 = ngs.CF((self.cf[0], self.cf[1], 0))
            vec_data = self.app_data.get_function_gpu_data(vec3,
                                                           self.region_or_mesh, order=self.order)
            self.surface_vectors = SurfaceVectors(vec_data, clipping=self.clipping, colormap=self.colormap,
                                                  grid_size=self.settings.get("vector_grid_size", 20))
            self.surface_vectors.active = self.settings.get("surface_vectors", False)
        else:
            self.surface_vectors = None
        self.fieldlines = None
        if self.cf.dim == self.mesh.dim:
            from ngsolve_webgpu.cf import FieldLines
            vec3 = self.cf if self.cf.dim == 3 else ngs.CF((self.cf[0], self.cf[1], 0))
            self.fieldlines = FieldLines(
                vec3,
                self.region_or_mesh,
                num_lines=self.settings.get("fieldlines_num_lines", 100),
                length=self.settings.get("fieldlines_length", 0.5),
                thickness=self.settings.get("fieldlines_thickness", 0.0015),
                direction=self.settings.get("fieldlines_direction", 0),
            )
            self.fieldlines.active = self.settings.get("field_lines", False)
        if self.mesh.dim == 3 and self.draw_vol:
            self.clippingcf = ClippingCF(func_data, self.clipping, self.colormap)
            self.clippingcf.active = self.settings.get("clipping_visible", True)
            if self.cf.dim == 3:
                self.clipping_vectors = ClippingVectors(
                    func_data,
                    clipping=self.clipping,
                    colormap=self.colormap,
                    grid_size=self.settings.get("vector_grid_size", 20),
                )
                self.clipping_vectors.active = self.settings.get(
                    "clipping_vectors", False
                )
        else:
            self.clippingcf = None
        if self.draw_surf:
            self.elements2d = CFRenderer(
                func_data, clipping=self.clipping, colormap=self.colormap
            )
            self.elements2d.active = self.settings.get("elements2d_visible", True)
        else:
            self.elements2d = None
        self.colorbar = Colorbar(self.colormap)
        self.colorbar.width = 0.8
        self.colorbar.position = (-0.5, 0.9)

        if self.contact is not None:
            from ngsolve_webgpu.contact import ContactPairs
            from webgpu.renderer import MultipleRenderer
            if isinstance(self.contact, list):
                from .region_colors import get_random_colors
                colors = get_random_colors(len(self.contact))
                self.contact_pairs = MultipleRenderer([ContactPairs(self.region_or_mesh, cb, color=c) for cb,c in zip(self.contact, colors)])
            else:
                self.contact_pairs = ContactPairs(
                    self.region_or_mesh,
                    self.contact,
                )
            self.contact_pairs.active = self.settings.get(
                "contact_enabled", True
            )

        render_objects = [
            obj
            for obj in [
                self.clippingcf,
                self.elements2d,
                self.wireframe,
                self.colorbar,
                self.contact_pairs,
                self.clipping_vectors,
                self.surface_vectors,
                self.fieldlines,
            ]
            if obj is not None
        ]
        self.wgpu.draw(render_objects, camera=self.camera)

        def set_min_max():
            self.min_max = (self.colormap.minval, self.colormap.maxval)
            self.settings.set(
                "colormap",
                (self.colormap.autoscale, self.colormap.discrete, self.colormap.minval, self.colormap.maxval),
            )

        self.wgpu.on_mounted(set_min_max)

        self.func_data = func_data
