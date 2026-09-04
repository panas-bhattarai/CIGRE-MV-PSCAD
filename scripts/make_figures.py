"""Figures for the CIGRE-MV-PSCAD paper/README (the single-line diagram is made by make_sld.py) (Python 3.11: numpy, matplotlib, pandapower).
Reads results/*.json and, where still present, raw PSCAD exports. Writes results/figures/*.png (and .pdf).
Figures whose inputs are missing are skipped with a message."""
import os, sys, json, math, glob
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
RES = os.path.join(ROOT, "results"); FIG = os.path.join(RES, "figures"); os.makedirs(FIG, exist_ok=True)
DATA = json.load(open(os.path.join(ROOT, "data", "cigre_mv_european_tb575.json"), encoding="utf-8"))

# fixed categorical order (colour-blind safe, validated palette)
C = dict(blue="#2a78d6", orange="#eb6834", aqua="#1baf7a", yellow="#eda100", magenta="#e87ba4", grey="#8a8985", ink="#0b0b0b")
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
                     "grid.color": "#e6e5e1", "grid.linewidth": 0.6, "axes.edgecolor": "#b5b4ae", "axes.linewidth": 0.8,
                     "legend.frameon": False, "figure.dpi": 150, "savefig.dpi": 300})

def save(fig, name):
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, name + ".png")); fig.savefig(os.path.join(FIG, name + ".pdf")); plt.close(fig)
    print("wrote", name)

def load_json(name):
    p = os.path.join(RES, name)
    return json.load(open(p)) if os.path.exists(p) else None

def read_outputs(case_dir, name):
    infs = glob.glob(os.path.join(case_dir, name + "*", name + ".inf"))
    if not infs: return None, None
    inf = infs[0]
    names = [ln.split('Desc="')[1].split('"')[0] for ln in open(inf) if "Desc=" in ln]
    outs = sorted(glob.glob(os.path.join(os.path.dirname(inf), name + "_*.out")))
    cols, t = [], None
    for o in outs:
        d = np.loadtxt(o, skiprows=1)
        if t is None: t = d[:, 0]
        cols.append(d[:, 1:])
    return t, dict(zip(names, np.hstack(cols).T))

