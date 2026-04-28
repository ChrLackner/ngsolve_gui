from ngapp.components import *
from ngsolve_gui.region_colors import RegionColors


class MeshColorSection(QExpansionItem):
    def __init__(self, comp):
        self.comp = comp
        colors = [fd.color for fd in comp.mesh.ngmesh.FaceDescriptors()]
        colors = [(c[0], c[1], c[2], c[3]) for c in colors]
        names = [fd.bcname for fd in comp.mesh.ngmesh.FaceDescriptors()]
        face_colors = RegionColors("Face Colors", colors, names)
        face_colors_card = QCard(
            QCardSection(face_colors), ui_flat=True, ui_bordered=True
        )
        face_colors.on_change_color(self.change_color)
        color_cards = [face_colors_card]

        edge_descriptors = list(comp.mesh.ngmesh.EdgeDescriptors())
        if edge_descriptors:
            enames = [ed.name for ed in edge_descriptors]
            saved = comp.settings.get("edge_colors", {})
            self.ecolors = {name: saved.get(name, [0, 0, 0, 255]) for name in set(enames)}
            ecolors = [
                (c[0] / 255, c[1] / 255, c[2] / 255, c[3] / 255 if c[3] > 1 else c[3])
                for c in [self.ecolors[name] for name in enames]
            ]
            edge_colors = RegionColors("Edge Colors", ecolors, enames)
            edge_colors_card = QCard(
                QCardSection(edge_colors), ui_flat=True, ui_bordered=True
            )
            edge_colors.on_change_color(self.change_edge_color)
            color_cards.append(edge_colors_card)

        if comp.mesh.dim == 3:
            dnames = list(set(comp.mesh.GetMaterials()))
            dcolors = [(1.0, 0.0, 0.0, 1.0) for _ in range(len(dnames))]
            domain_colors = RegionColors("Domain Colors", dcolors, dnames)
            self.dcolors = {
                name: [int(255 * ci) for i, ci in enumerate(dcol)]
                for name, dcol in zip(dnames, dcolors)
            }
            domain_colors_card = QCard(
                QCardSection(domain_colors), ui_flat=True, ui_bordered=True
            )
            domain_colors.on_change_color(self.change_d_color)
            color_cards.append(domain_colors_card)

        super().__init__(
            *color_cards,
            ui_icon="mdi-palette",
            ui_label="Colors",
        )

    def change_color(self, name, color):
        colors = []
        colmap = dict(zip(name, color))
        for fd in self.comp.mesh.ngmesh.FaceDescriptors():
            if fd.bcname in colmap:
                fd.color = colmap[fd.bcname]
            colors.append(
                [
                    int(fd.color[0] * 255),
                    int(fd.color[1] * 255),
                    int(fd.color[2] * 255),
                    int(fd.color[3] * 255),
                ]
            )
        self.comp.elements2d.gpu_objects.colormap.set_colormap(colors)
        self.comp.elements2d.set_needs_update()
        self.comp.wgpu.scene.render()

    def change_edge_color(self, name, color):
        colmap = dict(zip(name, color))
        for n, c in colmap.items():
            self.ecolors[n] = [
                int(c[0] * 255),
                int(c[1] * 255),
                int(c[2] * 255),
                int(c[3] * 255),
            ]
        self.comp.settings.set("edge_colors", self.ecolors)
        edge_descriptors = list(self.comp.mesh.ngmesh.EdgeDescriptors())
        colors = [self.ecolors[ed.name] for ed in edge_descriptors]
        self.comp.elements1d._user_colors = colors
        self.comp.elements1d.set_needs_update()
        self.comp.wgpu.scene.render()

    def change_d_color(self, name, color):
        colors = []
        colmap = dict(zip(name, color))
        for i, d in enumerate(self.comp.mesh.GetMaterials()):
            if d in colmap:
                c = list(colmap[d])
            else:
                c = [1.0, 0.0, 0.0, 1.0]
            self.dcolors[d] = [
                int(c[0] * 255),
                int(c[1] * 255),
                int(c[2] * 255),
                int(c[3] * 255),
            ]
            colors.append(self.dcolors[d])
        if self.comp.elements3d is not None:
            self.comp.elements3d.colormap.set_colormap(colors)
            self.comp.elements3d.set_needs_update()
            self.comp.wgpu.scene.render()
