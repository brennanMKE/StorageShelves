"""Verifies workbench_layout.py, then writes its STEP file and viewer page to output/.

The viewer reuses the geometry already in shelf_viewer.html and workbench_tables_viewer.html,
and tote_viewer.html, so run build_viewer.py, build_tables.py and build_tote.py first if a model has changed.
"""
import json
import re
import runpy
from pathlib import Path

from build123d import Compound, export_step, import_step

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "output"
IN = 25.4

ns = runpy.run_path(str(HERE / "workbench_layout.py"))
shelves, tables, result = ns["shelf_parts"], ns["table_parts"], ns["result"]
print("solids:", len(result.solids()), "shelf solids:", len(shelves), "table solids:", len(tables))
print("invalid:", [n for n, s in {**shelves, **tables}.items() if not s.is_valid])
box = result.bounding_box()
print("bbox in:", [round(v / IN, 3) for v in (box.size.X, box.size.Y, box.size.Z)])


def bbox_overlap(a, b):
    return (a.min.X < b.max.X and b.min.X < a.max.X and a.min.Y < b.max.Y
            and b.min.Y < a.max.Y and a.min.Z < b.max.Z and b.min.Z < a.max.Z)


boxes = {name: shape.bounding_box() for name, shape in {**shelves, **tables}.items()}
names = list(shelves)
candidates = 0
overlaps = []
for name in names:
    unit = name.split("_")[1]
    for other, shape in tables.items():
        if bbox_overlap(boxes[name], boxes[other]):
            candidates += 1
            common = shelves[name] & shape
            volume = sum(s.volume for s in common.solids()) if common is not None else 0
            if volume > 0.01:
                overlaps.append((name, other, round(volume, 2)))
    for other in names:
        if other > name and other.split("_")[1] != unit and bbox_overlap(boxes[name], boxes[other]):
            candidates += 1
            common = shelves[name] & shelves[other]
            volume = sum(s.volume for s in common.solids()) if common is not None else 0
            if volume > 0.01:
                overlaps.append((name, other, round(volume, 2)))
print("bbox candidates:", candidates, "overlaps:", overlaps)

totes = ns["tote_parts"]
print("tote solids:", len(totes), "invalid:", [n for n, s in totes.items() if not s.is_valid])
tote_boxes = {name: shape.bounding_box() for name, shape in totes.items()}
tote_overlaps = []
tote_candidates = 0
others = {**shelves, **tables}
for name, shape in totes.items():
    tote = name.split("_")[1]
    for other, other_shape in others.items():
        if bbox_overlap(tote_boxes[name], boxes[other]):
            tote_candidates += 1
            common = shape & other_shape
            volume = sum(s.volume for s in common.solids()) if common is not None else 0
            if volume > 0.01:
                tote_overlaps.append((name, other, round(volume, 2)))
    for other, other_shape in totes.items():
        if other > name and other.split("_")[1] != tote and bbox_overlap(tote_boxes[name], tote_boxes[other]):
            tote_candidates += 1
            common = shape & other_shape
            volume = sum(s.volume for s in common.solids()) if common is not None else 0
            if volume > 0.01:
                tote_overlaps.append((name, other, round(volume, 2)))
print("tote bbox candidates:", tote_candidates, "tote overlaps:", tote_overlaps)


def unit_box(label):
    selected = [boxes[n] for n in names if n.split("_")[1] == label]
    return (min(b.min.X for b in selected) / IN, max(b.max.X for b in selected) / IN,
            min(b.min.Y for b in selected) / IN, max(b.max.Y for b in selected) / IN,
            min(b.min.Z for b in selected) / IN, max(b.max.Z for b in selected) / IN)


units = {label: unit_box(label) for label in ("A1", "A2", "B1", "B2")}
for label, values in units.items():
    print(label, "x/y/z in:", [round(v, 3) for v in values])
