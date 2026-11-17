"""Printable cut sheets for the four shelf units and two totes.

Writes output/cut_sheets.pdf: part list with tape labels, one to-scale page per
plywood sheet with its cut sequence, and the solid-stock breakdown.

Formulas and labels match output/cut_list.html. Dimensions use the model's
default stock sizes below; if the measured stock differs, change them here
and re-run:  uv run --with reportlab python scripts/cut_sheets_pdf.py
"""
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    Flowable, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

OUT = Path(__file__).resolve().parent.parent / "output" / "cut_sheets.pdf"

# --- Stock sizes (in): model defaults; measure the delivered stock ---
t, b, p, n, h = 0.703, 0.25, 1.25, 0.75, 2.6

# --- Derived (same formulas as the plans and cut_list.html) ---
W, D, H, UPPER, NOSE_H = 30.0, 15.0, 29.5, 18.0, 1.4375
I = W - 0.5 - 2 * t
d = D - n - b
L = H - h - t
RAIL = I - 2 * p + 0.25
BASE_D = D - n
E_W, H_END = 7.75, 9 - t
IL = 12.5 - 0.25 - 2 * t
BAY = (E_W - 2 * b - b) / 2
LEDGER_TOP = UPPER - t
SHELF_LOW = h + t

INK = colors.HexColor("#18222b")
MUTED = colors.HexColor("#5a6872")
ACCENT = colors.HexColor("#1d5f8c")
TAPE = colors.HexColor("#4aa3df")
MAPLE = colors.HexColor("#ead3a6")
MAPLE_THIN = colors.HexColor("#f4e6c9")
PINE = colors.HexColor("#e0c08f")
SPARE = colors.HexColor("#eef1f2")


def frac(x):
    """Nearest 1/32 as shop notation: 26-3/16"."""
    q = round(x * 32)
    whole, r = divmod(q, 32)
    if not r:
        return f'{whole}"'
    den = 32
    while r % 2 == 0:
        r //= 2
        den //= 2
    return f'{whole}-{r}/{den}"' if whole else f'{r}/{den}"'


def dec(x):
    return f"{x:.3f}".rstrip("0").rstrip(".")


def both(x):
    return f"{dec(x)} ({frac(x)})"


# --- Styles ---
S = {
    "h1": ParagraphStyle("h1", fontName="Helvetica-Bold", fontSize=22, leading=26, textColor=INK, spaceAfter=4),
    "h2": ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=15, leading=19, textColor=INK, spaceBefore=6, spaceAfter=4),
    "body": ParagraphStyle("body", fontName="Helvetica", fontSize=9.5, leading=12.5, textColor=INK, alignment=TA_LEFT),
    "small": ParagraphStyle("small", fontName="Helvetica", fontSize=8, leading=10, textColor=MUTED),
    "cell": ParagraphStyle("cell", fontName="Helvetica", fontSize=8.5, leading=10.5, textColor=INK),
    "cellb": ParagraphStyle("cellb", fontName="Helvetica-Bold", fontSize=8.5, leading=10.5, textColor=INK),
    "lbl": ParagraphStyle("lbl", fontName="Helvetica-Bold", fontSize=9, leading=11, textColor=ACCENT),
}


def P(text, style="cell"):
    return Paragraph(text, S[style])


