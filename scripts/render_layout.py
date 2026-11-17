"""Renders still images of the third model (four shelves under two tables) to output/images/.

Part colors come from the viewer pages, so run build_viewer.py and build_tables.py first
if either model has changed. Needs a Python with build123d and VTK.
"""
import json
import re
import runpy
from pathlib import Path

import vtk

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "output"
IMAGES = OUT / "images"
IN = 25.4
SIZE = (2000, 1400)

ns = runpy.run_path(str(HERE / "workbench_layout.py"))


def model_data(path):
    match = re.search(r'id="model-data">(.*?)</script>', path.read_text(), re.S)
    return json.loads(match.group(1))["parts"]


unit_colors = [part["color"] for part in model_data(OUT / "shelf_viewer.html")]
unit_names = list(ns["UNIT"])
assert len(unit_colors) == len(unit_names)
color_of = dict(zip(unit_names, unit_colors))


def rgb(color):
    return [int(color[i:i + 2], 16) / 255 for i in (1, 3, 5)]


renderer = vtk.vtkRenderer()
renderer.SetBackground(0.71, 0.75, 0.75)  # darker than the white frames so they stay visible
vtk.vtkMapper.SetResolveCoincidentTopologyToPolygonOffset()
renderer.SetUseFXAA(True)
renderer.TwoSidedLightingOn()


def add_part(shape, color):
    vertices, triangles = shape.tessellate(0.2, 0.3)
    points = vtk.vtkPoints()
    for p in vertices:
        points.InsertNextPoint(p.X, p.Y, p.Z)
    cells = vtk.vtkCellArray()
    for a, b, c in triangles:
        cells.InsertNextCell(3, [a, b, c])
    poly = vtk.vtkPolyData()
    poly.SetPoints(points)
    poly.SetPolys(cells)
    normals = vtk.vtkPolyDataNormals()
    normals.SetInputData(poly)
    normals.SetFeatureAngle(30)
    normals.ConsistencyOn()
    normals.AutoOrientNormalsOn()
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(normals.GetOutputPort())
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    prop = actor.GetProperty()
    prop.SetColor(*rgb(color))
    prop.SetAmbient(0.22)
    prop.SetDiffuse(0.68)
    prop.SetSpecular(0.04)
    renderer.AddActor(actor)
    edges = vtk.vtkFeatureEdges()
    edges.SetInputData(poly)
    edges.SetFeatureAngle(30)
    edges.BoundaryEdgesOff()
    edges.ManifoldEdgesOff()
    edges.NonManifoldEdgesOff()
    edge_mapper = vtk.vtkPolyDataMapper()
    edge_mapper.SetInputConnection(edges.GetOutputPort())
    edge_mapper.ScalarVisibilityOff()
    edge_actor = vtk.vtkActor()
    edge_actor.SetMapper(edge_mapper)
    edge_actor.GetProperty().SetColor(0.2, 0.2, 0.2)
    edge_actor.GetProperty().SetOpacity(0.45)
    renderer.AddActor(edge_actor)
    return actor, edge_actor


tops = []
for name, record in ns["table_ns"]["parts"].items():
    pair = add_part(record[0], record[3])
    if name.endswith("_top") or "_panel" in name or "_outlet_" in name:
        tops.extend(pair)
# Shelf part names are "shelf_<label>_<unit name>"; viewer colors follow the same order.
for name, shape in ns["shelf_parts"].items():
    add_part(shape, color_of[name.split("_", 2)[2]])
tote_colors = [part["color"] for part in model_data(OUT / "tote_viewer.html")]
assert len(tote_colors) == len(ns["TOTE_UNIT"])
tote_color_of = dict(zip(ns["TOTE_UNIT"], tote_colors))
for name, shape in ns["tote_parts"].items():
    add_part(shape, tote_color_of[name.split("_", 2)[2]])

lights = vtk.vtkLightKit()
lights.SetKeyLightIntensity(0.68)
lights.SetKeyToFillRatio(2.2)
lights.SetKeyToHeadRatio(2.5)
lights.AddLightsToRenderer(renderer)

window = vtk.vtkRenderWindow()
window.SetOffScreenRendering(1)
window.AddRenderer(renderer)
window.SetSize(*SIZE)
window.SetMultiSamples(0)

CENTER = (36, 30, 19)
# name: camera direction, focal point (in), and framing. parallel = half the view height in inches.
VIEWS = {
    "01_front_three_quarter": {"dir": (-0.62, -1, 0.34), "angle": 24, "dist": 215},
    "02_rear_three_quarter": {"dir": (0.72, 1, 0.34), "angle": 24, "dist": 215},
    "03_long_side": {"dir": (0, -1, 0), "parallel": 28, "focus": (36, 30, 19.5)},
    "04_end_profile": {"dir": (-1, 0, 0), "parallel": 24, "focus": (36, 30, 19.5)},
    "05_floor_plan_tops_hidden": {"dir": (0, 0, 1), "parallel": 33, "up": (0, 1, 0), "hide_tops": True},
    "06_knee_space": {"dir": (-0.3, -1, 0.14), "angle": 30, "dist": 135, "focus": (36, 10, 18)},
    "07_totes_on_lower_shelf": {"dir": (-0.32, -1, 0.5), "angle": 24, "dist": 75, "focus": (20.2, 20, 9.5)},
}

IMAGES.mkdir(parents=True, exist_ok=True)
for name, view in VIEWS.items():
    for actor in tops:
        actor.SetVisibility(not view.get("hide_tops", False))
    camera = renderer.GetActiveCamera()
    focus = view.get("focus", CENTER)
    direction = view["dir"]
    length = sum(c * c for c in direction) ** 0.5
    distance = view.get("dist", 400)
    camera.SetFocalPoint(*(f * IN for f in focus))
    camera.SetPosition(*((f + d / length * distance) * IN for f, d in zip(focus, direction)))
    camera.SetViewUp(*view.get("up", (0, 0, 1)))
    if "parallel" in view:
        camera.ParallelProjectionOn()
        camera.SetParallelScale(view["parallel"] * IN)
    else:
        camera.ParallelProjectionOff()
        camera.SetViewAngle(view["angle"])
    renderer.ResetCameraClippingRange()
    window.Render()
    grab = vtk.vtkWindowToImageFilter()
    grab.SetInput(window)
    grab.Update()
    writer = vtk.vtkPNGWriter()
    path = IMAGES / f"{name}.png"
    writer.SetFileName(str(path))
    writer.SetInputConnection(grab.GetOutputPort())
    writer.Write()
    print(path.name, round(path.stat().st_size / 1e3), "KB")
