"""Builds output/shelf_viewer.html: tessellates shelf_unit.py into viewer_template.html.

Run with a Python that has build123d: python scripts/build_viewer.py
"""
import base64
import json
import re
import runpy
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
OUTPUT = HERE.parent / "output" / "shelf_viewer.html"
IN = 25.4

ns = runpy.run_path(str(HERE / "shelf_unit.py"), init_globals={"show": lambda *a, **k: None})
wood, screws, casters = ns["wood"], ns["screws"], ns["casters"]

COLORS = {
    "ply": "#e3be8a", "back": "#dcb47e", "frame": "#d9ae73", "pine": "#e8cfa0",
    "trim": "#d3a262", "pad": "#c8975a", "screw": "#7b8085", "bolt": "#6d7276",
    "steel": "#b9bec2", "tire": "#222222",
}
WOOD = [
    (r"^base$", "Base / lower shelf", "ply", "ply", 1),
    (r"^side_", "Side panel", "ply", "ply", 2),
    (r"^back$", "One-piece back", "back", "ply", 1),
    (r"^upper_shelf$", "Upper shelf", "ply", "ply", 1),
    (r"^post_", "Rear corner post", "frame", "wood", 2),
    (r"^rail_bottom$", "Bottom rear rail", "frame", "wood", 1),
    (r"^rail_top$", "Rear top rail (1×2 pine)", "pine", "wood", 1),
    (r"^ledger$", "Upper rear ledger", "frame", "wood", 1),
    (r"^cleat_", "Upper side cleat", "frame", "wood", 2),
    (r"^nosing_", "Front nosing", "trim", "wood", 2),
]
PLACEHOLDER = "Placeholder; confirm on the real part"


def pack(shape, tolerance=0.12):
    vertices, triangles = shape.tessellate(tolerance, 0.25)
    v = np.array([[p.X, p.Y, p.Z] for p in vertices], dtype="<f4")
    t = np.array(triangles, dtype="<u2")
    return base64.b64encode(v.tobytes()).decode(), base64.b64encode(t.tobytes()).decode()


def size_text(shape):
    s = shape.bounding_box().size
    dims = sorted((s.X / IN, s.Y / IN, s.Z / IN), reverse=True)
    return " × ".join(f"{d:.3f}".rstrip("0").rstrip(".") for d in dims) + " in"


parts = []


def add(name, shape, title, detail, color, group, toggle=None):
    v, t = pack(shape)
    parts.append({
        "name": name, "title": title, "detail": detail, "color": COLORS[color],
        "group": group, "toggle": toggle or group, "v": v, "t": t,
    })


for name, shape in wood.items():
    title, color, group, qty = next(
        (w[1], w[2], w[3], w[4]) for w in WOOD if re.search(w[0], name)
    )
    add(name, shape, title, f"{size_text(shape)} · {qty} per unit", color, group)

for name, shape in screws.items():
    add(f"screw:{name}", shape, "Wood screw", "#8 × 1¼ in · 18 per unit", "screw", "hardware")

STEEL_NAMES = ["Top plate", "Fork cheek", "Fork cheek", "Wheel hub", "Axle", "Swivel race", "Fork crown", "Brake lever"]
for caster_name, (steel, tire, bolts) in casters.items():
    kind = "Swivel/brake" if "swivel" in caster_name else "Rigid"
    for i, shape in enumerate(steel):
        add(f"{caster_name}:steel{i}", shape, f"{kind} caster: {STEEL_NAMES[i].lower()}", PLACEHOLDER, "steel", "caster")
    add(f"{caster_name}:tire", tire, f"{kind} caster: wheel", f"2 in wheel · {PLACEHOLDER.lower()}", "tire", "caster")
    for i, shape in enumerate(bolts):
        add(f"{caster_name}:bolt{i}", shape, "Caster screw", "#10 × ⅝ in, assumed size · 4 per wheel", "bolt", "hardware")

template = (HERE / "viewer_template.html").read_text()
page = template.replace("/*__MODEL__*/", json.dumps({"parts": parts}, separators=(",", ":")))
OUTPUT.parent.mkdir(exist_ok=True)
OUTPUT.write_text(page)
print(f"{len(parts)} parts, {OUTPUT.stat().st_size / 1e6:.2f} MB -> {OUTPUT}")
