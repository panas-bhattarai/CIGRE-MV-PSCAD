"""Short-circuit validation runs for CIGRE-MV-PSCAD (Python 3.7 + mhi.pscad + numpy).
Four cases: 3ph and 1ph (A-G) bolted faults at bus 1 and bus 11, applied at 0.5 s for 0.3 s.
Fault current fundamental rms is fitted over 0.7-0.8 s and compared with a hand Thevenin
calculation using the same model definitions (tap-scaled transformer impedance, EMF 110.48 kV)."""
import os, sys, math, json, time, glob
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pscad_session import pscad_session
import build_cigre_mv as B

OUT = os.path.join(B.ROOT, "pscad", "tests", "sc")
W = B.W
d = json.load(open(B.DATA, encoding="utf-8"))

def phasor(t, x, t0, t1):
    m = (t >= t0) & (t < t1)
    A = np.column_stack([np.cos(W * t[m]), np.sin(W * t[m]), np.ones(m.sum())])
    c, *_ = np.linalg.lstsq(A, x[m], rcond=None)
    return complex(c[0], -c[1]) / math.sqrt(2)

def read(case_dir, name):
    inf = glob.glob(os.path.join(case_dir, name + "*", name + ".inf"))[0]
    names = [ln.split('Desc="')[1].split('"')[0] for ln in open(inf) if "Desc=" in ln]
    outs = sorted(glob.glob(os.path.join(os.path.dirname(inf), name + "_*.out")))
    cols, t = [], None
    for o in outs:
        a = np.loadtxt(o, skiprows=1)
        if t is None: t = a[:, 0]
        cols.append(a[:, 1:])
    return t, dict(zip(names, np.hstack(cols).T))

def hand(bus, ftype):
    hv = d["hv_equivalent"]["network_specific"]; tr = d["transformers"][0]
    v2 = 20 * (1 + tr["tap_setting_used_in_power_flow"]["secondary_pct"] / 100)
    zs = 110 ** 2 / hv["short_circuit_power_MVA"]; xs = zs / math.sqrt(1 + hv["R_over_X"] ** 2); rs = hv["R_over_X"] * xs
    k2 = (v2 / 110) ** 2
    Zs1 = complex(rs, xs) * k2
    zb = v2 ** 2 / 25; Zt = complex(0.001 * zb, 0.12 * zb)
    E = B.HV_EMF_KV / math.sqrt(3) * (v2 / 110)
    # radial path from bus 1 to the fault bus (S1-S3 open)
    path = {1: [], 11: [1, 2, 12, 8, 9, 10]}[bus]
    segs = {l["segment"]: l for l in d["lines"]}
    Zl1 = sum(complex(segs[s]["R1_ohm_per_km"], segs[s]["X1_ohm_per_km"]) * segs[s]["length_km"] for s in path) if path else 0j
    Zl0 = sum(complex(segs[s]["R0_ohm_per_km"], segs[s]["X0_ohm_per_km"]) * segs[s]["length_km"] for s in path) if path else 0j
    Z1 = Zs1 + Zt + Zl1
    Z0 = Zt + Zl0            # delta HV winding blocks the upstream zero-sequence path
    if ftype == "3ph":
        return E / abs(Z1), dict(Z1=[Z1.real, Z1.imag], E_ph_kV=E)
    return 3 * E / abs(2 * Z1 + Z0), dict(Z1=[Z1.real, Z1.imag], Z0=[Z0.real, Z0.imag], E_ph_kV=E)

import argparse
ap = argparse.ArgumentParser(); ap.add_argument("--load_scale", type=float, default=1.0); ap.add_argument("--np", type=float, default=0.0)
ap.add_argument("--tag", default=""); a = ap.parse_args()
CASES = [(1, "3ph"), (11, "3ph"), (1, "1ph"), (11, "1ph")]
res = {}
name = "sc_cases" + a.tag; cdir = os.path.join(OUT, name)
with pscad_session() as pscad:
    t0 = time.time()
    prj = B.build(pscad, dt=50.0, dur=1.0, out_dir=cdir, name=name,
                  fault=dict(bus=1, type="3ph", tf=0.5, df=0.3), load_scale=a.load_scale, np_=a.np, nq=a.np, log=lambda *x: None)
    print("build %.0fs" % (time.time() - t0), flush=True)
    main = prj.canvas("Main")
    flt = main.find("master:tpflt")
    # the fault's own node label is the one placed at the fault location (x=40, y=70 grid)
    labels = main.find_all("master:nodelabel")
    fault_label = None
    for c in labels:
        x, y = c.get_location()
        if (x, y) == (40, 70):
            fault_label = c
    if fault_label is None:
        raise SystemExit("could not locate the fault node label")
    for bus, ftype in CASES:
        label = "sc_%s_b%d" % (ftype, bus)
        fault_label.parameters(Name=B.bus_label(bus))
        flt.parameters(A=1, B=1 if ftype == "3ph" else 0, C=1 if ftype == "3ph" else 0)
        prj.save()
        t1 = time.time(); prj.run(); trun = time.time() - t1
        bad = [m for m in prj.messages() if m.status == "error"]
        if bad:
            print("ERROR", label, [m.text[:120] for m in bad]); print(str(prj.output())[-1500:]); continue
        t, ch = read(cdir, name)
        ia = phasor(t, ch["If_A"], 0.7, 0.8)
        ipk = float(np.max(np.abs(ch["If_A"][(t >= 0.5) & (t < 0.6)])))
        vpre = abs(phasor(t, ch["V_B%d_A" % bus], 0.4, 0.5)) * math.sqrt(3)
        ihand, info = hand(bus, ftype)
        res[label] = dict(bus=bus, type=ftype, I_emt_kA=abs(ia), I_hand_kA=ihand, err_pct=(abs(ia) / ihand - 1) * 100,
                          I_peak_kA=ipk, V_prefault_kV=vpre, hand=info,
                          I_B_kA=abs(phasor(t, ch["If_B"], 0.7, 0.8)), I_C_kA=abs(phasor(t, ch["If_C"], 0.7, 0.8)))
        r = res[label]
        print("%-10s  Ia_emt = %.4f kA  hand = %.4f kA  err = %+.2f %%  peak = %.3f kA  Vpre = %.2f kV  (Ib %.3f Ic %.3f)  run %.0fs" %
              (label, r["I_emt_kA"], ihand, r["err_pct"], ipk, vpre, r["I_B_kA"], r["I_C_kA"], trun), flush=True)
json.dump(res, open(os.path.join(B.ROOT, "results", "sc_validation%s.json" % a.tag), "w"), indent=1)
print("saved results/sc_validation%s.json" % a.tag)
