"""Standalone test of the PSCAD master-library fixed load (master:fixed_load).

Question: with voltage exponents NP = NQ = 0, does the load hold constant P and Q
when the terminal voltage is below nominal?  Exponent 2 (constant impedance) is run
as a control.  Load values: CIGRE MV bus 3 residential, 285 kVA at pf 0.97.

Builds the case from scratch through the mhi.pscad automation library, runs the
cases, and computes P/Q from the recorded waveforms in Python.
"""
import os, sys, glob, math, json, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pscad_session import pscad_session

HERE = os.path.dirname(os.path.abspath(__file__))
CASE_DIR = os.path.abspath(os.path.join(HERE, "..", "pscad", "tests", "fixed_load"))
NAME = "fixed_load_test"
os.makedirs(CASE_DIR, exist_ok=True)

# Bus 3 residential load, three-phase totals
S_KVA, PF = 285.0, 0.97
P3 = S_KVA * PF / 1e3                      # MW, 3-phase
Q3 = S_KVA * math.sqrt(1 - PF**2) / 1e3    # MVAr, 3-phase
VLL = 20.0                                 # kV
VLG = VLL / math.sqrt(3)

CASES = [  # (label, NP, NQ, source L-L kV)
    ("exp0_V1.00", 0, 0, 20.0),
    ("exp0_V0.90", 0, 0, 18.0),
    ("exp2_V1.00", 2, 2, 20.0),
    ("exp2_V0.90", 2, 2, 18.0),
]

def build(pscad):
    prj = pscad.create_case(NAME, folder=CASE_DIR)
    prj.parameters(time_duration=1.0, time_step=50.0, sample_step=50.0,
                   PlotType="OUT", output_filename=NAME + ".out",
                   description="Master-library fixed load test: exponent 0 vs 2")
    main = prj.canvas("Main")

    src = main.create_component("master:source3R", 10, 10)
    src.parameters(Name="Src", MVA=25.0, Vm=VLL, F=50.0, Tc=0.05, Ideal=0, ZSeq=0,
                   Imp=0, View=0, R1p=0.001, X1p=0.01, P="Psrc", Q="Qsrc")
    # source voltage magnitude (kV L-L) and phase (deg) come from constant blocks
    cv = main.create_component("master:const", 4, 6); cv.parameters(Name="SrcV", Value=VLL, Dim=1)
    cp = main.create_component("master:const", 9, 3); cp.parameters(Name="SrcPh", Value=0.0, Dim=1)
    ev, ep = src.port("EV"), src.port("EP")
    print("  EV port", (ev.x, ev.y), " EP port", (ep.x, ep.y), " const ports", list(cv.ports().keys()), flush=True)
    co = next(iter(cv.ports().values())); po = next(iter(cp.ports().values()))
    main.create_wire((co.x, co.y), (ev.x, ev.y))
    main.create_wire((po.x, po.y), (ep.x, ep.y))
    loads, amms, vms = [], [], []
    for i, ph in enumerate("ABC"):
        y = 10 + (i - 1) * 2                          # source ports A,B,C at y = 8,10,12
        sp = src.port(ph)
        am = main.create_component("master:ammeter", 16, y)
        am.parameters(Name="I" + ph)
        ld = main.create_component("master:fixed_load", 24, y + 1)   # IA port is 1 grid above origin
        ld.parameters(Name="Load" + ph, PO=P3 / 3, QO=Q3 / 3, VBO=VLG, VPU=1.0, PQdef=0,
                      Parts=1, NP=0, NQ=0, FR=50.0, NCYC=10, Dtls=1)
        vm = main.create_component("master:voltmetergnd", 21, y)
        vm.parameters(Name="V" + ph)
        a1, a2 = am.port("N1"), am.port("N2")
        lp = ld.port("IA")
        vp = vm.port("N1")
        print(f"  phase {ph}: src({sp.x},{sp.y}) amm({a1.x},{a1.y})-({a2.x},{a2.y}) vm({vp.x},{vp.y}) load({lp.x},{lp.y})", flush=True)
        main.create_wire((sp.x, sp.y), (a1.x, a1.y))
        main.create_wire((a2.x, a2.y), (vp.x, vp.y))
        main.create_wire((vp.x, vp.y), (lp.x, lp.y))
        loads.append(ld); amms.append(am); vms.append(vm)

    # record channels: datalabel -> wire -> pgb
    for k, sig in enumerate(["VA", "VB", "VC", "IA", "IB", "IC", "Psrc", "Qsrc"]):
        y = 16 + 2 * k
        dl = main.create_component("master:datalabel", 30, y)
        dl.parameters(Name=sig)
        pg = main.create_component("master:pgb", 34, y)
        pg.parameters(Name=sig, Group="test", Max=1.0, Min=-1.0)
        sg = pg.port("Signl"); main.create_wire((30, y), (sg.x, sg.y))
    prj.save()
    return prj, cv, loads