bar_low = min(boxes[n].min.Z for n in tables if "_bar_" in n) / IN
under_top = min(boxes[n].min.Z for n in tables if n.endswith("_top")) / IN
print("clearance to bar in:", round(bar_low - units["A1"][5], 3), "to underside of top in:", round(under_top - units["A1"][5], 3))
leg_right = boxes["table_a_leg_left_far"].max.X / IN
leg_left = boxes["table_a_leg_right_far"].min.X / IN
print("gaps along width in:", round(units["A1"][0] - leg_right, 3), round(units["A2"][0] - units["A1"][1], 3), round(leg_left - units["A2"][1], 3))
print("knee depth, table A front edge to shelf front in:", round(units["A1"][2] - boxes["table_a_top"].min.Y / IN, 3))
print("knee depth, table B front edge to shelf front in:", round(boxes["table_b_top"].max.Y / IN - units["B1"][3], 3))
print("shelves back to back gap in:", round(units["B1"][2] - units["A1"][3], 3))


def group_box(prefix):
    selected = [tote_boxes[n] for n in totes if n.startswith(prefix)]
    return (min(b.min.X for b in selected) / IN, max(b.max.X for b in selected) / IN,
            min(b.min.Y for b in selected) / IN, max(b.max.Y for b in selected) / IN,
            min(b.min.Z for b in selected) / IN, max(b.max.Z for b in selected) / IN)


tote_1, tote_2 = group_box("tote_1_"), group_box("tote_2_")
print("tote 1 x/y/z in:", [round(v, 3) for v in tote_1])
print("tote 2 x/y/z in:", [round(v, 3) for v in tote_2])
side_l = boxes["shelf_A1_side_left"].max.X / IN
side_r = boxes["shelf_A1_side_right"].min.X / IN
print("tote width gaps in:", round(tote_1[0] - side_l, 3), round(tote_2[0] - tote_1[1], 3), round(side_r - tote_2[1], 3))
print("tote bottom vs lower shelf surface in:", round(tote_1[4] - boxes["shelf_A1_base"].max.Z / IN, 3))
cleat_low = boxes["shelf_A1_cleat_left"].min.Z / IN
deck_low = boxes["shelf_A1_upper_shelf"].min.Z / IN
print("tote top to cleat in:", round(cleat_low - tote_1[5], 3), "to upper shelf in:", round(deck_low - tote_1[5], 3))
print("nosing rise above shelf in:", round(boxes["shelf_A1_nosing_lower"].max.Z / IN - boxes["shelf_A1_base"].max.Z / IN, 3))
print("tote front to shelf front edge in:", round(tote_1[2] - boxes["shelf_A1_base"].min.Y / IN, 3),
      "tote rear to bottom rail in:", round(boxes["shelf_A1_rail_bottom"].min.Y / IN - tote_1[3], 3))

OUT.mkdir(exist_ok=True)
children = []
for name, shape in {**tables, **shelves, **totes}.items():
    solid = shape.solids()[0]
    solid.label = name
    children.append(solid)
step_path = OUT / "workbench_layout.step"
export_step(Compound(label="workbench_layout", children=children), str(step_path))
back = import_step(str(step_path))
labels = [c.label for c in back.children] if back.children else []
print("step solids:", len(back.solids()), "volume diff mm3:", round(back.volume - result.volume, 4),
      "named:", len(labels), "unique:", len(set(labels)))


def model_data(path):
    match = re.search(r'id="model-data">(.*?)</script>', path.read_text(), re.S)
    return json.loads(match.group(1))["parts"]


data = {
    "tables": model_data(OUT / "workbench_tables_viewer.html"),
    "unit": model_data(OUT / "shelf_viewer.html"),
    "placements": ns["PLACEMENTS"],
    "tote": model_data(OUT / "tote_viewer.html"),
    "tote_placements": ns["TOTE_PLACEMENTS"],
}
template = (HERE / "layout_viewer_template.html").read_text()
page_path = OUT / "workbench_layout_viewer.html"
page_path.write_text(template.replace("/*__MODEL__*/", json.dumps(data, separators=(",", ":"))))
print(round(page_path.stat().st_size / 1e6, 2), "MB")
