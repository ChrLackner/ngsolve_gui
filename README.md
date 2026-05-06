# NGSolve GUI

The desktop GUI we use internally at CERBSim for working with [NGSolve](https://ngsolve.org). Built on our in-house development stack:

- **[Netgen/NGSolve](https://ngsolve.org)** — meshing & finite elements
- **[ngapp](https://github.com/CERBSim/ngapp)** — application framework (UI components, keybindings, state management)
- **[webgpu](https://github.com/CERBSim/webgpu)** — GPU-accelerated rendering
- **[ngsolve_webgpu](https://github.com/CERBSim/ngsolve_webgpu)** — NGSolve-specific WebGPU renderers (meshes, functions, picking)

## Features

- **Geometry viewer** — visualize and inspect OCC geometries, pick faces/edges/vertices
- **Mesh viewer** — display 2D/3D meshes with wireframe, curved elements, volume shrink, region coloring
- **Function visualization** — scalar & vector fields, colormaps, deformation, clipping planes, fieldlines
- **Plots** — embedded Plotly charts for convergence studies and data analysis
- **Interactive clipping** — ctrl+click/drag/scroll to position and orient clipping planes
- **Element picking** — hover to highlight elements and regions, inspect coordinates
- **Keyboard shortcuts** — modal keybindings for fast navigation (`v` for view, `c` for clipping, etc.)
- **Navigator + property panel** — collapsible side panels with resizable splitters
- **Save/load projects** — persist state across sessions

## Installation

```/dev/null/sh#L1
pip install .
```

## Usage

```/dev/null/sh#L1-2
# Launch with a mesh/geometry file
ngsolve myfile.vol
```

```/dev/null/sh#L1-2
# Run a python script
ngsolve script.py
```

ngsolve.Draw and ngsolve.Redraw commands are automatically redirected to draw a new GUI item.

## Reuse

Feel free to use individual components in your own packages or take inspiration if you're building simulation tools with ngapp + webgpu. The main building blocks:

| Component | Purpose |
|-----------|---------|
| `WebgpuTab` | Base class for any 3D viewport tab with clipping, picking, camera |
| `MeshComponent` | Mesh visualization with all options |
| `FunctionComponent` | Scalar/vector field rendering |
| `GeometryComponent` | OCC geometry viewer with selection |
| `PlotComponent` | Plotly-based chart tab |
| `Navigator` | Left sidebar with item list |
| `PropertyPanel` | Right sidebar for per-tab settings |
| `sections/*` | Reusable UI sections (clipping, colorbar, deformation, etc.) |
