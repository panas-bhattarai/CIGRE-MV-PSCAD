"""Follow-up: does the exponent-0 fixed load's +0.77 % P/Q offset settle with time or time step?"""
import os, sys, glob, math, json, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pscad_session import pscad_session
import test_fixed_load as T

def windows_pq(t, ch, width=0.2):
    rows = []
    for t0 in np.arange(0.2, t[-1] - width + 1e-9, width):
        P = Q = 0.0
        for ph in "ABC":
            p, q, v = T.fundamental_pq(t, ch["V" + ph], ch["I" + ph], t0=t0, t1=t0 + width)
            P += p; Q += q
        rows.append((t0, t0 + width, P * 1e3, Q * 1e3, (P / T.P3 - 1) * 100))
    return rows

out = {}
with pscad_session() as pscad:
    prj = pscad.load(os.path.join(T.CASE_DIR, T.NAME + ".pscx")) or pscad.project(T.NAME)
    prj = pscad.project(T.NAME)
    main = prj.canvas("Main")
    cv = main.find("master:const", Name="SrcV")
    loads = [main.find("master:fixed_load", Name="Load" + ph) for ph in "ABC"]
    for label, dur, dt in [("exp0_V0.90_3s_50us", 3.0, 50.0), ("exp0_V0.90_1s_12.5us", 1.0, 12.5)]:
        prj.parameters(time_duration=dur, time_step=dt, sample_step=dt)
        cv.parameters(Value=18.0)
        for ld in loads:
            ld.parameters(NP=0, NQ=0, VPU=0.9)
        prj.save()
        t0 = time.time(); prj.run(); print(f"run {label} in {time.time()-t0:.1f}s", flush=True)
        if any(m.status == "error" for m in prj.messages()):
            print(str(prj.output())[-1500:]); raise SystemExit("run error")
        t, ch, inf = T.read_outputs()
        rows = windows_pq(t, ch)
        out[label] = rows
        for r in rows:
            print(f"  {label} t={r[0]:.1f}-{r[1]:.1f}s  P={r[2]:.2f} kW  Q={r[3]:.2f} kvar  P err {r[4]:+.2f}%", flush=True)
json.dump(out, open(os.path.join(T.HERE, "..", "results", "fixed_load_settle.json"), "w"), indent=1)
