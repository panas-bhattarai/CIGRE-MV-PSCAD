"""Single-line diagram of the CIGRE European MV benchmark, drawn with schemdraw from the data file.
Writes results/figures/fig01_single_line.{png,pdf,svg}. Python 3.11, schemdraw >= 0.23."""
import os, json, math
import schemdraw
import schemdraw.elements as e
from schemdraw.segments import SegmentCircle, Segment, SegmentText

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, ".."))
FIG = os.path.join(ROOT, "results", "figures"); os.makedirs(FIG, exist_ok=True)
D = json.load(open(os.path.join(ROOT, "data", "cigre_mv_european_tb575.json"), encoding="utf-8"))
SEG = {l["segment"]: l for l in D["lines"]}
SW = {s["line_segment"]: s for s in D["switches"]}
LOADS = {ld["bus"]: ld for ld in D["loads"]}

BLUE, ORANGE, GREY, INK, YEL = "#2a78d6", "#eb6834", "#8a8985", "#0b0b0b", "#eda100"
BAR = 0.9   # half-length of a busbar

# bus-bar centres (x, y)
P = {0: (4, 3), 1: (0, 1), 2: (0, -1), 3: (0, -3),
     4: (-3, -5), 5: (-3, -7), 6: (-3, -9), 7: (-3, -11),
     8: (3, -5), 9: (3, -7), 10: (3, -9), 11: (3, -11),
     12: (8, 1), 13: (8, -3), 14: (8, -7)}

class Trafo2(e.Element):
    """Two-winding transformer as two overlapping circles, vertical."""
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        r = 0.32
        self.segments.append(SegmentCircle((0, 0.55), r))
        self.segments.append(SegmentCircle((0, 0.05), r))
        self.segments.append(Segment([(0, 0.87), (0, 1.2)]))
        self.segments.append(Segment([(0, -0.27), (0, -0.6)]))
        self.anchors["start"] = (0, 1.2); self.anchors["end"] = (0, -0.6)
        self.params["theta"] = 0

def busbar(d, n, kv=None):
    x, y = P[n]
    d += e.Line().at((x - BAR, y)).to((x + BAR, y)).linewidth(3.2).color(INK)
    d += e.Label().at((x - BAR - 0.15, y)).label(str(n), loc="left", fontsize=11, halign="right")
    return (x, y)

def seg_label(d, xy, seg, dx=0.15, dy=0.0, halign="left"):
    L = SEG[seg]["length_km"]
    d += e.Label().at((xy[0] + dx, xy[1] + dy)).label("%.2f km" % L, fontsize=7.5, color=GREY, halign=halign)

def vline(d, seg, xa, ya, yb, col, side="right"):
    d += e.Line().at((xa, ya)).to((xa, yb)).color(col).linewidth(1.6)
    if side == "right":
        seg_label(d, (xa, (ya + yb) / 2), seg)
    else:
        seg_label(d, (xa, (ya + yb) / 2), seg, dx=-0.15, halign="right")

def switch_glyph(d, c, vertical, name):
    """Open switch drawn along the line: a masked gap, two contacts and a slanted blade."""
    x, y = c
    if vertical:
        d += e.Line().at((x, y - 0.45)).to((x, y + 0.45)).color("white").linewidth(7)
        d += e.Line().at((x, y - 0.45)).to((x, y - 0.32)).color(INK).linewidth(1.4)
        d += e.Line().at((x, y + 0.32)).to((x, y + 0.45)).color(INK).linewidth(1.4)
        d += e.Dot(radius=0.05).at((x, y - 0.32)).color(INK)
        d += e.Dot(radius=0.05).at((x, y + 0.32)).color(INK)
        d += e.Line().at((x, y - 0.32)).to((x + 0.32, y + 0.28)).color(INK).linewidth(1.4)
        d += e.Label().at((x + 0.4, y)).label(name + " open", fontsize=7.5, halign="left")
    else:
        d += e.Line().at((x - 0.45, y)).to((x + 0.45, y)).color("white").linewidth(7)
        d += e.Line().at((x - 0.45, y)).to((x - 0.32, y)).color(INK).linewidth(1.4)
        d += e.Line().at((x + 0.32, y)).to((x + 0.45, y)).color(INK).linewidth(1.4)
        d += e.Dot(radius=0.05).at((x - 0.32, y)).color(INK)
        d += e.Dot(radius=0.05).at((x + 0.32, y)).color(INK)
        d += e.Line().at((x - 0.32, y)).to((x + 0.28, y + 0.32)).color(INK).linewidth(1.4)
        d += e.Label().at((x, y + 0.42)).label(name + " open", fontsize=7.5, halign="center")