# --- Part lists: (labels, name, qty per build, length, width, thick, stock, note) ---
SHELF = [
    ("A1", "Base / lower shelf", 1, W, BASE_D, t, '3/4 maple ply', "No notches. Casters screw into the underside."),
    ("B1 left, B2 right", "Side panel", 2, L, d, t, '3/4 maple ply', "Grain vertical. Gang-cut the pair."),
    ("C1", "Upper shelf", 1, I, d, t, '3/4 maple ply', f"Notch both rear corners {frac(p)} square. Fit to the case."),
    ("D1", "Back", 1, W - 0.5, L, b, '1/4 maple ply', "One piece. Final-trim to the frame."),
    ("E1 left, E2 right", "Rear corner post", 2, L, p, p, "2x2, planed", "Three 1/8 housings (see below)."),
    ("F1", "Bottom rear rail", 1, RAIL, p, p, "2x2, planed", "Includes 1/8 housing each end."),
    ("F2", "Upper rear ledger", 1, RAIL, p, p, "2x2, planed", f"Top {dec(LEDGER_TOP)} above floor."),
    ("F3", "Rear top rail", 1, RAIL, 1.5, 0.75, "1x2 clear pine", "Top flush with the side tops."),
    ("G1 left, G2 right", "Upper side cleat", 2, d - p, p, p, "2x2, planed", "Top level with the ledger."),
    ("H1 lower, H2 upper", "Nosing", 2, I, NOSE_H, n, "2x4, ripped 3/4", "Height 1-3/8 to 1-1/2 (estimate). Rises 1/2 above shelf."),
]
TOTE = [
    ("J1", "Flat base", 1, 12.5, 8, t, '3/4 maple ply', "1/8 overhang all round."),
    ("K1 left, K2 right", "Shaped end panel", 2, H_END, E_W, t, '3/4 maple ply',
     f"Taper to 3 flat top; 1 in Forstner hole 1/4 deep, {dec(7.875 - t)} above bottom."),
    ("L1 front, L2 back", "Wall", 2, IL, 3, b, '1/4 maple ply', "Between the end panels."),
    ("M1", "Long centre divider", 1, IL, 2.75, b, '1/4 maple ply', "Centred."),
    ("N1 front, N2 back", "Short divider", 2, BAY, 2.75, b, '1/4 maple ply', "One per bay."),
    ("P1-P4", "Inside corner cleat", 4, 2.5, 1.125, 0.5, "2x2 offcut, ripped", "P1 front-left, P2 front-right, P3 back-left, P4 back-right."),
    ("R1", "Handle", 1, IL + 0.5, 1, 1, "1 in dowel", "Round, 1 in diameter."),
]


def part_table(rows, builds):
    data = [[P("<b>Label</b>"), P("<b>Part</b>"), P("<b>Per</b>"), P("<b>Total</b>"), P("<b>Length</b>"),
             P("<b>Width</b>"), P("<b>Thick</b>"), P("<b>Stock</b>"), P("<b>Notes</b>"), P("<b>Cut</b>")]]
    for lbl, name, q, ln, wd, th, stock, note in rows:
        data.append([P(lbl, "lbl"), P(name, "cellb"), P(str(q)), P(f"<b>{q * builds}</b>"),
                     P(both(ln)), P(both(wd)), P(both(th)), P(stock), P(note), ""])
    tbl = Table(data, colWidths=[76, 92, 26, 40, 82, 76, 70, 82, 146, 30], repeatRows=1)
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), SPARE),
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, colors.HexColor("#c9d1d6")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("BOX", (-1, 1), (-1, -1), 0.4, MUTED), ("INNERGRID", (-1, 1), (-1, -1), 0.4, MUTED),
    ]))
    return tbl


