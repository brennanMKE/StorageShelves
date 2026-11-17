"""Third model: the four shelf units under the two workbench tables, with the two totes.

Reuses shelf_unit.py, workbench_tables.py and tote.py unchanged. Dimensions are in inches.
Each table's two shelves sit side by side with their backs toward the center of the
pair, with equal gaps between the legs and shelves. Table B's shelves are turned 180 degrees.
"""
import copy
import runpy
from pathlib import Path

from build123d import Compound, Location

HERE = Path(__file__).resolve().parent
IN = 25.4


def noop(*args, **kwargs):
    return None


shelf_ns = runpy.run_path(str(HERE / "shelf_unit.py"), init_globals={"show": noop})
table_ns = runpy.run_path(str(HERE / "workbench_tables.py"), init_globals={"show": noop})

SHELF_W, SHELF_D, SHELF_H = shelf_ns["W"], shelf_ns["D"], shelf_ns["H"]
TABLE_D = table_ns["TABLE_D"]
TABLE_B_Y0 = table_ns["table_b_y0"]
LEG_X_INNER = table_ns["OVERHANG_X"] + table_ns["LEG"]
OPEN_W = table_ns["BASE_W"] - 2 * table_ns["LEG"]  # clear width between legs
SHELF_GAP = (OPEN_W - 2 * SHELF_W) / 3  # equal gaps: leg-shelf, shelf-shelf, shelf-leg
SHELF_X = (LEG_X_INNER + SHELF_GAP, LEG_X_INNER + 2 * SHELF_GAP + SHELF_W)

PLACEMENTS = []
for label, x in zip(("A1", "A2"), SHELF_X):
    PLACEMENTS.append({"label": label, "x": x, "y": TABLE_D - SHELF_D, "rot": 0})
for label, x in zip(("B1", "B2"), SHELF_X):
    PLACEMENTS.append({"label": label, "x": x + SHELF_W, "y": TABLE_B_Y0 + SHELF_D, "rot": 180})


def unit_shapes():
    shapes = dict(shelf_ns["wood"])
    shapes.update({f"screw_{name}": shape for name, shape in shelf_ns["screws"].items()})
    for name, (steel, tire, screws) in shelf_ns["casters"].items():
        shapes.update({f"{name}_steel{i}": shape for i, shape in enumerate(steel)})
        shapes[f"{name}_tire"] = tire
        shapes.update({f"{name}_screw{i}": shape for i, shape in enumerate(screws)})
    return shapes


UNIT = unit_shapes()
shelf_parts = {}  # "shelf_A1_base" -> shape, placed
for place in PLACEMENTS:
    location = Location((place["x"] * IN, place["y"] * IN, 0), (0, 0, place["rot"]))
    for name, shape in UNIT.items():
        placed = copy.deepcopy(shape).moved(location)
        shelf_parts[f"shelf_{place['label']}_{name}"] = placed

table_parts = {name: record[0] for name, record in table_ns["parts"].items()}

# --- Two totes side by side on the lower shelf of unit A1 (owner's choice) ---
tote_ns = runpy.run_path(str(HERE / "tote.py"), init_globals={"show": noop})
TOTE_UNIT = {**tote_ns["wood"], **{f"screw_{n}": s for n, s in tote_ns["screws"].items()}}
TOTE_L = tote_ns["L"]
TOTE_FRONT_GAP = 1.0  # ASSUMED: behind the shelf's front edge, for easy reach
A1 = PLACEMENTS[0]
SHELF_IN_L = shelf_ns["x_in_l"]
TOTE_GAP = (shelf_ns["I"] - 2 * TOTE_L) / 3  # equal gaps: side, between totes, side
TOTE_PLACEMENTS = [
    {
        "label": str(i + 1),
        "x": A1["x"] + SHELF_IN_L + TOTE_GAP + i * (TOTE_L + TOTE_GAP),
        "y": A1["y"] + shelf_ns["y_front"] + TOTE_FRONT_GAP,
        "z": shelf_ns["shelf_low"],
    }
    for i in range(2)
]
tote_parts = {}  # "tote_1_base" -> shape, placed
for place in TOTE_PLACEMENTS:
    location = Location((place["x"] * IN, place["y"] * IN, place["z"] * IN))
    for name, shape in TOTE_UNIT.items():
        tote_parts[f"tote_{place['label']}_{name}"] = copy.deepcopy(shape).moved(location)

result = Compound(
    label="workbench_layout",
    children=list(table_parts.values()) + list(shelf_parts.values()) + list(tote_parts.values()),
)