with schemdraw.Drawing(show=False) as d:
    d.config(fontsize=9, color=INK, lw=1.4)
    # --- 110 kV source and bus 0
    x0, y0 = P[0]
    d += e.SourceSin().at((x0, y0 + 2.0)).down().length(1.2).label("110 kV grid\n5000 MVA, R/X 0.1", loc="right", fontsize=8, ofst=0.3)
    d += e.Line().at((x0, y0 + 0.8)).to((x0, y0)).color(INK)
    d += e.Line().at((x0 - 4.6, y0)).to((x0 + 4.6, y0)).linewidth(3.6).color(INK)
    d += e.Label().at((x0 - 4.75, y0)).label("0", fontsize=11, halign="right")
    d += e.Label().at((x0 + 4.7, y0)).label("110 kV", fontsize=8, color=GREY, halign="left")
    # --- transformers
    for tr, xb in ((D["transformers"][0], P[1][0]), (D["transformers"][1], P[12][0])):
        top = (xb, y0); bot = (xb, P[1][1])
        d += e.Line().at(top).to((xb, y0 - 0.4))
        t = Trafo2().at((xb, y0 - 1.6)); d += t
        d += e.Line().at((xb, y0 - 2.2)).to(bot)
        tap = tr["tap_setting_used_in_power_flow"]["secondary_pct"]
        d += e.Label().at((xb + 0.45, y0 - 1.05)).label("%s  25 MVA  110/20 kV  Dyn\ntap +%.3f %%" % (tr["id"], tap), fontsize=7.5, halign="left")
    # --- busbars 20 kV
    for n in range(1, 15):
        busbar(d, n)
    d += e.Label().at((P[12][0] + BAR + 0.15, P[12][1])).label("20 kV", fontsize=8, color=GREY, halign="left")
    # --- feeder 1 trunk
    vline(d, 1, 0, P[1][1], P[2][1], BLUE, side="left")
    vline(d, 2, 0, P[2][1], P[3][1], BLUE, side="left")
    # bus 3 -> 4 (left) and 3 -> 8 (right): drop from bus 3, then horizontal, then down
    for seg, tgt, xo in ((3, 4, -0.6), (12, 8, 0.6)):
        xt, yt = P[tgt]
        d += e.Line().at((xo, P[3][1])).to((xo, P[3][1] - 0.7)).color(BLUE).linewidth(1.6)
        d += e.Line().at((xo, P[3][1] - 0.7)).to((xt, P[3][1] - 0.7)).color(BLUE).linewidth(1.6)
        d += e.Line().at((xt, P[3][1] - 0.7)).to((xt, yt)).color(BLUE).linewidth(1.6)
        seg_label(d, (xt, (P[3][1] - 0.7 + yt) / 2), seg)
    vline(d, 4, P[4][0], P[4][1], P[5][1], BLUE)
    vline(d, 5, P[5][0], P[5][1], P[6][1], BLUE)
    vline(d, 8, P[8][0], P[8][1], P[9][1], BLUE, side="left")
    vline(d, 9, P[9][0], P[9][1], P[10][1], BLUE, side="left")
    vline(d, 10, P[10][0], P[10][1], P[11][1], BLUE, side="left")
    # segment 7: bus 8 -> bus 7, routed right of the 8-9-10-11 column, below bus 7
    xr = P[8][0] + BAR + 0.7; yb = P[7][1] - 1.6
    d += e.Line().at((P[8][0] + BAR, P[8][1])).to((xr, P[8][1])).color(BLUE).linewidth(1.6)
    d += e.Line().at((xr, P[8][1])).to((xr, yb)).color(BLUE).linewidth(1.6)
    d += e.Line().at((xr, yb)).to((P[7][0], yb)).color(BLUE).linewidth(1.6)
    d += e.Line().at((P[7][0], yb)).to((P[7][0], P[7][1])).color(BLUE).linewidth(1.6)
    seg_label(d, (xr, (P[8][1] + yb) / 2), 7)
    # --- tie switches (dashed, breaker symbol), radial base case = open
    def tie(d, seg, path, lab_at, vertical, km_at):
        s = SW[seg]
        for a, b in zip(path[:-1], path[1:]):
            d += e.Line().at(a).to(b).color(GREY).linewidth(1.3).linestyle("--")
        switch_glyph(d, lab_at, vertical, s["id"])
        d += e.Label().at(km_at).label("%.2f km" % SEG[seg]["length_km"], fontsize=7.5, color=GREY, halign="left")
    # S2: bus 6 -> bus 7 (vertical, same column)
    tie(d, 6, [(P[6][0], P[6][1]), (P[7][0], P[7][1])], (P[6][0], (P[6][1] + P[7][1]) / 2), True, (P[6][0] + 0.15, P[7][1] + 0.45))
    # S3: bus 11 -> bus 4 through the middle column
    tie(d, 11, [(P[11][0] - BAR, P[11][1]), (0, P[11][1]), (0, P[4][1]), (P[4][0] + BAR, P[4][1])], (0, (P[11][1] + P[4][1]) / 2), True, (0.15, (P[11][1] + P[4][1]) / 2 - 0.75))
    # S1: bus 14 -> bus 8 from above
    xm = (P[14][0] - BAR + P[8][0] + BAR) / 2 + 0.6; xin = P[8][0] + 0.5
    tie(d, 15, [(P[14][0] - BAR, P[14][1]), (xm, P[14][1]), (xm, P[8][1] + 0.9), (xin, P[8][1] + 0.9), (xin, P[8][1])], (xm, (P[14][1] + P[8][1] + 0.9) / 2), True, (xm + 0.15, (P[14][1] + P[8][1] + 0.9) / 2 - 0.75))
    # --- feeder 2
    vline(d, 13, P[12][0], P[12][1], P[13][1], ORANGE, side="left")
    vline(d, 14, P[13][0], P[13][1], P[14][1], ORANGE, side="right")
    # --- loads
    for n in range(1, 15):
        x, y = P[n]; ld = LOADS.get(n)
        if not ld: continue
        parts = [("R", ld["residential"]["S_kVA"]), ("CI", ld["commercial_industrial"]["S_kVA"])]
        parts = [(t, s) for t, s in parts if s]
        if not parts: continue
        for k, (t, s) in enumerate(parts):
            xx = x + 0.35 + 0.45 * k if n not in (4, 5, 6, 7) else x - 0.35 - 0.45 * k
            d += e.Line().at((xx, y)).to((xx, y - 0.5)).color(YEL).linewidth(1.8)
            d += e.Arrowhead().at((xx, y - 0.68)).theta(-90).color(YEL).fill(YEL)
        txt = "  ".join("%s %.0f" % (t, s) for t, s in parts) + " kVA"
        if n in (4, 5, 6, 7):
            d += e.Label().at((x - BAR - 0.05, y - 0.55)).label(txt, fontsize=6.3, color=GREY, halign="right")
        else:
            d += e.Label().at((x + 0.15, y - 0.9)).label(txt, fontsize=6.3, color=GREY, halign="left")
    # --- legend
    lx, ly = -5.4, P[7][1] - 2.4
    d += e.Line().at((lx, ly)).to((lx + 0.8, ly)).color(BLUE).linewidth(1.8); d += e.Label().at((lx + 0.95, ly)).label("cable NA2XS2Y 120 mm², feeder 1", fontsize=7.5, halign="left")
    d += e.Line().at((lx, ly - 0.5)).to((lx + 0.8, ly - 0.5)).color(ORANGE).linewidth(1.8); d += e.Label().at((lx + 0.95, ly - 0.5)).label("overhead A1 63 mm², feeder 2", fontsize=7.5, halign="left")
    d += e.Line().at((lx, ly - 1.0)).to((lx + 0.8, ly - 1.0)).color(GREY).linewidth(1.3).linestyle("--"); d += e.Label().at((lx + 0.95, ly - 1.0)).label("tie line with switch, open in base case", fontsize=7.5, halign="left")
    d += e.Line().at((lx + 0.4, ly - 1.35)).to((lx + 0.4, ly - 1.75)).color(YEL).linewidth(1.8); d += e.Arrowhead().at((lx + 0.4, ly - 1.9)).theta(-90).color(YEL).fill(YEL)
    d += e.Label().at((lx + 0.95, ly - 1.6)).label("load (R residential, CI commercial/industrial)", fontsize=7.5, halign="left")
    d.save(os.path.join(FIG, "fig01_single_line.png"), dpi=300, transparent=False)
    d.save(os.path.join(FIG, "fig01_single_line.pdf"), transparent=False)
    d.save(os.path.join(FIG, "fig01_single_line.svg"), transparent=False)
print("wrote fig01_single_line (png, pdf, svg)")