# --- Drawing helpers ---
class SheetDrawing(Flowable):
    """A 96 x 48 in sheet drawn to scale with the parts and cut lines."""

    def __init__(self, kind, number, width=720):
        super().__init__()
        self.kind, self.number = kind, number
        self.s = width / 100.0  # points per inch, with room for dimension labels
        self.width, self.height = width, 54 * self.s

    def X(self, x):
        return (x + 2.5) * self.s

    def Y(self, y):  # y measured down from the top edge of the sheet
        return (48 - y + 2.0) * self.s

    def rect(self, x, y, w, hgt, fill, stroke=INK, lw=0.6, dash=None):
        c = self.canv
        c.setLineWidth(lw)
        c.setStrokeColor(stroke)
        c.setDash(*dash) if dash else c.setDash()
        c.setFillColor(fill or colors.white)
        c.rect(self.X(x), self.Y(y + hgt), w * self.s, hgt * self.s, stroke=1, fill=1 if fill else 0)
        c.setDash()

    def label(self, x, y, w, hgt, code, text):
        c = self.canv
        cx, cy = self.X(x + w / 2), self.Y(y + hgt / 2)
        size = max(5.5, min(11, w * self.s / (len(code) * 0.75), hgt * self.s / 3))
        tw = c.stringWidth(code, "Helvetica-Bold", size) + 6
        c.setFillColor(TAPE)
        c.rect(cx - tw / 2, cy + 1, tw, size + 3, stroke=0, fill=1)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", size)
        c.drawCentredString(cx, cy + 2.6, code)
        if text:
            c.setFillColor(INK)
            fs = max(5, min(8, w * self.s / (len(text) * 0.55)))
            c.setFont("Helvetica", fs)
            c.drawCentredString(cx, cy - fs - 1, text)

    def dim_h(self, x0, x1, y, text):
        c = self.canv
        c.setStrokeColor(MUTED)
        c.setLineWidth(0.4)
        Y = self.Y(y)
        c.line(self.X(x0), Y, self.X(x1), Y)
        for x in (x0, x1):
            c.line(self.X(x), Y - 3, self.X(x), Y + 3)
        c.setFillColor(MUTED)
        c.setFont("Helvetica", 7.5)
        c.drawCentredString(self.X((x0 + x1) / 2), Y + 2.5, text)

    def dim_v(self, x, y0, y1, text):
        c = self.canv
        c.setStrokeColor(MUTED)
        c.setLineWidth(0.4)
        X = self.X(x)
        c.line(X, self.Y(y0), X, self.Y(y1))
        for y in (y0, y1):
            c.line(X - 3, self.Y(y), X + 3, self.Y(y))
        c.saveState()
        c.translate(X - 3, self.Y((y0 + y1) / 2))
        c.rotate(90)
        c.setFillColor(MUTED)
        c.setFont("Helvetica", 7.5)
        c.drawCentredString(0, 0, text)
        c.restoreState()

    def draw(self):
        self.rect(0, 0, 96, 48, SPARE, MUTED, 0.8)
        (self.draw_thick if self.kind == "thick" else self.draw_thin)()

    def draw_thick(self):
        u1, u2, tote = 2 * self.number - 1, 2 * self.number, f"T{self.number}"
        BW, BH = 31.5, 14.5
        plan = [
            [("side", f"{u1}-B1"), ("side", f"{u1}-B2"), ("base", f"{u1}-A1")],
            [("side", f"{u2}-B1"), ("side", f"{u2}-B2"), ("deck", f"{u1}-C1")],
            [("base", f"{u2}-A1"), ("deck", f"{u2}-C1"), ("tote", tote)],
        ]
        for r, row in enumerate(plan):
            for col, (kind, code) in enumerate(row):
                x, y = col * (BW + 0.25), r * (BH + 0.25)
                self.rect(x, y, BW, BH, None, MUTED, 0.5, (3, 2))
                px, py = x + 0.25, y + 0.25
                if kind == "side":
                    self.rect(px, py, L, d, MAPLE)
                    self.label(px, py, L, d, code, f"SIDE {frac(L)} x {frac(d)}")
                elif kind == "base":
                    self.rect(px, py, W, BASE_D, MAPLE)
                    self.label(px, py, W, BASE_D, code, f"BASE {frac(W)} x {frac(BASE_D)}")
                elif kind == "deck":
                    c = self.canv
                    c.setFillColor(MAPLE)
                    c.setStrokeColor(INK)
                    c.setLineWidth(0.6)
                    pts = [(px, py + p), (px + p, py + p), (px + p, py), (px + I - p, py), (px + I - p, py + p),
                           (px + I, py + p), (px + I, py + d), (px, py + d)]
                    path = c.beginPath()
                    path.moveTo(self.X(pts[0][0]), self.Y(pts[0][1]))
                    for qx, qy in pts[1:]:
                        path.lineTo(self.X(qx), self.Y(qy))
                    path.close()
                    c.drawPath(path, stroke=1, fill=1)
                    self.label(px, py, I, d, code, f"UPPER SHELF {frac(I)} x {frac(d)}, rear notches")
                else:
                    self.rect(px, py, 12.5, 8, MAPLE, ACCENT, 1)
                    self.label(px, py, 12.5, 8, f"{tote}-J1", "BASE 12-1/2 x 8")
                    for i, k in enumerate(("K1", "K2")):
                        ex = px + 12.75 + i * (H_END + 0.25)
                        self.rect(ex, py, H_END, E_W, MAPLE, ACCENT, 1)
                        self.label(ex, py, H_END, E_W, f"{tote}-{k}", f"END {frac(H_END)} x 7-3/4")
        for col in range(3):
            x = col * (BW + 0.25)
            self.dim_h(x, x + BW, -0.9, '31-1/2" blank')
        for r in range(3):
            y = r * (BH + 0.25)
            self.dim_v(-0.6, y, y + BH, '14-1/2"')

    def draw_thin(self):
        u1, u2, tote = 2 * self.number - 1, 2 * self.number, f"T{self.number}"
        c = self.canv
        c.setStrokeColor(MUTED)
        c.setDash(4, 2)
        c.line(self.X(0), self.Y(27.1), self.X(96), self.Y(27.1))
        c.setDash()
        for i, u in enumerate((u1, u2)):
            x = i * 30.25
            self.rect(x, 0, 30, 27, None, MUTED, 0.5, (3, 2))
            self.rect(x + 0.25, 0.4, W - 0.5, L, MAPLE_THIN)
            self.label(x + 0.25, 0.4, W - 0.5, L, f"{u}-D1", f"BACK {frac(W - 0.5)} x {frac(L)}")
        x0 = 60.5
        self.rect(x0, 0, 30, 27, None, MUTED, 0.5, (3, 2))
        x0, y0 = x0 + 0.25, 0.4
        parts = [(0, IL, 3, "L1", "WALL"), (3.25, IL, 3, "L2", "WALL"), (6.5, IL, 2.75, "M1", "DIVIDER")]
        for dy, w, hh, k, nm in parts:
            self.rect(x0, y0 + dy, w, hh, MAPLE_THIN, ACCENT, 1)
            self.label(x0, y0 + dy, w, hh, f"{tote}-{k}", f"{nm} {frac(w)} x {frac(hh)}")
        for i, k in enumerate(("N1", "N2")):
            self.rect(x0 + IL + 0.25, y0 + i * 3.0, BAY, 2.75, MAPLE_THIN, ACCENT, 1)
            self.label(x0 + IL + 0.25, y0 + i * 3.0, BAY, 2.75, f"{tote}-{k}", "")
        c.setFillColor(MUTED)
        c.setFont("Helvetica", 8)
        c.drawCentredString(self.X(x0 + 14), self.Y(18), "rest of this blank is spare")
        c.setFont("Helvetica", 10)
        c.drawCentredString(self.X(48), self.Y(38), "Spare strip, about 21 x 96: keep for repairs and test cuts")
        for i in range(3):
            self.dim_h(i * 30.25, i * 30.25 + 30, -0.9, '30" blank')
        self.dim_v(-0.6, 0, 27, '27" band')
        self.dim_v(-0.6, 27.1, 48, "rest")


