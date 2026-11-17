"""Tessellate each solid of shelf_unit.py and render with VTK (off-screen)."""
import math
import runpy
from pathlib import Path

import numpy as np
import vtk
from vtk.util.numpy_support import vtk_to_numpy

PROJECT = Path("/Users/brennan/Developer/CAD/ElectronicsStorageShelves")
OUT = PROJECT / "output"
SCRATCH = Path("/tmp")
IN = 25.4
SIZE = (1600, 1200)
COLORS = {
    "wood": (0.88, 0.73, 0.54),
    "nosing": (0.78, 0.62, 0.43),
    "tire": (0.05, 0.05, 0.06),
    "steel": (0.74, 0.75, 0.77),
    "fastener": (0.30, 0.31, 0.34),
}

ns = runpy.run_path(str(PROJECT / "scripts/shelf_unit.py"), init_globals={"show": lambda s, n=None: None})
parts = []
for name, shape in ns["wood"].items():
    parts.append((name, "nosing" if name.startswith("nosing") else "wood", shape))
for name, shape in ns["screws"].items():
    parts.append((f"screw_{name}", "fastener", shape))
for cname, (steel, tire, bolts) in ns["casters"].items():
    parts += [(f"{cname}_steel_{i}", "steel", s) for i, s in enumerate(steel)]
    parts.append((f"{cname}_tire", "tire", tire))
    parts += [(f"{cname}_screw_{i}", "fastener", s) for i, s in enumerate(bolts)]


def polydata(solid, tol=0.03, ang=0.12):
    verts, tris = solid.tessellate(tol, ang)
    pts = vtk.vtkPoints()
    for v in verts:
        pts.InsertNextPoint(v.X, v.Y, v.Z)
    cells = vtk.vtkCellArray()
    signed = 0.0
    for a, b, c in tris:
        cells.InsertNextCell(3, (a, b, c))
        va, vb, vc = verts[a], verts[b], verts[c]
        signed += (va.X * (vb.Y * vc.Z - vb.Z * vc.Y) - va.Y * (vb.X * vc.Z - vb.Z * vc.X)
                   + va.Z * (vb.X * vc.Y - vb.Y * vc.X)) / 6
    poly = vtk.vtkPolyData()
    poly.SetPoints(pts)
    poly.SetPolys(cells)
    return poly, signed


meshes = []  # (name, category, polydata with normals, feature-edge polydata)
worst = (0.0, "")
for name, category, shape in parts:
    for solid in shape.solids():
        poly, signed = polydata(solid)
        # Mesh volume confirms outward winding and that nothing tessellated to nothing.
        err = abs(signed - solid.volume) / solid.volume
        worst = max(worst, (err, name))
        assert signed > 0, f"inverted mesh: {name}"
        nrm = vtk.vtkPolyDataNormals()
        nrm.SetInputData(poly)
        nrm.SetFeatureAngle(35)
        nrm.SplittingOn()
        nrm.ConsistencyOff()
        nrm.AutoOrientNormalsOff()
        nrm.Update()
        clean = vtk.vtkCleanPolyData()
        clean.SetInputData(poly)
        edges = vtk.vtkFeatureEdges()
        edges.SetInputConnection(clean.GetOutputPort())
        edges.BoundaryEdgesOff()
        edges.NonManifoldEdgesOff()
        edges.ManifoldEdgesOff()
        edges.FeatureEdgesOn()
        edges.SetFeatureAngle(35)
        edges.Update()
        meshes.append((name, category, nrm.GetOutput(), edges.GetOutput()))
print(f"solids meshed: {len(meshes)}; worst mesh-vs-solid volume error {worst[0] * 100:.4f}% ({worst[1]})")


def actor_for(data, color, shaded=True, category=None):
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputData(data)
    mapper.ScalarVisibilityOff()
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    prop = actor.GetProperty()
    prop.SetColor(*color)
    if shaded:
        prop.SetAmbient(0.45)
        prop.SetDiffuse(0.55)
        metal = category in ("steel", "fastener")
        prop.SetSpecular(0.10 if metal else 0.02)
        prop.SetSpecularPower(30)
    else:
        prop.LightingOff()
    return actor


CENTER = np.array((15 * IN, 7.5 * IN, 14.25 * IN))


def direction(azimuth, elevation):
    """azimuth: degrees from -Y (front) toward -X (viewer's left of the unit)."""
    a, e = math.radians(azimuth), math.radians(elevation)
    return np.array((-math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))


def setup(azimuth, elevation, view_angle, dist):
    ren = vtk.vtkRenderer()
    ren.SetBackground(1, 1, 1)
    win = vtk.vtkRenderWindow()
    win.SetOffScreenRendering(1)
    win.SetSize(*SIZE)
    win.AddRenderer(ren)
    d = direction(azimuth, elevation)
    cam = ren.GetActiveCamera()
    cam.SetFocalPoint(*CENTER)
    cam.SetPosition(*(CENTER + d * dist))
    cam.SetViewUp(0, 0, 1)
    cam.SetViewAngle(view_angle)
    return ren, win, d


