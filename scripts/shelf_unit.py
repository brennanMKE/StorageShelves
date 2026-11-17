"""One electronics workbench shelf unit, from "Plans for shelves.pdf".

Parameters are in inches, as in the plan; geometry is built in mm.
Axes: X = width (left to right, facing the front), Y = depth (0 at the front of
the nosing, increasing to the rear), Z = height (0 at the floor).
"""
from build123d import *

IN = 25.4

# --- Plan parameters (in): worked example from page 3 ---
W, D, H = 30.0, 15.0, 29.5  # overall envelope
t = 0.703  # side/deck plywood, measured
b = 0.25  # back plywood
n = 0.75  # finished nosing thickness
p = 1.25  # finished post size
h = 2.6  # caster mounting height
UPPER_SURFACE = 18.0  # upper shelf surface above the floor
SIDE_INSET = 0.25  # side outer face inboard of the base edge
HOUSING = 0.125  # rail penetration into each post
TOP_RAIL_DEEP, TOP_RAIL_HIGH = 0.75, 1.5  # 1x2 pine
NOSE_RISE = 0.5  # nosing above the shelf surface
NOSE_HIGH = 1.4375  # midpoint of the plan's 1.375-1.5 range
NOSE_ROUND = 0.2  # routed edge radius (assumed; plan says "round")

# --- Screws: #8 x 1-1/4 ---
SCREW_L, SCREW_D, SCREW_HEAD_D, SCREW_HEAD_H = 1.25, 0.164, 0.32, 0.1

# --- PLACEHOLDER caster hardware: not specified in the plan; confirm on the real part ---
WHEEL_D, WHEEL_W = 2.0, 0.75
PLATE_X, PLATE_Y, PLATE_T = 2.5, 1.75, 0.1
BOLT_X, BOLT_Y = 1.875, 1.25  # plate hole spacing
# Casters screw up into the base from below, with nothing showing on top. Owner
# decision replacing the plan's through-bolts. The screw size is assumed: #10 x 5/8.
CASTER_SCREW_L, CASTER_SCREW_D = 0.625, 0.19  # length below the head, shank
CASTER_SCREW_HEAD_D, CASTER_SCREW_HEAD_H = 0.37, 0.12
SWIVEL_OFFSET = 0.6
# Caster plate centres. Caster pads are removed by owner decision; positions are
# where the plan's pads centred them.
CASTER_INSET_X = 1.75  # from the interior face of each side
CASTER_FRONT_Y = 3.0  # behind the front edge of the base
CASTER_REAR_Y = 1.625  # in front of the front faces of the posts

# --- Derived, using the plan's formulas ---
I = W - 2 * SIDE_INSET - 2 * t  # interior width
d = D - n - b  # side/deck depth
L = H - h - t  # side/post/back height
shelf_low = h + t  # lower shelf surface
ledger_top = UPPER_SURFACE - t
y_front = n  # front edge of base, sides and deck
y_rear = D - b  # rear face of sides and posts
x_in_l, x_in_r = SIDE_INSET + t, W - SIDE_INSET - t  # interior faces of the sides
post_face_l, post_face_r = x_in_l + p, x_in_r - p
rail_x0, rail_x1 = post_face_l - HOUSING, post_face_r + HOUSING


def box(x0, x1, y0, y1, z0, z1):
    return Box(
        (x1 - x0) * IN, (y1 - y0) * IN, (z1 - z0) * IN, align=(Align.MIN, Align.MIN, Align.MIN)
    ).move(Location((x0 * IN, y0 * IN, z0 * IN)))


def mirror_x(x0, x1):
    return W - x1, W - x0


def cylinder_y(radius, width, x=0.0, z=0.0, y=0.0):
    """Cylinder with its axis along Y, centred at (x, y, z)."""
    return Cylinder(radius * IN, width * IN).move(
        Location((x * IN, y * IN, z * IN), (90, 0, 0))
    )


def prism_xz(points, y0, y1):
    """Extrude an XZ polygon (in) from y0 to y1."""
    profile = Plane.XZ * Polygon(*[(u * IN, v * IN) for u, v in points], align=None)
    # Extrude direction follows polygon winding, so place it by its actual extent.
    solid = extrude(profile, amount=(y1 - y0) * IN)
    return solid.move(Location((0, y0 * IN - solid.bounding_box().min.Y, 0)))