def fundamental_pq(t, v, i, f=50.0, t0=0.8, t1=1.0):
    """Least-squares fundamental phasors over [t0,t1); returns P, Q (single phase) and Vrms."""
    m = (t >= t0) & (t < t1)
    w = 2 * math.pi * f
    A = np.column_stack([np.cos(w * t[m]), np.sin(w * t[m]), np.ones(m.sum())])
    cv, *_ = np.linalg.lstsq(A, v[m], rcond=None)
    ci, *_ = np.linalg.lstsq(A, i[m], rcond=None)
    V = complex(cv[0], -cv[1]); I = complex(ci[0], -ci[1])
    S = 0.5 * V * np.conj(I)           # peak phasors -> 0.5 factor
    return S.real, S.imag, abs(V) / math.sqrt(2)

def read_outputs():
    inf = glob.glob(os.path.join(CASE_DIR, NAME + "*", NAME + ".inf"))
    if not inf:
        raise FileNotFoundError("no .inf under " + CASE_DIR)
    inf = inf[0]
    names = []
    for line in open(inf):
        if "Desc=" in line:
            names.append(line.split('Desc="')[1].split('"')[0])
    outs = sorted(glob.glob(os.path.join(os.path.dirname(inf), NAME + "_*.out")))
    cols = []
    t = None
    for o in outs:
        d = np.loadtxt(o, skiprows=1)
        if t is None:
            t = d[:, 0]
        cols.append(d[:, 1:])
    data = np.hstack(cols)
    return t, dict(zip(names, data.T)), inf

def main():
    results = {}
    with pscad_session() as pscad:
        print("licensed:", pscad.licensed(), flush=True)
        prj, cv, loads = build(pscad)
        for label, NP, NQ, vkv in CASES:
            cv.parameters(Value=vkv)
            for ld in loads:
                ld.parameters(NP=NP, NQ=NQ, VPU=vkv / VLL)
            prj.save()
            t0 = time.time()
            prj.run()
            print(f"run {label} done in {time.time()-t0:.1f}s", flush=True)
            errs = [m for m in prj.messages() if m.status != "normal"]
            for m in errs[:8]:
                print("   MSG", m.status, m.text[:140], flush=True)
            if any(m.status == "error" for m in errs):
                try:
                    print("---- runtime output ----"); print(str(prj.output())[-3000:], flush=True)
                except Exception as e:
                    print("output() failed:", e, flush=True)
                raise SystemExit("build/run errors, see above")
            t, ch, inf = read_outputs()
            P = Q = 0.0; vr = []
            for ph in "ABC":
                p, q, v = fundamental_pq(t, ch["V" + ph], ch["I" + ph])   # kV * kA = MW
                P += p; Q += q; vr.append(v)
            Psrc = float(np.mean(ch["Psrc"][t >= 0.8])); Qsrc = float(np.mean(ch["Qsrc"][t >= 0.8]))
            results[label] = dict(NP=NP, NQ=NQ, Vsrc_kV=vkv, Vrms_LG_kV=vr, Vpu=[v / VLG for v in vr],
                                  P_MW=P, Q_MVAr=Q, P_set=P3, Q_set=Q3,
                                  P_err_pct=(P / P3 - 1) * 100, Q_err_pct=(Q / Q3 - 1) * 100,
                                  Psrc_MW=Psrc, Qsrc_MVAr=Qsrc)
            r = results[label]
            print(f"  {label}: V={r['Vpu'][0]:.4f} pu  P={P*1e3:.2f} kW ({r['P_err_pct']:+.2f}%)  "
                  f"Q={Q*1e3:.2f} kvar ({r['Q_err_pct']:+.2f}%)  src P={Psrc*1e3:.1f} kW Q={Qsrc*1e3:.1f} kvar", flush=True)
    out = os.path.join(HERE, "..", "results", "fixed_load_test.json")
    json.dump(results, open(out, "w"), indent=1)
    print("saved", os.path.abspath(out))

if __name__ == "__main__":
    main()
