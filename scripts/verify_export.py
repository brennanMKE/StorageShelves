"""Run shelf_unit.py outside the MCP server, verify it, export a STEP assembly, verify the re-import."""
import copy
import itertools
import runpy
from pathlib import Path

from build123d import Compound, Location, export_step, import_step

PROJECT = Path("/Users/brennan/Developer/CAD/ElectronicsStorageShelves")
SCRIPT = PROJECT / "scripts" / "shelf_unit.py"
OUT = PROJECT / "output"
STEP = OUT / "shelf_unit.step"
IN = 25.4
THRESH = 0.01  # mm^3
BOX_TOL = 1e-6


def show(shape, name=None):
    pass


ns = runpy.run_path(str(SCRIPT), init_globals={"show": show})
wood, screws, casters, result = ns["wood"], ns["screws"], ns["casters"], ns["result"]

# --- Named, categorised flat parts list -----------------------------------------
parts = []  # (name, category, shape)
for name, shape in wood.items():
    parts.append((name, "nosing" if name.startswith("nosing") else "wood", shape))
for name, shape in screws.items():
    parts.append((f"screw_{name}", "fastener", shape))
for cname, (steel, tire, bolts) in casters.items():
    for i, s in enumerate(steel):
        parts.append((f"{cname}_steel_{i}", "steel", s))
    parts.append((f"{cname}_tire", "tire", tire))
    for i, s in enumerate(bolts):
        parts.append((f"{cname}_screw_{i}", "fastener", s))

print("wood", len(wood), "screws", len(screws), "caster parts",
      sum(len(st) + 1 + len(bo) for st, _, bo in casters.values()))

# --- 1. Verification ------------------------------------------------------------
solids = result.solids()
print(f"result solids: {len(solids)}")
per_part = [(n, len(s.solids())) for n, _, s in parts]
print(f"named parts: {len(parts)}, solids across named parts: {sum(c for _, c in per_part)}")
for n, c in per_part:
    if c != 1:
        print(f"  part {n} has {c} solids")

invalid = [i for i, s in enumerate(solids) if not s.is_valid]
print(f"valid solids: {len(solids) - len(invalid)}/{len(solids)}; invalid indices: {invalid}")
print(f"result.is_valid: {result.is_valid}")

bb = result.bounding_box()
print("bbox mm:", bb.size.X, bb.size.Y, bb.size.Z)
print(f"bbox in: {bb.size.X / IN:.6f} x {bb.size.Y / IN:.6f} x {bb.size.Z / IN:.6f}")
print(f"bbox min (in): {bb.min.X / IN:.6f} {bb.min.Y / IN:.6f} {bb.min.Z / IN:.6f}")
print(f"bbox max (in): {bb.max.X / IN:.6f} {bb.max.Y / IN:.6f} {bb.max.Z / IN:.6f}")

total_vol = sum(s.volume for s in solids)
print(f"total solid volume mm^3: {total_vol:.3f}")

# Name each solid for overlap reporting.
named_solids = []
for n, _, shape in parts:
    for s in shape.solids():
        named_solids.append((n, s))
boxes = [(n, s, s.bounding_box()) for n, s in named_solids]
candidates = 0
worst = 0.0
hits = []
errors = []
for (na, a, ba), (nb, b, bb2) in itertools.combinations(boxes, 2):
    if (ba.min.X < bb2.max.X - BOX_TOL and bb2.min.X < ba.max.X - BOX_TOL
            and ba.min.Y < bb2.max.Y - BOX_TOL and bb2.min.Y < ba.max.Y - BOX_TOL
            and ba.min.Z < bb2.max.Z - BOX_TOL and bb2.min.Z < ba.max.Z - BOX_TOL):
        candidates += 1
        try:
            common = a.intersect(b)
            v = 0.0
            if common is not None:
                v = sum(s.volume for s in common.solids()) if hasattr(common, "solids") else common.volume
        except Exception as exc:  # report rather than treat as zero
            errors.append((na, nb, repr(exc)))
            continue
        worst = max(worst, v)
        if v > THRESH:
            hits.append((na, nb, v))
n_pairs = len(boxes) * (len(boxes) - 1) // 2
print(f"overlap: pairs {n_pairs}, bbox candidates {candidates}, over {THRESH} mm^3: {len(hits)}, "
      f"max intersection {worst:.6g} mm^3, boolean errors {len(errors)}")
for h in sorted(hits, key=lambda x: -x[2]):
    print("  OVERLAP", h)
for e in errors:
    print("  ERROR", e)

# --- 2. STEP assembly -----------------------------------------------------------
OUT.mkdir(exist_ok=True)
children = []
expected_vol = {}
for n, _, shape in parts:
    # Independent geometry per child: the screws share one TShape, and XCAF would
    # otherwise collapse them into a single product carrying only the last label.
    child = copy.deepcopy(shape.solids()[0])
    child.label = n
    children.append(child)
    expected_vol[n] = shape.volume
assembly = Compound(label="shelf_unit", children=children)
ok = export_step(assembly, str(STEP))
print(f"export_step returned {ok}; size {STEP.stat().st_size} bytes")

back = import_step(str(STEP))
back_solids = back.solids()
back_vol = sum(s.volume for s in back_solids)
print(f"re-import solids: {len(back_solids)}, volume {back_vol:.3f} mm^3, "
      f"diff {back_vol - total_vol:+.6f} mm^3 ({(back_vol - total_vol) / total_vol * 100:+.6f}%)")
print(f"re-import invalid solids: {sum(1 for s in back_solids if not s.is_valid)}")
bbb = back.bounding_box()
print(f"re-import bbox in: {bbb.size.X / IN:.6f} x {bbb.size.Y / IN:.6f} x {bbb.size.Z / IN:.6f}")


def walk(node, depth=0, out=None):
    out = [] if out is None else out
    out.append((depth, node.label, type(node).__name__))
    for c in getattr(node, "children", []) or []:
        walk(c, depth + 1, out)
    return out


tree = walk(back)
labels = [l for d, l, _ in tree if d >= 1]
print(f"re-import tree nodes: {len(tree)}, depth-1+ labelled: {sum(1 for l in labels if l)}")
print("top label:", back.label, "children:", len(back.children))
print("first children labels:", [c.label for c in back.children][:8])
missing = sorted(set(n for n, _, _ in parts) - set(labels))
print(f"expected names missing from re-import: {len(missing)} {missing[:10]}")
dupes = sorted(l for l in set(labels) if labels.count(l) > 1)
print(f"unique names in re-import: {len(set(labels))}, duplicated: {dupes}")
by_label = {c.label: c for c in back.children}
vol_err = max((abs(by_label[n].volume - v), n) for n, v in expected_vol.items() if n in by_label)
print(f"max per-part volume difference after re-import: {vol_err[0]:.6g} mm^3 ({vol_err[1]})")

# Positive control: the overlap measure must report a known interpenetration.
base = wood["base"].solids()[0]
bolt = casters["caster_rigid_front"][2][0].solids()[0]
real = base.intersect(bolt)
shifted = base.moved(Location((60, 0, 0))).intersect(bolt)
print("control, real base vs bolt:", 0.0 if real is None else sum(x.volume for x in real.solids()))
print("control, base shifted +60 mm in X vs bolt:", 0.0 if shifted is None else sum(x.volume for x in shifted.solids()))
