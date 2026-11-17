"""One soldering tool tote, from "Plans for tool totes.pdf".

Parameters are in inches, as in the plan; geometry is built in mm.
Axes: X = tote length, Y = tote depth, Z = height (0 at the underside of the base).
Owner decisions: round dowel handle in blind Forstner holes, replacing the plan's
0.75 x 1 handle and rectangular pockets; keep the corner cleats.
"""
from build123d import *

IN = 25.4

# --- Plan parameters (in): worked example from page 2 ---
L, D, H_TOTAL = 12.5, 8.0, 9.0  # overall envelope
t = 0.703  # base and end plywood, measured
s = 0.25  # wall and divider plywood
a = 0.125  # base overhang past the ends and walls
r = 0.25  # handle pocket depth
WALL_H = 3.0
DIVIDER_H = 2.75
SHOULDER_V = 3.25  # straight lower sides of the end panel
TOP_FLAT = 3.0  # flat top width of the end panel, centred
HANDLE_D = 1.0  # round dowel, seated in holes from a matching 1 in Forstner bit
POCKET_V_CENTER = 7.875 - t
SHORT_DIVIDER_CENTER = 7.0  # from the left inside end face (plan's starting layout)
CLEAT_H, CLEAT_ALONG, CLEAT_INTO = 2.5, 0.5, 1.125
OUTLINE_RADIUS = 0.125  # ASSUMED: plan says round the outline corners, with no size

# --- Screws: #8 x 1-1/4 ---
SCREW_L, SCREW_D, SCREW_HEAD_D, SCREW_HEAD_H = 1.25, 0.164, 0.32, 0.1

# --- Derived, using the plan's formulas ---
E = D - 2 * a  # end width
H = H_TOTAL - t  # end height
I = L - 2 * a - 2 * t  # clear length between the ends
J = E - 2 * s  # inside depth between the walls
BAY = (J - s) / 2
HANDLE_L = I + 2 * r
end_x_l = (a, a + t)  # left end, outer face to inner face
end_x_r = (L - a - t, L - a)
x_in_l, x_in_r = end_x_l[1], end_x_r[0]
y_front, y_rear = a, D - a  # outer faces of the walls and edges of the ends
y_wall_in_f, y_wall_in_r = y_front + s, y_rear - s
y_center = D / 2
handle_z = t + POCKET_V_CENTER


def box(x0, x1, y0, y1, z0, z1):
    return Box(
        (x1 - x0) * IN, (y1 - y0) * IN, (z1 - z0) * IN, align=(Align.MIN, Align.MIN, Align.MIN)
    ).move(Location((x0 * IN, y0 * IN, z0 * IN)))


def overlaps(p, q):
    a_box, b_box = p.bounding_box(), q.bounding_box()
    return (a_box.min.X < b_box.max.X and b_box.min.X < a_box.max.X
            and a_box.min.Y < b_box.max.Y and b_box.min.Y < a_box.max.Y
            and a_box.min.Z < b_box.max.Z and b_box.min.Z < a_box.max.Z)


def cut_all(part, tools):
    for tool in tools:
        if overlaps(part, tool):
            part = part - tool
    return part


def cylinder_x(diameter, x0, x1):
    """Cylinder along X at the handle's center line, from x0 to x1 (in)."""
    return Cylinder(diameter / 2 * IN, (x1 - x0) * IN).move(
        Location(((x0 + x1) / 2 * IN, y_center * IN, handle_z * IN), (0, 90, 0))
    )


def end_panel(x0, x1, pocket_x0, pocket_x1):
    half = TOP_FLAT / 2
    outline = [
        (0, 0), (E, 0), (E, SHOULDER_V), (E / 2 + half, H), (E / 2 - half, H), (0, SHOULDER_V),
    ]
    with BuildSketch(Plane.YZ) as sketch:
        Polygon(*[(u * IN, v * IN) for u, v in outline], align=None)
        fillet(
            [v for v in sketch.vertices() if v.Y > 0.1 * IN or v.Z > 0.1 * IN],
            radius=OUTLINE_RADIUS * IN,
        )
    solid = extrude(sketch.sketch, amount=(x1 - x0) * IN)
    box_now = solid.bounding_box()
    solid = solid.move(Location((x0 * IN - box_now.min.X, y_front * IN - box_now.min.Y, t * IN - box_now.min.Z)))
    return solid - cylinder_x(HANDLE_D, pocket_x0, pocket_x1)