def overlaps(a, b_shape):
    ba, bb = a.bounding_box(), b_shape.bounding_box()
    return (
        ba.min.X < bb.max.X and bb.min.X < ba.max.X
        and ba.min.Y < bb.max.Y and bb.min.Y < ba.max.Y
        and ba.min.Z < bb.max.Z and bb.min.Z < ba.max.Z
    )


def cut_all(part, tools):
    for tool in tools:
        if overlaps(part, tool):
            part = part - tool
    return part


# --- Wood parts -------------------------------------------------------------
wood = {}
wood["base"] = box(0, W, y_front, D, h, h + t)
wood["side_left"] = box(SIDE_INSET, x_in_l, y_front, y_rear, shelf_low, H)
wood["side_right"] = box(x_in_r, W - SIDE_INSET, y_front, y_rear, shelf_low, H)
wood["back"] = box(SIDE_INSET, W - SIDE_INSET, y_rear, D, shelf_low, H)

post_y0 = y_rear - p
wood["post_left"] = box(x_in_l, post_face_l, post_y0, y_rear, shelf_low, H)
wood["post_right"] = box(post_face_r, x_in_r, post_y0, y_rear, shelf_low, H)
wood["rail_bottom"] = box(rail_x0, rail_x1, post_y0, y_rear, shelf_low, shelf_low + p)
wood["ledger"] = box(rail_x0, rail_x1, post_y0, y_rear, ledger_top - p, ledger_top)
wood["rail_top"] = box(
    rail_x0, rail_x1, y_rear - TOP_RAIL_DEEP, y_rear, H - TOP_RAIL_HIGH, H
)
for name in ("post_left", "post_right"):
    wood[name] = cut_all(
        wood[name], [wood["rail_bottom"], wood["ledger"], wood["rail_top"]]
    )

wood["cleat_left"] = box(x_in_l, post_face_l, y_front, post_y0, ledger_top - p, ledger_top)
wood["cleat_right"] = box(post_face_r, x_in_r, y_front, post_y0, ledger_top - p, ledger_top)

wood["upper_shelf"] = (
    box(x_in_l, x_in_r, y_front, y_rear, ledger_top, UPPER_SURFACE)
    - box(x_in_l - 1, post_face_l, post_y0, y_rear + 1, ledger_top - 1, UPPER_SURFACE + 1)
    - box(post_face_r, x_in_r + 1, post_y0, y_rear + 1, ledger_top - 1, UPPER_SURFACE + 1)
)


def nosing(surface_z):
    z1 = surface_z + NOSE_RISE
    z0 = z1 - NOSE_HIGH
    blank = box(x_in_l, x_in_r, 0, n, z0, z1)
    wanted = [(0, z1), (0, z0), (n, z1)]  # exposed long edges: (y, z) in inches
    edges = [
        e
        for e in blank.edges().filter_by(Axis.X)
        if any(
            abs(e.center().Y - y * IN) < 0.01 and abs(e.center().Z - z * IN) < 0.01
            for y, z in wanted
        )
    ]
    return fillet(edges, radius=NOSE_ROUND * IN)


wood["nosing_lower"] = nosing(shelf_low)
wood["nosing_upper"] = nosing(UPPER_SURFACE)

# --- Laser-engraved logo on the outer face of each side (owner request) ---------
# Tree mark only, no text, from assets/sf-logo-mark.svg. Centred front to back on
# the side, and centred between the upper shelf surface and the top edge.
from pathlib import Path

_ROOT = (
    Path(__file__).resolve().parent.parent if "__file__" in globals() else Path.cwd()
)
LOGO_SVG = _ROOT / "assets" / "sf-logo-mark.svg"
LOGO_H = 4.0  # in; fits the xTool F1's 115 mm (4.5 in) field, so either laser works
LOGO_DEPTH = 0.008  # in (about 0.2 mm); shallow, to stay inside the maple face veneer
LOGO_Y = (y_front + y_rear) / 2
LOGO_Z = (UPPER_SURFACE + H) / 2