class Bar(Flowable):
    """One length of solid stock with its rough cuts."""

    def __init__(self, title, segs, total=96, width=720):
        super().__init__()
        self.title, self.segs, self.total = title, segs, total
        self.width, self.height = width, 30
        self.s = (width - 130) / 96.0

    def draw(self):
        c = self.canv
        c.setFont("Helvetica-Bold", 9)
        c.setFillColor(INK)
        c.drawString(0, 11, self.title)
        x0 = 130
        c.setFillColor(SPARE)
        c.setStrokeColor(MUTED)
        c.setLineWidth(0.5)
        c.rect(x0, 2, self.total * self.s, 24, stroke=1, fill=1)
        x = 0
        for ln, text, spare in self.segs:
            c.setFillColor(SPARE if spare else PINE)
            c.setStrokeColor(MUTED if spare else INK)
            c.rect(x0 + x * self.s, 4, ln * self.s, 20, stroke=1, fill=1)
            c.setFillColor(INK)
            c.setFont("Helvetica-Bold" if not spare else "Helvetica", 7.5)
            c.drawCentredString(x0 + (x + ln / 2) * self.s, 11.5, text)
            x += ln + 0.4


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(MUTED)
    canvas.drawString(36, 20, f"Shelf & Tote Cut Sheets  |  stock t={dec(t)} b={dec(b)} p={dec(p)} n={dec(n)} h={dec(h)}  |  "
                              "inches, length along grain, fractions to nearest 1/32")
    canvas.drawRightString(756, 20, f"Page {doc.page}")
    canvas.restoreState()