# ---------------------------------------------------------------- 1 single-line diagram
def fig_single_line():
    import pandapower.networks as pn
    net = pn.create_cigre_network_mv(with_der=False)
    g = net.bus_geodata if hasattr(net, "bus_geodata") and len(net.bus_geodata) else None
    if g is None or "x" not in g:
        try:
            xy = {i: (float(net.bus.geo[i].split('[')[1].split(',')[0]), float(net.bus.geo[i].split(',')[1].split(']')[0])) for i in net.bus.index}
        except Exception:
            print("skip single-line: no geodata"); return
    else:
        xy = {i: (float(g.x[i]), float(g.y[i])) for i in g.index}
    # brochure numbering equals pandapower numbering here (bus 0 = 110 kV)
    fig, ax = plt.subplots(figsize=(5.2, 6.2))
    sw = {s["line_segment"]: s for s in DATA["switches"]}
    for l in DATA["lines"]:
        (x1, y1), (x2, y2) = xy[l["from_bus"]], xy[l["to_bus"]]
        col = C["blue"] if l["installation"] == "underground" else C["orange"]
        if l["segment"] in sw:
            ax.plot([x1, x2], [y1, y2], color=C["grey"], lw=1.4, ls=(0, (3, 2)), zorder=1)
            xm, ym = (x1 + x2) / 2, (y1 + y2) / 2
            ax.plot(xm, ym, marker="s", ms=6, mfc="white", mec=C["ink"], mew=0.9, zorder=3)
            off = (5, 4) if sw[l["segment"]]["id"] != "S1" else (-8, -14)
            ax.annotate(sw[l["segment"]]["id"] + " (open)", (xm, ym), xytext=off, textcoords="offset points", fontsize=7.5)
        else:
            ax.plot([x1, x2], [y1, y2], color=col, lw=1.8, zorder=1)
        xm, ym = (x1 + x2) / 2, (y1 + y2) / 2
        ax.annotate("%.2f km" % l["length_km"], (xm, ym), xytext=(3, -9), textcoords="offset points", fontsize=6.5, color=C["grey"])
    for tr in DATA["transformers"]:
        (x1, y1), (x2, y2) = xy[tr["from_bus"]], xy[tr["to_bus"]]
        ax.plot([x1, x2], [y1, y2], color=C["ink"], lw=1.2, zorder=1)
        xm, ym = (x1 + x2) / 2, (y1 + y2) / 2
        ax.plot(xm, ym, marker="o", ms=9, mfc="white", mec=C["ink"], mew=1.0, zorder=3)
        ax.plot(xm + 0.15, ym, marker="o", ms=9, mfc="none", mec=C["ink"], mew=1.0, zorder=3)
        ax.annotate(tr["id"] + "\n25 MVA 110/20 kV", (xm, ym), xytext=(8, 2), textcoords="offset points", fontsize=7)
    loads = {ld["bus"]: ld for ld in DATA["loads"]}
    for i, (x, y) in xy.items():
        has_load = i in loads and (loads[i]["residential"]["S_kVA"] or loads[i]["commercial_industrial"]["S_kVA"])
        ax.plot(x, y, marker="o", ms=7 if i else 9, mfc=C["yellow"] if has_load else "white", mec=C["ink"], mew=0.9, zorder=4)
        ax.annotate(str(i), (x, y), xytext=(-9 if i not in (0, 12, 13, 14) else 6, 4), textcoords="offset points", fontsize=8, fontweight="bold")
    ax.plot([], [], color=C["blue"], lw=1.8, label="cable NA2XS2Y 120 mm²")
    ax.plot([], [], color=C["orange"], lw=1.8, label="overhead A1 63 mm²")
    ax.plot([], [], color=C["grey"], lw=1.4, ls=(0, (3, 2)), label="tie line, switch open")
    ax.plot([], [], marker="o", ms=7, mfc=C["yellow"], mec=C["ink"], ls="none", label="bus with load")
    ax.legend(loc="upper left", fontsize=7.5)
    ax.set_title("CIGRE European MV benchmark, radial base case", fontsize=10)
    ax.set_aspect("equal"); ax.axis("off")
    save(fig, "fig01_single_line")

# ---------------------------------------------------------------- 2/3 voltage profile and error
def fig_voltage_profile():
    v = load_json("validation_cigre_mv_bias.json")
    if not v: return
    rows = [r for r in v["buses"] if r["bus"] > 0]
    b = [r["bus"] for r in rows]
    fig, ax = plt.subplots(figsize=(6.4, 3.2))
    for key, col, mk, ls, lab in (("tb_kv", C["grey"], "o", "-", "CIGRE TB 575, Table 9.6"), ("pp_kv", C["orange"], "s", "-", "pandapower, same data"),
                                  ("emt_kv", C["blue"], "^", "--", "PSCAD EMT (this model)")):
        for f1 in (True, False):
            rr = [r for r in rows if (r["bus"] <= 11) == f1]
            ax.plot([r["bus"] for r in rr], [r[key] for r in rr], color=col, lw=2, marker=mk, ms=4, ls=ls, label=lab if f1 else None)
    ax.set_xticks(b); ax.set_xlabel("bus"); ax.set_ylabel("line-to-line voltage (kV)")
    ax.axvspan(11.5, 14.5, color="#f2f1ee", zorder=0); ax.text(12, ax.get_ylim()[1] - 0.05, "feeder 2", fontsize=8, color=C["grey"], va="top")
    ax.text(1.2, ax.get_ylim()[1] - 0.05, "feeder 1", fontsize=8, color=C["grey"], va="top")
    ax.legend(loc="upper center", fontsize=8); ax.set_title("Steady-state voltage profile, radial base case", fontsize=10)
    save(fig, "fig02_voltage_profile")
    fig, ax = plt.subplots(figsize=(6.4, 2.8))
    w = 0.38
    ax.bar([x - w / 2 for x in b], [r["err_pp_pct"] for r in rows], w, color=C["orange"], label="vs pandapower (same data, load bias corrected)")
    ax.bar([x + w / 2 for x in b], [r["err_tb_pct"] for r in rows], w, color=C["grey"], label="vs brochure Table 9.6")
    ax.axhline(0, color=C["ink"], lw=0.8); ax.set_xticks(b); ax.set_xlabel("bus"); ax.set_ylabel("voltage difference (%)")
    ax.legend(fontsize=8, loc="lower right"); ax.set_title("EMT bus-voltage difference from the two references", fontsize=10)
    save(fig, "fig03_voltage_error")

