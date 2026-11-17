"""Verifies tote.py, then writes its STEP file and viewer page to output/."""
import base64
import itertools
import json
import re
import runpy
from pathlib import Path

import numpy as np
from build123d import Compound, export_step, import_step

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "output"
IN = 25.4

ns = runpy.run_path(str(HERE / "tote.py"), init_globals={"show": lambda *a, **k: None})
wood, screws, result = ns["wood"], ns["screws"], ns["result"]
shapes = {**wood, **{f"screw_{n}": s for n, s in screws.items()}}
print("solids:", len(result.solids()), "wood:", len(wood), "screws:", len(screws))
print("invalid:", [n for n, s in shapes.items() if not s.is_valid], "multi-solid:", [n for n, s in shapes.items() if len(s.solids()) != 1])
box = result.bounding_box()
print("bbox in:", [round(v / IN, 3) for v in (box.size.X, box.size.Y, box.size.Z)])
for name, shape in wood.items():
    size = shape.bounding_box().size
    print(f"  {name}: {size.X / IN:.3f} x {size.Y / IN:.3f} x {size.Z / IN:.3f}")
handle = wood["handle"].bounding_box()
print("grip top in:", round(handle.max.Z / IN, 3))


def bbox_overlap(a, b):
    p, q = a.bounding_box(), b.bounding_box()
    return (p.min.X < q.max.X and q.min.X < p.max.X and p.min.Y < q.max.Y
            and q.min.Y < p.max.Y and p.min.Z < q.max.Z and q.min.Z < p.max.Z)


overlaps = []
for (na, a), (nb, b) in itertools.combinations(shapes.items(), 2):
    if bbox_overlap(a, b):
        common = a & b
        volume = sum(s.volume for s in common.solids()) if common is not None else 0
        if volume > 0.01:
            overlaps.append((na, nb, round(volume, 2)))
print("overlaps:", overlaps)

# Every screw tip must stay buried in wood.
for name, shape in screws.items():
    size = shape.bounding_box()
    print(f"  screw {name}: x {size.min.X / IN:.3f}-{size.max.X / IN:.3f} y {size.min.Y / IN:.3f}-{size.max.Y / IN:.3f} z {size.min.Z / IN:.3f}-{size.max.Z / IN:.3f}")

OUT.mkdir(exist_ok=True)
children = []
for name, shape in shapes.items():
    solid = shape.solids()[0]
    solid.label = name
    children.append(solid)
step_path = OUT / "tote.step"
export_step(Compound(label="tote", children=children), str(step_path))
back = import_step(str(step_path))
print("step solids:", len(back.solids()), "volume diff mm3:", round(back.volume - result.volume, 4))

COLORS = {"ply": "#e3be8a", "thin": "#e9c998", "handle": "#d3a262", "cleat": "#cf9f64", "screw": "#7b8085"}
TITLES = [
    (r"^base$", "Flat base", "ply", 1), (r"^end_", "Shaped end panel", "ply", 2),
    (r"^wall_", "Front or back wall", "thin", 2), (r"^divider_center$", "Long center divider", "thin", 1),
    (r"^divider_short", "Short divider", "thin", 2), (r"^handle$", "Round dowel handle", "handle", 1),
    (r"^cleat_", "Inside corner cleat", "cleat", 4),
]


def size_text(shape):
    s = shape.bounding_box().size
    dims = sorted((s.X / IN, s.Y / IN, s.Z / IN), reverse=True)
    return " × ".join(f"{d:.3f}".rstrip("0").rstrip(".") for d in dims) + " in"


def pack(shape, tolerance=0.06):
    vertices, triangles = shape.tessellate(tolerance, 0.2)
    v = np.array([[p.X, p.Y, p.Z] for p in vertices], dtype="<f4")
    tri = np.array(triangles, dtype="<u2")
    return base64.b64encode(v.tobytes()).decode(), base64.b64encode(tri.tobytes()).decode()


parts = []
for name, shape in wood.items():
    title, color, qty = next((w[1], w[2], w[3]) for w in TITLES if re.search(w[0], name))
    v, tri = pack(shape)
    parts.append({"name": name, "title": title, "detail": f"{size_text(shape)} · {qty} per tote", "color": COLORS[color], "group": "wood", "v": v, "t": tri})
for name, shape in screws.items():
    v, tri = pack(shape)
    parts.append({"name": f"screw:{name}", "title": "Wood screw", "detail": "#8 × 1¼ in · 12 per tote", "color": COLORS["screw"], "group": "screws", "v": v, "t": tri})

page = (HERE / "tote_viewer_template.html").read_text().replace(
    "/*__MODEL__*/", json.dumps({"parts": parts}, separators=(",", ":"))
)
(OUT / "tote_viewer.html").write_text(page)
print(len(parts), "parts,", round((OUT / "tote_viewer.html").stat().st_size / 1e6, 2), "MB")