def grab(win):
    f = vtk.vtkWindowToImageFilter()
    f.SetInput(win)
    f.ReadFrontBufferOff()
    f.Update()
    return f.GetOutput()


def to_array(img):
    w, h, _ = img.GetDimensions()
    arr = vtk_to_numpy(img.GetPointData().GetScalars()).reshape(h, w, -1)
    return arr[:, :, :3]


def write_png(img, path, voi=None):
    src = img
    if voi:
        ext = vtk.vtkExtractVOI()
        ext.SetInputData(img)
        ext.SetVOI(*voi, 0, 0)
        ext.Update()
        src = ext.GetOutput()
    w = vtk.vtkPNGWriter()
    w.SetFileName(str(path))
    w.SetInputData(src)
    w.Write()


def render(filename, azimuth, elevation, view_angle=6.4, dist=8000.0):
    ren, win, d = setup(azimuth, elevation, view_angle, dist)
    win.SetMultiSamples(8)
    for name, cat, poly, edges in meshes:
        ren.AddActor(actor_for(poly, COLORS[cat], category=cat))
        if cat in ("wood", "nosing"):
            line = actor_for(edges, tuple(c * 0.62 for c in COLORS[cat]), shaded=False)
            line.GetProperty().SetLineWidth(1.5)
            ren.AddActor(line)
    ren.ResetCameraClippingRange()
    right = np.cross(-d, (0, 0, 1))
    right /= np.linalg.norm(right)
    ren.RemoveAllLights()
    for offset, intensity in (
        (d * 3000 - right * 1500 + np.array((0, 0, 2200)), 0.72),  # key: upper camera-left
        (d * 3000 + right * 2200 + np.array((0, 0, 300)), 0.40),  # fill: camera-right
        (d * 2000 + np.array((0, 0, -2500)), 0.25),  # low fill for the casters
        (-right * 3000 + d * 300, 0.22),  # side fill so the end panels stay light
        (right * 3000 + d * 300, 0.22),
    ):
        light = vtk.vtkLight()
        light.SetLightTypeToSceneLight()
        light.SetPositional(False)
        light.SetPosition(*(CENTER + offset))
        light.SetFocalPoint(*CENTER)
        light.SetIntensity(intensity)
        ren.AddLight(light)
    win.Render()
    img = grab(win)
    write_png(img, filename)
    arr = to_array(img)
    ys, xs = np.where((arr < 250).any(axis=2))
    print(f"{filename.name}: az {azimuth} el {elevation}; content x {xs.min()}-{xs.max()}, y {ys.min()}-{ys.max()} of {SIZE}")
    win.Finalize()
    return img


def visibility(azimuth, elevation, view_angle=6.4, dist=8000.0):
    """Flat ID pass: count unoccluded pixels per part in the same camera."""
    ren, win, _ = setup(azimuth, elevation, view_angle, dist)
    win.SetMultiSamples(0)
    for i, (name, cat, poly, _) in enumerate(meshes, start=1):
        rgb = (i * 2 / 255, (i % 7) * 30 / 255, 1 - i / 255 / 2)
        ren.AddActor(actor_for(poly, rgb, shaded=False))
    ren.ResetCameraClippingRange()
    win.Render()
    arr = to_array(grab(win)).astype(int)
    ids = arr[:, :, 0] // 2
    bg = (arr == 255).all(axis=2)
    ids[bg] = 0
    counts = np.bincount(ids.ravel(), minlength=len(meshes) + 1)
    win.Finalize()
    return {meshes[i][0]: int(counts[i + 1]) for i in range(len(meshes))}


VIEWS = {"front": (24, 7), "rear": (180 + 24, 7)}
OUT.mkdir(exist_ok=True)
for label, (az, el) in VIEWS.items():
    img = render(OUT / f"shelf_unit_{label}.png", az, el)
    vis = visibility(az, el)
    groups = {}
    for name, cat, _, _ in meshes:
        key = "screw" if name.startswith("screw_") else ("bolt" if "_screw_" in name else cat)
        g = groups.setdefault(key, [0, 0, 0])
        g[0] += 1
        g[1] += vis[name] > 0
        g[2] += vis[name]
    print(f"  {label}: visible parts/total, pixels: " + ", ".join(f"{k} {v[1]}/{v[0]} {v[2]}px" for k, v in groups.items()))
    for name in vis:
        if name.endswith("_tire"):
            print(f"    {name}: {vis[name]} px")
    print("    screws visible:", {n[6:]: vis[n] for n in vis if n.startswith("screw_") and vis[n]})
    write_png(img, SCRATCH / f"crop_{label}_bottom.png", (0, SIZE[0] - 1, 0, 420))