def logo_faces():
    """The mark's filled faces, LOGO_H tall, centred on the origin in XY (mm)."""
    # fix(): two of the SVG paths import as faces OCCT flags invalid until repaired.
    faces = [s.fix() for s in import_svg(str(LOGO_SVG)) if isinstance(s, Face)]
    bb = Compound(faces).bounding_box()
    k = LOGO_H * IN / bb.size.Y
    c = bb.center()
    return [f.moved(Location((-c.X, -c.Y, 0))).scale(k) for f in faces]


def engraving(x_face, outward):
    """Logo recess on a side's outer face, reading correctly from outside."""
    plane = Plane(
        origin=(x_face * IN, LOGO_Y * IN, LOGO_Z * IN),
        x_dir=(0, outward, 0),  # the viewer's right, standing outside the side
        z_dir=(outward, 0, 0),
    )
    cuts = [
        extrude(plane.location * f, amount=LOGO_DEPTH * IN, dir=(-outward, 0, 0))
        for f in logo_faces()
    ]
    return Part() + cuts


wood["logo_left"] = engraving(SIDE_INSET, -1)
wood["logo_right"] = engraving(W - SIDE_INSET, 1)
wood["side_left"] = wood["side_left"] - wood["logo_left"]
wood["side_right"] = wood["side_right"] - wood["logo_right"]

# --- Wood screws (18, per the plan's schedule) --------------------------------
screw_blank = Part() + [
    Cylinder(SCREW_D / 2 * IN, SCREW_L * IN, align=(Align.CENTER, Align.CENTER, Align.MIN)),
    Cone(
        SCREW_HEAD_D / 2 * IN,
        SCREW_D / 2 * IN,
        SCREW_HEAD_H * IN,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    ),
]


def screw(x, y, z, direction):
    """Head flush at (x, y, z) (in), driven along direction."""
    plane = Plane(origin=(x * IN, y * IN, z * IN), z_dir=direction)
    return plane.location * screw_blank


screws = {}
post_cy = post_y0 + p / 2
cleat_z = ledger_top - p / 2
for side, x_face, drive, post_x in (
    ("left", SIDE_INSET, (1, 0, 0), x_in_l + p / 2),
    ("right", W - SIDE_INSET, (-1, 0, 0), x_in_r - p / 2),
):
    # Sides into posts, staggered clear of the back screws, pads and cleats.
    screws[f"side_post_{side}_low"] = screw(x_face, post_cy, 10.0, drive)
    screws[f"side_post_{side}_high"] = screw(x_face, post_cy, 23.0, drive)
    # Sides into cleats.
    screws[f"side_cleat_{side}_front"] = screw(x_face, y_front + 3.0, cleat_z, drive)
    screws[f"side_cleat_{side}_rear"] = screw(x_face, post_y0 - 3.0, cleat_z, drive)
    # Back into posts.
    screws[f"back_post_{side}_low"] = screw(post_x, D, shelf_low + p / 2, (0, -1, 0))
    screws[f"back_post_{side}_high"] = screw(post_x, D, H - TOP_RAIL_HIGH / 2, (0, -1, 0))
# Back into rails.
screws["back_rail_bottom"] = screw(W / 2, D, shelf_low + p / 2, (0, -1, 0))
screws["back_rail_top"] = screw(W / 2, D, H - TOP_RAIL_HIGH / 2, (0, -1, 0))
# Nosing into the shelf edge, centred on the deck thickness.
for shelf, deck_z in (("lower", h + t / 2), ("upper", UPPER_SURFACE - t / 2)):
    for label, frac in (("a", 0.25), ("b", 0.75)):
        screws[f"nosing_{shelf}_{label}"] = screw(x_in_l + frac * I, 0, deck_z, (0, 1, 0))


