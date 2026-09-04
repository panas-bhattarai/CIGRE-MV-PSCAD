"""Frequency scan of the phase-A-to-ground driving-point impedance at a bus (Python 3.7 + mhi.pscad).
One build with a single-phase injection source; frequency changed between runs."""
import os, sys, math, json, time, glob, argparse
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pscad_session import pscad_session
import build_cigre_mv as B

ap = argparse.ArgumentParser(); ap.add_argument("--bus", type=int, default=11); ap.add_argument("--np", type=float, default=2.0)
ap.add_argument("--freqs", default="120,180,270,330,450,650,850,1150,1550,2050,2950")
a = ap.parse_args()
FREQS = [float(x) for x in a.freqs.split(",")]
name = "fscan_b%d" % a.bus; cdir = os.path.join(B.ROOT, "pscad", "tests", "fscan", name)

def read(case_dir, name):
    inf = glob.glob(os.path.join(case_dir, name + "*", name + ".inf"))[0]
    names = [ln.split('Desc="')[1].split('"')[0] for ln in open(inf) if "Desc=" in ln]
    outs = sorted(glob.glob(os.path.join(os.path.dirname(inf), name + "_*.out")))
    cols, t = [], None
    for o in outs:
        d = np.loadtxt(o, skiprows=1)
        if t is None: t = d[:, 0]
        cols.append(d[:, 1:])
    return t, dict(zip(names, np.hstack(cols).T))

def tone(t, x, f, t0, t1):
    m = (t >= t0) & (t < t1); w = 2 * math.pi * f
    A = np.column_stack([np.cos(w * t[m]), np.sin(w * t[m]), np.cos(2*math.pi*50*t[m]), np.sin(2*math.pi*50*t[m]), np.ones(m.sum())])
    c, *_ = np.linalg.lstsq(A, x[m], rcond=None)
    return complex(c[0], -c[1])

res = {}
with pscad_session() as pscad:
    t0 = time.time()
    prj = B.build(pscad, dt=20.0, dur=0.6, out_dir=cdir, name=name, np_=a.np, nq=a.np,
                  scan=dict(bus=a.bus, f=FREQS[0]), log=lambda *x: None)
    print("build %.0fs" % (time.time() - t0), flush=True)
    src = prj.canvas("Main").find("master:source_1")
    for f in FREQS:
        src.parameters(f=f); prj.save()
        t1 = time.time(); prj.run()
        bad = [m for m in prj.messages() if m.status == "error"]
        if bad:
            print("ERROR", f, [m.text[:100] for m in bad]); continue
        t, ch = read(cdir, name)
        # choose a window that is an integer number of cycles of f and of 50 Hz: 0.4-0.6 s (0.2 s = 10 cycles of 50 Hz)
        V = tone(t, ch["V_B%d_A" % a.bus], f, 0.4, 0.6) * 1e3      # V
        I = tone(t, ch["I_scan"], f, 0.4, 0.6) * 1e3               # A (source current, +out of source into the bus?)
        Z = V / I
        res[str(f)] = dict(f=f, Zmag=abs(Z), Zang=math.degrees(math.atan2(Z.imag, Z.real)), Vmag=abs(V), Imag=abs(I))
        print("f = %7.1f Hz  |Z| = %9.3f ohm  angle = %7.2f deg  (|V| %.2f V, |I| %.4f A)  run %.0fs" % (f, abs(Z), res[str(f)]["Zang"], abs(V), abs(I), time.time() - t1), flush=True)
json.dump(res, open(os.path.join(B.ROOT, "results", "fscan_b%d_emt.json" % a.bus), "w"), indent=1)
print("saved")
