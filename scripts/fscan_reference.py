"""Analytic frequency scan reference for CIGRE-MV-PSCAD (Python 3.11, numpy only).
Builds the positive- and zero-sequence nodal admittance matrices at each frequency from the
data file (lumped PI lines, transformer leakage, grid Thevenin, loads as parallel R-L sized at
nominal voltage = exponent-2 fixed loads) and returns the phase-A-to-ground driving-point
impedance Z_AG = (2 Z1 + Z0) / 3 at a bus.  Compares with results/fscan_b<bus>_emt.json if present."""
import os, sys, math, json, argparse
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, ".."))
d = json.load(open(os.path.join(ROOT, "data", "cigre_mv_european_tb575.json"), encoding="utf-8"))
HV_EMF = 110.48

def seq_impedance(bus, f, seq, load_scale=1.0):
    w = 2 * math.pi * f
    sw_segments = [s["line_segment"] for s in d["switches"]]
    n = 15 + len(sw_segments); Y = np.zeros((n, n), dtype=complex)   # extra dangling nodes for the open ends of tie lines
    def add(i, j, y):
        Y[i, i] += y; Y[j, j] += y; Y[i, j] -= y; Y[j, i] -= y
    def shunt(i, y):
        Y[i, i] += y
    # grid equivalent at bus 0 (positive sequence only; zero sequence blocked by delta HV winding anyway)
    hv = d["hv_equivalent"]["network_specific"]
    zs = 110 ** 2 / hv["short_circuit_power_MVA"]; xs = zs / math.sqrt(1 + hv["R_over_X"] ** 2); rs = hv["R_over_X"] * xs
    if seq == 1:
        shunt(0, 1 / complex(rs, xs * f / 50))
    # transformers: leakage referred to LV with tapped ratio; positive seq: series between bus 0 (referred) and LV bus
    for tr in d["transformers"]:
        v2 = 20 * (1 + tr["tap_setting_used_in_power_flow"]["secondary_pct"] / 100)
        zb = v2 ** 2 / 25; zt = complex(0.001 * zb, 0.12 * zb * f / 50)
        k2 = (v2 / 110) ** 2   # refer the 110 kV side to the LV side
        if seq == 1:
            add(0, tr["to_bus"], 1 / zt)      # bus 0 handled in LV-referred ohms (see below)
        else:
            shunt(tr["to_bus"], 1 / zt)       # zero sequence: LV star grounded, delta HV -> path to ground only
    sw = {seg: 15 + k for k, seg in enumerate(sw_segments)}
    for l in d["lines"]:
        L = l["length_km"]
        if seq == 1:
            z = complex(l["R1_ohm_per_km"], l["X1_ohm_per_km"] * f / 50) * L; b = l["B1_uS_per_km"] * 1e-6 * f / 50 * L
        else:
            z = complex(l["R0_ohm_per_km"], l["X0_ohm_per_km"] * f / 50) * L; b = l["B0_uS_per_km"] * 1e-6 * f / 50 * L
        # an open tie line stays connected at its to_bus end in the EMT model; its from_bus end is
        # behind the open breaker, i.e. a dangling node
        fb = sw.get(l["segment"], l["from_bus"])
        add(fb, l["to_bus"], 1 / z); shunt(fb, 1j * b / 2); shunt(l["to_bus"], 1j * b / 2)
    # loads: parallel R and L per phase sized at 20 kV (exponent-2 fixed load); same in all sequences (grounded star)
    for ld in d["loads"]:
        for sec in ("residential", "commercial_industrial"):
            sd = ld[sec]
            if sd["S_kVA"]:
                P = sd["P_kW_derived"] / 1e3 * load_scale; Q = sd["Q_kvar_derived"] / 1e3 * load_scale
                R = 400.0 / P; X = 400.0 / Q * f / 50
                shunt(ld["bus"], 1 / R + 1 / (1j * X))
    if seq == 1:
        # bus 0 is in 110 kV ohms for the grid shunt but the transformer branch above is in LV ohms:
        # rescale the grid shunt admittance to LV-referred ohms using TR1's ratio (both transformers share bus 0)
        v2 = 20 * (1 + d["transformers"][0]["tap_setting_used_in_power_flow"]["secondary_pct"] / 100)
        Y[0, 0] = Y[0, 0] - 1 / complex(rs, xs * f / 50) + 1 / (complex(rs, xs * f / 50) * (v2 / 110) ** 2)
    Y += np.eye(n) * 1e-12   # keep isolated nodes (bus 0 in zero sequence) non-singular
    Z = np.linalg.inv(Y)
    return Z[bus, bus]

def z_ag(bus, f, **kw):
    z1 = seq_impedance(bus, f, 1, **kw); z0 = seq_impedance(bus, f, 0, **kw)
    return (2 * z1 + z0) / 3, z1, z0

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--bus", type=int, default=11); a = ap.parse_args()
    emt_path = os.path.join(ROOT, "results", "fscan_b%d_emt.json" % a.bus)
    emt = json.load(open(emt_path)) if os.path.exists(emt_path) else {}
    freqs = sorted(float(k) for k in emt) if emt else [120, 180, 270, 330, 450, 650, 850, 1150, 1550, 2050, 2950]
    out = {}
    DT = 20e-6   # scan time step; PSCAD exports the source current one step after the voltage
    print("%8s %10s %8s | %10s %8s %8s | %7s %7s" % ("f Hz", "|Z| calc", "ang", "|Z| EMT", "ang raw", "ang cor", "dZ %", "dang"))
    for f in freqs:
        z, z1, z0 = z_ag(a.bus, f)
        e = emt.get(str(f)) or emt.get(str(int(f)))
        dz = (e["Zmag"] / abs(z) - 1) * 100 if e else float("nan")
        angc = (e["Zang"] - 360.0 * f * DT) if e else float("nan")
        angcalc = math.degrees(math.atan2(z.imag, z.real))
        print("%8.1f %10.3f %8.2f | %10s %8s %8s | %7.2f %7.2f" % (f, abs(z), angcalc,
              ("%.3f" % e["Zmag"]) if e else "-", ("%.2f" % e["Zang"]) if e else "-", ("%.2f" % angc) if e else "-", dz, angc - angcalc))
        if e: e["Zang_corrected"] = angc
        out[str(f)] = dict(f=f, Zmag=abs(z), Zang=math.degrees(math.atan2(z.imag, z.real)), Z1=[z1.real, z1.imag], Z0=[z0.real, z0.imag], emt=e, dZ_pct=dz)
    # resonance search
    fs = np.arange(50, 5001, 10.0); zz = [abs(z_ag(a.bus, f)[0]) for f in fs]
    k = int(np.argmax(zz)); print("first parallel resonance (calc): %.0f Hz, |Z| = %.1f ohm" % (fs[k], zz[k]))
    out["resonance_calc"] = dict(f=float(fs[k]), Zmag=float(zz[k]))
    json.dump(out, open(os.path.join(ROOT, "results", "fscan_b%d_reference.json" % a.bus), "w"), indent=1)