# ---------------------------------------------------------------- 4 fixed load test
def fig_fixed_load():
    r = load_json("fixed_load_test.json"); s = load_json("fixed_load_settle.json")
    if not r: return
    fig, axs = plt.subplots(1, 2, figsize=(6.6, 2.9))
    ax = axs[0]
    for exp, col, lab, mk in ((0, C["blue"], "exponent 0 (constant power)", "o"), (2, C["orange"], "exponent 2 (constant impedance)", "s")):
        pts = sorted([(v["Vpu"][0], v["P_MW"] * 1e3) for k, v in r.items() if v["NP"] == exp])
        ax.plot([p[0] for p in pts], [p[1] for p in pts], color=col, marker=mk, ms=6, lw=2, label=lab)
    vv = np.linspace(0.88, 1.02, 50); P0 = r["exp2_V1.00"]["P_set"] * 1e3
    ax.plot(vv, P0 * vv ** 2, color=C["orange"], lw=0.8, ls=":", label="P₀·V² (theory)")
    ax.axhline(P0, color=C["blue"], lw=0.8, ls=":", label="P₀ setpoint")
    ax.set_xlabel("terminal voltage (pu)"); ax.set_ylabel("three-phase P drawn (kW)"); ax.legend(fontsize=7, loc="center left")
    ax.set_title("Master-library fixed load, bus 3 residential", fontsize=9)
    ax = axs[1]
    if s:
        for k, col in (("exp0_V0.90_3s_50us", C["blue"]), ("exp0_V0.90_1s_12.5us", C["aqua"])):
            if k in s:
                ax.plot([w[0] for w in s[k]], [w[4] for w in s[k]], color=col, marker="o", ms=3, lw=1.5, label=k.replace("exp0_V0.90_", "").replace("_", " "))
        ax.axhline(0, color=C["ink"], lw=0.8); ax.set_ylim(-0.2, 1.0)
        ax.set_xlabel("time (s)"); ax.set_ylabel("P error vs setpoint (%)"); ax.legend(fontsize=7)
        ax.set_title("Constant-power bias vs time and step", fontsize=9)
    save(fig, "fig04_fixed_load")

# ---------------------------------------------------------------- 5/6 short circuit
def fig_short_circuit():
    nl = load_json("sc_validation_noload.json"); ld = load_json("sc_validation.json")
    if not nl: return
    keys = ["sc_3ph_b1", "sc_1ph_b1", "sc_3ph_b11", "sc_1ph_b11"]
    labels = ["3-ph, bus 1", "1-ph, bus 1", "3-ph, bus 11", "1-ph, bus 11"]
    fig, axs = plt.subplots(1, 2, figsize=(6.6, 2.9), gridspec_kw=dict(width_ratios=[1.3, 1]))
    ax = axs[0]; x = np.arange(4); w = 0.26
    ax.bar(x - w, [nl[k]["I_hand_kA"] for k in keys], w, color=C["grey"], label="hand Thevenin (no load)")
    ax.bar(x, [nl[k]["I_emt_kA"] for k in keys], w, color=C["blue"], label="EMT, loads at 0.1 %")
    if ld: ax.bar(x + w, [ld[k]["I_emt_kA"] for k in keys], w, color=C["orange"], label="EMT, benchmark loads")
    for i, k in enumerate(keys):
        ax.annotate("%+.2f %%" % nl[k]["err_pct"], (i, nl[k]["I_emt_kA"]), xytext=(0, 3), textcoords="offset points", ha="center", fontsize=7)
    ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=8); ax.set_ylabel("fault current, fundamental (kA rms)")
    ax.legend(fontsize=7); ax.set_title("Bolted faults: EMT vs hand calculation", fontsize=9)
    ax = axs[1]
    t, ch = read_outputs(os.path.join(ROOT, "pscad", "tests", "sc", "sc_cases_noload"), "sc_cases_noload")
    if t is not None:
        m = (t >= 0.46) & (t <= 0.62)
        ax.plot(t[m] * 1e3, ch["If_A"][m], color=C["blue"], lw=1.2, label="fault current, phase A")
        ax.plot(t[m] * 1e3, ch["V_B11_A"][m] / 10, color=C["orange"], lw=1.0, label="bus 11 V_A (kV / 10)")
        ax.set_xlabel("time (ms)"); ax.set_ylabel("kA, kV/10"); ax.legend(fontsize=7, loc="upper right")
        ax.set_title("1-ph fault at bus 11, no load, waveforms", fontsize=9)
    else:
        ax.axis("off")
    save(fig, "fig05_short_circuit")

