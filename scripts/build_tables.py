"""Verifies workbench_tables.py, then writes its STEP file and viewer page to output/."""
import base64
import itertools
import json
import runpy
from pathlib import Path

import numpy as np
from build123d import Compound, export_step, import_step

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "output"
IN = 25.4

ns = runpy.run_path(str(HERE / "workbench_tables.py"), init_globals={"show": lambda *a, **k: None})
parts, result = ns["parts"], ns["result"]

shapes = {name: record[0] for name, record in parts.items()}
print("solids:", len(result.solids()), "invalid:", [n for n, s in shapes.items() if not s.is_valid])
box = result.bounding_box()
print("bbox in:", [round(v / IN, 3) for v in (box.size.X, box.size.Y, box.size.Z)])


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

t = ns["TOP_Z"], ns["BAR_BOTTOM_Z"], ns["TABLE_W"], ns["TABLE_D"]
top = shapes["table_a_top"].bounding_box()
bar = shapes["table_a_bar_near"].bounding_box()
print("top surface in:", round(top.max.Z / IN, 3), "table footprint in:", round(top.size.X / IN, 3), round(top.size.Y / IN, 3))
print("bar bottom in:", round(bar.min.Z / IN, 3))
legs = shapes["table_a_leg_left_near"].bounding_box(), shapes["table_a_leg_right_near"].bounding_box()
print("clear between legs along width in:", round((legs[1].min.X - legs[0].max.X) / IN, 3))
far = shapes["table_a_leg_left_far"].bounding_box()
print("clear between legs along depth in:", round((far.min.Y - legs[0].max.Y) / IN, 3))

OUT.mkdir(exist_ok=True)
step_path = OUT / "workbench_tables.step"
children = []
for name, shape in shapes.items():
    solid = shape.solids()[0]
    solid.label = name
    children.append(solid)
export_step(Compound(label="workbench_tables", children=children), str(step_path))
back = import_step(str(step_path))
print("step solids:", len(back.solids()), "volume diff mm3:", round(back.volume - result.volume, 6))


def pack(shape, tolerance=0.12):
    vertices, triangles = shape.tessellate(tolerance, 0.25)
    v = np.array([[p.X, p.Y, p.Z] for p in vertices], dtype="<f4")
    tri = np.array(triangles, dtype="<u2")
    return base64.b64encode(v.tobytes()).decode(), base64.b64encode(tri.tobytes()).decode()


items = []
for name, (shape, title, detail, color, group) in parts.items():
    v, tri = pack(shape)
    items.append({"name": name, "title": title, "detail": detail, "color": color, "group": group, "v": v, "t": tri})

page = (HERE / "tables_viewer_template.html").read_text().replace(
    "/*__MODEL__*/", json.dumps({"parts": items}, separators=(",", ":"))
)
(OUT / "workbench_tables_viewer.html").write_text(page)
print(len(items), "parts,", round((OUT / "workbench_tables_viewer.html").stat().st_size / 1e6, 2), "MB")