# --- Casters and through-bolts (dimensions are placeholders) ------------------
def caster(cx, cy, swivel):
    """Returns (steel, rubber, bolts) solids, with the plate top at z = h."""
    axle_x = SWIVEL_OFFSET if swivel else 0.0
    r = WHEEL_D / 2
    plate_z0 = h - PLATE_T
    cheek_in, cheek_out = WHEEL_W / 2 + 0.07, WHEEL_W / 2 + 0.15

    hub = cylinder_y(0.45, WHEEL_W + 0.05, x=axle_x, z=r)
    tire = Cylinder(r * IN, WHEEL_W * IN)
    tire = fillet(tire.edges().filter_by(GeomType.CIRCLE), radius=0.12 * IN)
    tire = tire.move(Location((axle_x * IN, 0, r * IN), (90, 0, 0))) - hub
    axle = cylinder_y(0.125, 2 * cheek_out + 0.2, x=axle_x, z=r)
    hub = hub - axle

    if swivel:
        top = plate_z0 - 0.2
        cheek_pts = [(-0.5, top), (0.7, top), (axle_x + 0.3, r - 0.2), (axle_x - 0.3, r - 0.2)]
    else:
        top = plate_z0
        cheek_pts = [(-0.6, top), (0.6, top), (0.3, r - 0.2), (-0.3, r - 0.2)]
    cheek_a = prism_xz(cheek_pts, cheek_in, cheek_out) - axle
    cheek_b = prism_xz(cheek_pts, -cheek_out, -cheek_in) - axle
    steel = [box(-PLATE_X / 2, PLATE_X / 2, -PLATE_Y / 2, PLATE_Y / 2, plate_z0, h), cheek_a, cheek_b, hub, axle]

    if swivel:
        race = Cylinder(0.85 * IN, 0.2 * IN, align=(Align.CENTER, Align.CENTER, Align.MIN)).move(
            Location((0, 0, top * IN))
        )
        crown = box(-0.5, 0.7, -cheek_in, cheek_in, top - 0.1, top)
        lever = prism_xz(
            [(0.75, top - 0.1), (1.0, top - 0.1), (2.1, top - 0.5), (2.1, top - 0.58), (0.75, top - 0.18)],
            -0.3,
            0.3,
        )
        steel += [race, crown, lever]

    bolts = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            bx, by = sx * BOLT_X / 2, sy * BOLT_Y / 2
            location = Location((bx * IN, by * IN, 0))
            shank = Cylinder(CASTER_SCREW_D / 2 * IN, CASTER_SCREW_L * IN, align=(Align.CENTER, Align.CENTER, Align.MIN)).move(
                Location((0, 0, plate_z0 * IN))
            )
            screw_head = Cylinder(CASTER_SCREW_HEAD_D / 2 * IN, CASTER_SCREW_HEAD_H * IN, align=(Align.CENTER, Align.CENTER, Align.MIN)).move(
                Location((0, 0, (plate_z0 - CASTER_SCREW_HEAD_H) * IN))
            )
            bolts.append(location * (Part() + [shank, screw_head]))
    steel = [cut_all(part, bolts) for part in steel]

    move = Location((cx * IN, cy * IN, 0))
    return [move * s for s in steel], move * tire, [move * s for s in bolts]


caster_x_l = x_in_l + CASTER_INSET_X
caster_x_r = x_in_r - CASTER_INSET_X
caster_y_f = y_front + CASTER_FRONT_Y
caster_y_r = post_y0 - CASTER_REAR_Y
casters = {
    "caster_swivel_front": caster(caster_x_l, caster_y_f, True),
    "caster_swivel_rear": caster(caster_x_l, caster_y_r, True),
    "caster_rigid_front": caster(caster_x_r, caster_y_f, False),
    "caster_rigid_rear": caster(caster_x_r, caster_y_r, False),
}

# --- Holes in the wood for every screw and bolt --------------------------------
fasteners = list(screws.values())
for _, _, caster_bolts in casters.values():
    fasteners += caster_bolts
for name in list(wood):
    wood[name] = cut_all(wood[name], fasteners)

# --- Register parts -------------------------------------------------------------
for name, part in wood.items():
    show(part, name)
show(Compound(label="wood_screws", children=list(screws.values())), "wood_screws")
for name, (steel, tire, caster_bolts) in casters.items():
    show(Compound(label=f"{name}_steel", children=steel), f"{name}_steel")
    show(tire, f"{name}_tire")
    show(Compound(label=f"{name}_bolts", children=caster_bolts), f"{name}_bolts")

all_parts = list(wood.values()) + list(screws.values())
for steel, tire, caster_bolts in casters.values():
    all_parts += steel + [tire] + caster_bolts
result = Compound(label="shelf_unit", children=all_parts)

part_names = list(wood) + list(screws)