# ---------------------------------------------------------------- 7 impedance scan
def fig_impedance_scan():
    e = load_json("fscan_b11_emt.json")
    if not e: return
    import fscan_reference as FR
    fs = np.arange(60, 3501, 10.0)
    zz = np.array([FR.z_ag(11, f)[0] for f in fs])
    fe = sorted(float(k) for k in e)
    ze = [e[str(f)]["Zmag"] if str(f) in e else e[str(int(f))]["Zmag"] for f in fe]
    ae = [(e[str(f)]["Zang"] if str(f) in e else e[str(int(f))]["Zang"]) - 360 * f * 20e-6 for f in fe]
    fig, axs = plt.subplots(2, 1, figsize=(6.4, 4.6), sharex=True)
    axs[0].plot(fs, np.abs(zz), color=C["grey"], lw=2, label="analytic sequence networks")
    axs[0].plot(fe, ze, "o", color=C["blue"], ms=6, label="PSCAD EMT, 20 µs, 1-ph injection")
    axs[0].set_ylabel("|Z_A-G| (Ω)"); axs[0].legend(fontsize=8); axs[0].set_title("Phase-to-ground driving-point impedance at bus 11", fontsize=10)
    axs[1].plot(fs, np.degrees(np.angle(zz)), color=C["grey"], lw=2)
    axs[1].plot(fe, ae, "o", color=C["blue"], ms=6)
    axs[1].set_ylabel("angle (°)"); axs[1].set_xlabel("frequency (Hz)")
    for h, lab in ((250, "5th"), (350, "7th"), (550, "11th"), (650, "13th")):
        axs[0].axvline(h, color="#d9d8d3", lw=0.8, zorder=0); axs[0].text(h + 5, axs[0].get_ylim()[1] * 0.93, lab, fontsize=7, color=C["grey"])
    save(fig, "fig07_impedance_scan")

# ---------------------------------------------------------------- 8 variants
def fig_variants():
    a = load_json("validation_cigre_mv_bias.json"); b12 = load_json("validation_radial_12p5us.json"); m = load_json("validation_meshed.json")
    if not (a and m): return
    rows = lambda v: [r for r in v["buses"] if r["bus"] > 0]
    b = [r["bus"] for r in rows(a)]; base = [r["emt_kv"] for r in rows(a)]
    fig, axs = plt.subplots(1, 2, figsize=(6.6, 3.0))
    ax = axs[0]
    f1 = [r for r in rows(a) if r["bus"] <= 11]; f1m = [r for r in rows(m) if r["bus"] <= 11]
    ax.plot([r["bus"] for r in f1], [r["emt_kv"] for r in f1], color=C["blue"], lw=2, marker="^", ms=4, label="radial (S1-S3 open)")
    ax.plot([r["bus"] for r in f1m], [r["emt_kv"] for r in f1m], color=C["orange"], lw=2, marker="s", ms=4, label="meshed (S2, S3 closed)")
    ax.plot([r["bus"] for r in f1m], [r["pp_kv"] for r in f1m], color=C["grey"], lw=1, marker="o", ms=3, ls=":", label="pandapower, meshed")
    ax.set_xticks([r["bus"] for r in f1]); ax.set_xlabel("bus (feeder 1)"); ax.set_ylabel("line-to-line voltage (kV)"); ax.legend(fontsize=7)
    ax.set_title("Closing the loops lifts the feeder end", fontsize=9)
    ax = axs[1]
    if b12:
        d12 = [(r["emt_kv"] / v - 1) * 100 for r, v in zip(rows(b12), base)]
        ax.plot(b, d12, color=C["aqua"], marker="v", ms=4, lw=1.5, label="radial, 12.5 us vs 50 us")
    ax.plot(b, [r["err_pp_pct"] for r in rows(a)], color=C["blue"], marker="^", ms=4, lw=1.5, label="radial 50 us vs pandapower")
    ax.plot(b, [r["err_pp_pct"] for r in rows(m)], color=C["orange"], marker="s", ms=4, lw=1.5, label="meshed 50 us vs pandapower")
    ax.axhline(0, color=C["ink"], lw=0.8); ax.set_ylim(-0.06, 0.06)
    ax.set_xticks(b); ax.set_xlabel("bus"); ax.set_ylabel("voltage difference (%)"); ax.legend(fontsize=7, loc="lower left")
    ax.set_title("Differences stay below 0.04 %", fontsize=9)
    save(fig, "fig08_variants")