def build():
    doc = SimpleDocTemplate(str(OUT), pagesize=landscape(letter), leftMargin=36, rightMargin=36,
                            topMargin=30, bottomMargin=36, title="Shelf & Tote Cut Sheets",
                            author="Electronics workbench project")
    st = []
    st.append(P("Shelf &amp; Tote Cut Sheets", "h1"))
    st.append(P("Four shelf units (builds 1-4) and two soldering totes (T1, T2). Write each part's label on "
                "painter's tape with a Sharpie as soon as it is cut: <b>build - letter + number</b>, e.g. "
                "<b>2-B1</b> or <b>T1-K2</b>. Put the tape on a hidden face with an arrow to the front or top edge. "
                "Left and right are as seen from the front. Letters I, O and Q are skipped.", "body"))
    st.append(Spacer(1, 4))
    st.append(P("Sizes use the model's stock values in the footer. If your measured stock differs, use the "
                "live cut list page, which recalculates, or edit and re-run scripts/cut_sheets_pdf.py.", "small"))
    st.append(Spacer(1, 6))
    st.append(P("Shelf unit parts (x4)", "h2"))
    st.append(part_table(SHELF, 4))
    st.append(Spacer(1, 6))
    housing = Table([
        [P("<b>Post housings (E1, E2)</b>"), P("<b>From post bottom</b>"), P("<b>To</b>"), P("<b>Width</b>"), P("<b>Depth</b>")],
        [P("F1 bottom rail"), P(both(0)), P(both(p)), P(both(p)), P('1/8"')],
        [P("F2 upper ledger"), P(both(LEDGER_TOP - p - SHELF_LOW)), P(both(LEDGER_TOP - SHELF_LOW)), P(both(p)), P('1/8"')],
        [P("F3 rear top rail"), P(both(L - 1.5)), P(both(L)), P(both(0.75) + " at rear"), P('1/8"')],
    ], colWidths=[130, 110, 110, 110, 60])
    housing.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), SPARE),
                                 ("LINEBELOW", (0, 0), (-1, -1), 0.4, colors.HexColor("#c9d1d6"))]))
    st.append(housing)
    st.append(PageBreak())
    st.append(P("Tote parts (x2)", "h2"))
    st.append(part_table(TOTE, 2))
    st.append(Spacer(1, 10))
    st.append(P("Hardware", "h2"))
    for line in [
        "96 #8 x 1-1/4 wood screws: 18 per shelf, 12 per tote (delivered, 200-count box).",
        "16 casters, 2 in: 8 swivel/brake + 8 rigid (delivered).",
        "64 caster mounting screws, 4 per caster, up into the base. #10 x 5/8 pan head is an estimate: "
        "match the plate holes. Not on the order.",
        "About 24 in of 1 in round dowel for two tote handles. Not on the order.",
        "Painter's tape, Sharpie, wood glue, finish, abrasives.",
    ]:
        st.append(P("&bull; " + line, "body"))
    st.append(PageBreak())

    steps_thick = [
        "1. Rip the sheet lengthwise into three 14-1/2 rows.",
        "2. Crosscut each row into three 31-1/2 blanks. Grain runs along the 31-1/2.",
        "3. Tape-label every blank now, using the labels shown.",
        "4. Gang-cut to final size: stack {u1}-B1 + {u1}-B2, then {u2}-B1 + {u2}-B2, then {u1}-A1 + {u2}-A1. "
        "Rip to width off a factory edge, then crosscut to length.",
        "5. Leave the upper shelves ({u1}-C1, {u2}-C1) oversize until each case is assembled, then fit and notch them.",
        "6. Tote {tote}: cut the base and both end panels from the last blank.",
    ]
    steps_thin = [
        "1. Rip a 27 band off the full 96 length. Keep the 21 strip as spare.",
        "2. Crosscut the band into three 30 blanks. Grain runs along the 30.",
        "3. Backs {u1}-D1 and {u2}-D1: leave them slightly oversize and final-trim to each assembled frame.",
        "4. Third blank, tote {tote}: rip strips 3, 3 and 2-3/4 wide, crosscut to {il}, then cut two {bay} short dividers.",
    ]
    for kind, steps, title in (("thick", steps_thick, "3/4 maple ply"), ("thin", steps_thin, "1/4 maple ply")):
        for num in (1, 2):
            u1, u2, tote = 2 * num - 1, 2 * num, f"T{num}"
            block = [P(f"{title}, sheet {num} of 2: shelves {u1} and {u2}, tote {tote}", "h2"),
                     SheetDrawing(kind, num), Spacer(1, 6)]
            for s_ in steps:
                block.append(P(s_.format(u1=u1, u2=u2, tote=tote, il=frac(IL), bay=frac(BAY)), "body"))
            block.append(Spacer(1, 3))
            block.append(P("Dashed lines are the rough blanks. Blue outlines are tote parts. Drawn to scale; "
                           "always measure, never scale off the print.", "small"))
            st.append(KeepTogether(block))
            st.append(PageBreak())

    st.append(P("Solid stock: rough cuts", "h2"))
    st.append(P("Rough lengths come from the plan to allow for planing and snipe. Plane the 2x2s to "
                f"{frac(p)} square while they are long, then cut to the finished lengths on page 1.", "body"))
    st.append(Spacer(1, 8))
    post, rail, cleat = 27.25, 26.75, 13.25
    bars = [
        ("2x2 boards 1-4", [(post, "E post", 0), (post, "E post", 0), (rail, "F1/F2 rail", 0), (cleat, "G cleat", 0)]),
        ("2x2 boards 5-6", [(rail, "F1/F2 rail", 0), (rail, "F1/F2 rail", 0), (cleat, "G cleat", 0), (cleat, "G cleat", 0)]),
        ("2x2 board 7", [(12, "P cleats", 0), (83.6, "spare", 1)]),
        ("2x2 board 8", [(96, "spare, for defects", 1)]),
        ("1x2 x 4' boards 1-4", [(rail, "F3 top rail", 0), (20.85, "offcut", 1)], 48),
        ("2x4 #1, strips 1-2", [(31, "H nosing", 0), (31, "H nosing", 0), (31, "H nosing", 0)]),
        ("2x4 #1, strip 3", [(31, "H nosing", 0), (31, "H nosing", 0), (31, "spare", 1)]),
        ("2x4 #2", [(96, "spare (caster pads removed)", 1)]),
    ]
    for item in bars:
        st.append(Bar(item[0], item[1], item[2] if len(item) > 2 else 96))
        st.append(Spacer(1, 6))
    st.append(Spacer(1, 6))
    for line in [
        "2x2 boards 1-6 give 8 posts (E), 8 square rails (4 F1 + 4 F2) and 8 cleats (G).",
        "Tote cleats: cut 12 in from board 7, rip two 1-1/8 x 1/2 strips, each gives four 2-1/2 cleats (P1-P4 for each tote).",
        "Nosing: rip three 3/4 strips from the 3-1/2 face of 2x4 #1. Use a push stick. Rough 31 in sections fit in the car.",
    ]:
        st.append(P("&bull; " + line, "body"))

    doc.build(st, onFirstPage=footer, onLaterPages=footer)
    print(OUT)


if __name__ == "__main__":
    build()