wood = {}
wood["base"] = box(0, L, 0, D, 0, t)
wood["end_left"] = end_panel(*end_x_l, x_in_l - r, x_in_l)
wood["end_right"] = end_panel(*end_x_r, x_in_r, x_in_r + r)
wood["wall_front"] = box(x_in_l, x_in_r, y_front, y_wall_in_f, t, t + WALL_H)
wood["wall_rear"] = box(x_in_l, x_in_r, y_wall_in_r, y_rear, t, t + WALL_H)
wood["divider_center"] = box(x_in_l, x_in_r, y_center - s / 2, y_center + s / 2, t, t + DIVIDER_H)
short_x = x_in_l + SHORT_DIVIDER_CENTER
wood["divider_short_front"] = box(
    short_x - s / 2, short_x + s / 2, y_wall_in_f, y_center - s / 2, t, t + DIVIDER_H
)
wood["divider_short_rear"] = box(
    short_x - s / 2, short_x + s / 2, y_center + s / 2, y_wall_in_r, t, t + DIVIDER_H
)

wood["handle"] = cylinder_x(HANDLE_D, x_in_l - r, x_in_r + r)

cleat_spots = {
    "front_left": (x_in_l, x_in_l + CLEAT_ALONG, y_wall_in_f, y_wall_in_f + CLEAT_INTO),
    "front_right": (x_in_r - CLEAT_ALONG, x_in_r, y_wall_in_f, y_wall_in_f + CLEAT_INTO),
    "rear_left": (x_in_l, x_in_l + CLEAT_ALONG, y_wall_in_r - CLEAT_INTO, y_wall_in_r),
    "rear_right": (x_in_r - CLEAT_ALONG, x_in_r, y_wall_in_r - CLEAT_INTO, y_wall_in_r),
}
for name, (x0, x1, y0, y1) in cleat_spots.items():
    wood[f"cleat_{name}"] = box(x0, x1, y0, y1, t, t + CLEAT_H)

# --- Wood screws (12, per the plan's allocation) ---
screw_blank = Part() + [
    Cylinder(SCREW_D / 2 * IN, SCREW_L * IN, align=(Align.CENTER, Align.CENTER, Align.MIN)),
    Cone(SCREW_HEAD_D / 2 * IN, SCREW_D / 2 * IN, SCREW_HEAD_H * IN, align=(Align.CENTER, Align.CENTER, Align.MIN)),
]


def screw(x, y, z, direction):
    """Head flush at (x, y, z) (in), driven along direction."""
    return Plane(origin=(x * IN, y * IN, z * IN), z_dir=direction).location * screw_blank


screws = {}
wall_screw_z = t + CLEAT_H / 2
for name, (x0, x1, y0, y1) in cleat_spots.items():
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    screws[f"base_cleat_{name}"] = screw(cx, cy, 0, (0, 0, 1))
    if name.startswith("front"):
        screws[f"wall_{name}"] = screw(cx, y_front, wall_screw_z, (0, 1, 0))
    else:
        screws[f"wall_{name}"] = screw(cx, y_rear, wall_screw_z, (0, -1, 0))
screws["base_end_left"] = screw(sum(end_x_l) / 2, y_center, 0, (0, 0, 1))
screws["base_end_right"] = screw(sum(end_x_r) / 2, y_center, 0, (0, 0, 1))
screws["handle_left"] = screw(end_x_l[0], y_center, handle_z, (1, 0, 0))
screws["handle_right"] = screw(end_x_r[1], y_center, handle_z, (-1, 0, 0))

for name in list(wood):
    wood[name] = cut_all(wood[name], screws.values())

for name, part in wood.items():
    show(part, name)
for name, part in screws.items():
    show(part, f"screw_{name}")

result = Compound(label="tote", children=list(wood.values()) + list(screws.values()))