# ---------------------------------------------------------------- 9 transformer currents and grid power
def fig_transformers():
    v = load_json("validation_cigre_mv_bias.json")
    if not v: return
    tb = {br["to_bus"]: br for br in DATA["powerflow_reference"].get("branches", []) if str(br.get("from_bus")) == "0"}
    ids = list(v["trafo_emt_A"].keys())
    fig, ax = plt.subplots(figsize=(4.2, 2.8)); x = np.arange(len(ids)); w = 0.26
    tbv = [tb.get(str(t["to_bus"]), tb.get(t["to_bus"], {})).get("I_rms_A", {}).get("A", np.nan) for t in DATA["transformers"]]
    ax.bar(x - w, tbv, w, color=C["grey"], label="brochure Table 9.6")
    ax.bar(x, [v["trafo_emt_A"][i] for i in ids], w, color=C["blue"], label="PSCAD EMT")
    ax.set_xticks(x); ax.set_xticklabels(ids); ax.set_ylabel("LV current (A rms)"); ax.legend(fontsize=7)
    ax.set_title("Transformer secondary currents", fontsize=9)
    save(fig, "fig09_transformer_currents")

# ---------------------------------------------------------------- 10 start-up waveforms of the base run
def fig_startup():
    t, ch = read_outputs(os.path.join(ROOT, "pscad", "CIGRE-MV-PSCAD"), "CIGRE_MV_PSCAD")
    if t is None: return
    fig, axs = plt.subplots(2, 1, figsize=(6.4, 4.4))
    m = t <= 0.12
    for ph, col in (("A", C["blue"]), ("B", C["orange"]), ("C", C["aqua"])):
        axs[0].plot(t[m] * 1e3, ch["V_B11_" + ph][m], color=col, lw=0.9, label="phase " + ph)
    axs[0].set_ylabel("bus 11 voltage (kV)"); axs[0].set_xlabel("time (ms)")
    axs[0].legend(fontsize=7, ncol=3, loc="upper left"); axs[0].set_ylim(-19, 21)
    axs[0].set_title("Base run start-up: 50 ms source ramp, then power settling", fontsize=10)
    m = t <= 0.5
    axs[1].plot(t[m] * 1e3, ch["P_grid"][m], color=C["blue"], lw=1.2, label="P grid (MW)")
    axs[1].plot(t[m] * 1e3, ch["Q_grid"][m], color=C["orange"], lw=1.2, label="Q grid (MVAr)")
    axs[1].axvline(200, color=C["grey"], lw=0.8, ls=":"); axs[1].text(205, 28, "loads switch to constant-P law\n(after 10 cycles)", fontsize=7, color=C["grey"])
    axs[1].set_xlabel("time (ms)"); axs[1].set_ylabel("MW, MVAr"); axs[1].legend(fontsize=7, loc="center right")
    save(fig, "fig10_startup")

if __name__ == "__main__":
    for f in (fig_voltage_profile, fig_fixed_load, fig_short_circuit, fig_impedance_scan, fig_variants, fig_transformers, fig_startup):
        try:
            f()
        except Exception as ex:
            print("FAILED", f.__name__, repr(ex))
