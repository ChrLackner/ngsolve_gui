"""Region visibility state + derived per-element alphas.

Owns the mesh's region metadata (materials, boundaries, face-descriptor
adjacency) and the user's intent — a set of hidden volume regions plus
explicit per-boundary overrides — and derives the effective alpha arrays for
:class:`ngsolve_webgpu.RegionVisibility`.

The core rule: a boundary/interface face is drawn iff at least ONE of its
adjacent volume regions is visible. Hiding ``region1`` hides its exterior
surfaces, but an interface to a visible ``region2`` stays until region2 is
hidden too. Per-boundary overrides (``True`` = force show, ``False`` = force
hide, absent = auto) win over the derived state.

Indexing follows netgen: volume alphas by material number - 1 (3D element
``index``), surface alphas by face descriptor number - 1 on 3D meshes and by
material number - 1 on 2D meshes (2D element ``index``). Regions are
addressed by *name*; repeated names toggle together.
"""

import numpy as np


class RegionState:
    def __init__(self, mesh):
        self.mesh = mesh
        self.hidden = set()      # hidden volume/material region names
        self.overrides = {}      # boundary name -> True (show) / False (hide)

        self.materials = list(mesh.GetMaterials())
        if mesh.dim == 3:
            self.boundaries = list(mesh.GetBoundaries())
            self.fd_doms = [
                (fd.domin, fd.domout) for fd in mesh.ngmesh.FaceDescriptors()
            ]
            # One boundary region per face descriptor (same assumption the
            # renderer's element data makes: el2d index == fd number).
            n = min(len(self.boundaries), len(self.fd_doms))
            self.boundaries = self.boundaries[:n]
            self.fd_doms = self.fd_doms[:n]
        else:
            self.boundaries = []
            self.fd_doms = []

    # -- name helpers ------------------------------------------------------

    @property
    def unique_materials(self):
        return list(dict.fromkeys(self.materials))

    @property
    def unique_boundaries(self):
        return list(dict.fromkeys(self.boundaries))

    def material_name(self, index):
        """Region name for a 0-based material index (None if out of range)."""
        if 0 <= index < len(self.materials):
            return self.materials[index]
        return None

    # -- derived alphas ----------------------------------------------------

    def vol_alphas(self):
        return np.array(
            [0.0 if m in self.hidden else 1.0 for m in self.materials],
            dtype=np.float32,
        )

    def surf_alphas(self):
        if self.mesh.dim != 3:
            # 2D: the drawn surface elements ARE the materials.
            return self.vol_alphas()
        vol = self.vol_alphas()
        nmat = len(vol)
        alphas = np.empty(len(self.fd_doms), dtype=np.float32)
        for i, (name, doms) in enumerate(zip(self.boundaries, self.fd_doms)):
            ov = self.overrides.get(name)
            if ov is not None:
                alphas[i] = 1.0 if ov else 0.0
                continue
            doms = [d for d in doms if 1 <= d <= nmat]
            # Auto: visible iff any adjacent volume region is visible.
            # Free-standing surfaces (no volume neighbours) stay visible.
            alphas[i] = 1.0 if (not doms or any(vol[d - 1] > 0 for d in doms)) else 0.0
        return alphas

    # -- queries for the UI ------------------------------------------------

    def material_visible(self, name):
        return name not in self.hidden

    def boundary_effective(self, name):
        """Whether any face descriptor with this name is currently drawn."""
        alphas = self.surf_alphas()
        return any(
            alphas[i] > 0 for i, n in enumerate(self.boundaries) if n == name
        )

    def visible_boundary_names(self):
        alphas = self.surf_alphas()
        return list(dict.fromkeys(
            n for i, n in enumerate(self.boundaries) if alphas[i] > 0
        ))

    def any_hidden(self):
        """True if the current state hides anything relative to the default."""
        if self.hidden & set(self.materials):
            return True
        return any(
            self.overrides.get(n) is False for n in self.boundaries
        )
