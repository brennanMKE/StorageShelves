"""Two separate 72 x 30 workbench tables placed back to back, each with its own outlet panel.

Parameters are in inches; geometry is built in mm.
Axes: X = width, Y = depth (table A 0-30, table B 30-60, seam at 30), Z = height.

GIVEN by the owner: top size and height, bottom of the bar, base size, panel height and depth.
ESTIMATED from one photo, needing a tape measure: everything marked ESTIMATE.
"""
from build123d import *

IN = 25.4

# --- Given dimensions ---
TABLE_W = 72.0
TABLE_D = 30.0
TOP_Z = 36.0
BAR_BOTTOM_Z = 32.0
BASE_W = 70.0  # white metal base
BASE_D = 25.0
PANEL_H, PANEL_D = 2.75, 1.75  # one outlet panel per table
TABLE_GAP = 0.0  # separate tables; the gap between them has not been measured

# --- ESTIMATES from the photo ---
TOP_T = 1.25  # top thickness
LEG = 2.5  # square leg
BAR_T = 1.0  # frame bar thickness
CASTER_H = 3.0  # floor to underside of leg
WHEEL_D, WHEEL_W = 2.5, 1.0
OUTLET_W, OUTLET_H, OUTLET_T = 4.5, 2.25, 0.1  # plate, as laid out in the photo
OUTLET_X = (TABLE_W / 4, 3 * TABLE_W / 4)  # two per side; the positions are a guess

# --- Derived ---
UNDER_TOP_Z = TOP_Z - TOP_T
OVERHANG_X = (TABLE_W - BASE_W) / 2
OVERHANG_Y = (TABLE_D - BASE_D) / 2  # ASSUMED: base centred front to back under the top


def box(x0, x1, y0, y1, z0, z1):
    return Box(
        (x1 - x0) * IN, (y1 - y0) * IN, (z1 - z0) * IN, align=(Align.MIN, Align.MIN, Align.MIN)
    ).move(Location((x0 * IN, y0 * IN, z0 * IN)))


def caster_parts(cx, cy):
    r = WHEEL_D / 2
    wheel = Cylinder(r * IN, WHEEL_W * IN).move(Location((cx * IN, cy * IN, r * IN), (90, 0, 0)))
    housing = Cylinder(0.8 * IN, 0.28 * IN, align=(Align.CENTER, Align.CENTER, Align.MIN)).move(
        Location((cx * IN, cy * IN, (CASTER_H - 0.28) * IN))
    )
    half = WHEEL_W / 2
    cheek_a = box(cx - 0.35, cx + 0.35, cy + half + 0.04, cy + half + 0.14, r - 0.3, CASTER_H - 0.28)
    cheek_b = box(cx - 0.35, cx + 0.35, cy - half - 0.14, cy - half - 0.04, r - 0.3, CASTER_H - 0.28)
    return wheel, [housing, cheek_a, cheek_b]


parts = {}  # name -> (shape, title, detail, color, group)
EST = "Estimated from the photo"


def add(name, shape, title, detail, color, group):
    parts[name] = (shape, title, detail, color, group)


def build_table(label, y0):
    group = f"table_{label.lower()}"
    prefix = f"{group}_"
    add(prefix + "top", box(0, TABLE_W, y0, y0 + TABLE_D, UNDER_TOP_Z, TOP_Z), "Table top",
        f"72 × 30 in, top surface at 36 in · {TOP_T} in thick is estimated", "#55585b", group)
    x0, x1 = OVERHANG_X, TABLE_W - OVERHANG_X
    y_a, y_b = y0 + OVERHANG_Y, y0 + TABLE_D - OVERHANG_Y
    leg_spots = {
        "left_near": (x0, y_a), "right_near": (x1 - LEG, y_a),
        "left_far": (x0, y_b - LEG), "right_far": (x1 - LEG, y_b - LEG),
    }
    for spot, (lx, ly) in leg_spots.items():
        add(f"{prefix}leg_{spot}", box(lx, lx + LEG, ly, ly + LEG, CASTER_H, UNDER_TOP_Z),
            "Leg", f"{LEG} in square · {EST.lower()}", "#e7e9e6", group)
        wheel, steel = caster_parts(lx + LEG / 2, ly + LEG / 2)
        add(f"{prefix}caster_{spot}_wheel", wheel, "Caster wheel", EST, "#26282a", group)
        for i, piece in enumerate(steel):
            add(f"{prefix}caster_{spot}_steel{i}", piece, "Caster", EST, "#a9aeb2", group)
    bar_x0, bar_x1 = x0 + LEG, x1 - LEG
    add(prefix + "bar_near", box(bar_x0, bar_x1, y_a, y_a + BAR_T, BAR_BOTTOM_Z, UNDER_TOP_Z),
        "Long frame bar", f"Bottom edge at {BAR_BOTTOM_Z:g} in · thickness estimated", "#e7e9e6", group)
    add(prefix + "bar_far", box(bar_x0, bar_x1, y_b - BAR_T, y_b, BAR_BOTTOM_Z, UNDER_TOP_Z),
        "Long frame bar", f"Bottom edge at {BAR_BOTTOM_Z:g} in · thickness estimated", "#e7e9e6", group)
    end_y0, end_y1 = y_a + LEG, y_b - LEG
    add(prefix + "bar_left", box(x0, x0 + BAR_T, end_y0, end_y1, BAR_BOTTOM_Z, UNDER_TOP_Z),
        "End frame bar", f"Bottom edge at {BAR_BOTTOM_Z:g} in · {EST.lower()}", "#e7e9e6", group)
    add(prefix + "bar_right", box(x1 - BAR_T, x1, end_y0, end_y1, BAR_BOTTOM_Z, UNDER_TOP_Z),
        "End frame bar", f"Bottom edge at {BAR_BOTTOM_Z:g} in · {EST.lower()}", "#e7e9e6", group)


def build_panel(label, rear_y, toward):
    """One outlet panel on a table's rear edge. toward = -1 or +1: the Y direction it faces."""
    group = f"table_{label.lower()}"
    front_y = rear_y + toward * PANEL_D
    y0, y1 = sorted((rear_y, front_y))
    add(f"{group}_panel", box(0, TABLE_W, y0, y1, TOP_Z, TOP_Z + PANEL_H), "Outlet panel",
        f"{PANEL_H:g} in high × {PANEL_D:g} in deep · 72 in length is estimated", "#f1f2ee", group)
    plate_z0 = TOP_Z + (PANEL_H - OUTLET_H) / 2
    py0, py1 = sorted((front_y, front_y + toward * OUTLET_T))
    for i, ox in enumerate(OUTLET_X):
        add(f"{group}_outlet_{i}",
            box(ox - OUTLET_W / 2, ox + OUTLET_W / 2, py0, py1, plate_z0, plate_z0 + OUTLET_H),
            "Outlet plate", "Count and position are guesses", "#fbfbf8", group)


table_b_y0 = TABLE_D + TABLE_GAP
build_table("A", 0.0)
build_table("B", table_b_y0)
build_panel("A", TABLE_D, -1)
build_panel("B", table_b_y0, 1)

for name, record in parts.items():
    show(record[0], name)

result = Compound(label="workbench_tables", children=[record[0] for record in parts.values()])
