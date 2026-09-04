"""Build CIGRE-MV-PSCAD: a PSCAD 5 implementation of the CIGRE European MV benchmark
(CIGRE TB 575, 2014; Rudion et al. 2006) generated from data/cigre_mv_european_tb575.json
through the mhi.pscad automation library.

Every element is a master-library component. Electrical connections are made with
node labels named BUS_0 .. BUS_14 so the schematic is regular and the build is traceable.

Usage (Python 3.7 with mhi.pscad):
    python build_cigre_mv.py [--dt 50] [--dur 1.0] [--np 0] [--nq 0] [--run]
"""
import os, sys, math, json, argparse, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pscad_session import pscad_session

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
DATA = os.path.join(ROOT, "data", "cigre_mv_european_tb575.json")
OUT_DIR = ROOT   # the model lives at the repository root
NAME = "CIGRE_MV_PSCAD"
W = 2 * math.pi * 50.0

def bus_label(n):
    return "BUS_%d" % n

class Builder:
    def __init__(self, main, log=print):
        self.main = main
        self.log = log
        self.signals = []          # (signal name, group, units, max, min)

    # ---- helpers -------------------------------------------------------------
    def comp(self, defn, x, y, **params):
        c = self.main.create_component(defn, x, y)
        if params:
            c.parameters(**params)
        return c

    def wire(self, p1, p2):
        self.main.create_wire((p1[0], p1[1]), (p2[0], p2[1]))

    def port(self, c, name):
        p = c.port(name)
        if p is None:
            p = c.ports().get(name)
        if p is None:
            raise RuntimeError("component has no port %r; ports: %s" % (name, list(c.ports().keys())))
        return (p.x, p.y)

    def label_at(self, c, portname, label, dx=0, dy=0):
        """Attach a node label to a component port via a short wire."""
        px, py = self.port(c, portname)
        lx, ly = px + dx, py + dy
        self.comp("master:nodelabel", lx, ly, Name=label)
        if (dx, dy) != (0, 0):
            self.wire((px, py), (lx, ly))

    def ground_at(self, c, portname, dx=0, dy=2):
        px, py = self.port(c, portname)
        g = self.comp("master:ground", px + dx, py + dy)
        self.wire((px, py), (px + dx, py + dy))
        return g

    def record(self, sig, group, units, vmax, vmin):
        self.signals.append((sig, group, units, vmax, vmin))

    # ---- model sections ------------------------------------------------------
    def source_and_transformers(self, d, x0, y0, tap_scale, hv_ev=None):
        hv = d["hv_equivalent"]["network_specific"]
        vkv = hv["nominal_voltage_kV"]
        z = vkv ** 2 / hv["short_circuit_power_MVA"]
        rx = hv["R_over_X"]
        xohm = z / math.sqrt(1 + rx ** 2)
        rohm = rx * xohm
        src = self.comp("master:source3R", x0 + 6, y0, Name="HV_Grid", MVA=hv["short_circuit_power_MVA"],
                        Vm=vkv, F=50.0, Tc=0.05, Ideal=0, ZSeq=0, Imp=0, View=1,
                        R1p=rohm, X1p=xohm, P="P_grid", Q="Q_grid")
        # The brochure holds bus 0 at exactly 110 kV (slack). The Thevenin EMF behind the
        # 5000 MVA equivalent is therefore slightly higher than 110 kV; hv_ev sets it.
        cv = self.comp("master:const", x0, y0 - 4, Name="HV_EMF_kV", Value=float(hv_ev or vkv), Dim=1)
        cp = self.comp("master:const", x0 + 5, y0 - 7, Name="HV_deg", Value=0.0, Dim=1)
        self.wire(self.port(cv, "OUT"), self.port(src, "EV"))
        self.wire(self.port(cp, "OUT"), self.port(src, "EP"))
        self.label_at(src, "N3", bus_label(0), dx=2)
        self.record("P_grid", "Source", "MW", 60, -60); self.record("Q_grid", "Source", "MVAr", 30, -30)

        for k, t in enumerate(d["transformers"]):
            y = y0 + 8 + 8 * k
            R = t["Z_ohm_ref_V2"]["R"]; X = t["Z_ohm_ref_V2"]["X"]
            zb = t["V2_kV"] ** 2 / t["S_rated_MVA"]
            tap = t["tap_setting_used_in_power_flow"]["secondary_pct"] * tap_scale / 100.0
            tr = self.comp("master:xfmr-3p2w", x0 + 8, y, Name=t["id"], Tmva=t["S_rated_MVA"], f=50.0,
                           YD1=1, YD2=0, Lead=1, Xl=X / zb, CuL=R / zb, NLL=0.0, Ideal=0, Tap=0,
                           View=1, V1=t["V1_kV"], V2=t["V2_kV"] * (1 + tap), Enab=0,
                           ILA2="I_%s_A" % t["id"], ILB2="I_%s_B" % t["id"], ILC2="I_%s_C" % t["id"])
            self.log("  %s ports: %s" % (t["id"], list(tr.ports().keys())))
            self.label_at(tr, "N1", bus_label(t["from_bus"]), dx=-2)
            self.label_at(tr, "N2", bus_label(t["to_bus"]), dx=2)
            # ground the neutral of the star (Y) winding only; winding 1 is delta
            self.ground_at(tr, "G2")
            for ph in "ABC":
                self.record("I_%s_%s" % (t["id"], ph), "Transformer LV currents", "kA", 1.0, -1.0)

    def lines(self, d, x0, y0):
        sw = {s["line_segment"]: s for s in d["switches"]}
        for i, l in enumerate(d["lines"]):
            y = y0 + 4 * i
            R1, X1, B1 = l["R1_ohm_per_km"], l["X1_ohm_per_km"], l["B1_uS_per_km"]
            R0, X0, B0 = l["R0_ohm_per_km"], l["X0_ohm_per_km"], l["B0_uS_per_km"]
            name = "L%02d_%d_%d" % (l["segment"], l["from_bus"], l["to_bus"])
            ln = self.comp("master:newpi", x0 + 8, y, Name=name, PU=4, Config=1, F=50.0,
                           len=l["length_km"] * 1000.0, Estim=0, View=2,
                           Rp2=R1 / 1000.0, Lp=X1 / W / 1000.0, Cp=B1 / W / 1000.0,
                           Rz2=R0 / 1000.0, Lz=X0 / W / 1000.0, Cz=B0 / W / 1000.0)
            if l["segment"] in sw:
                s = sw[l["segment"]]
                br = self.comp("master:breaker3", x0 + 2, y, NAME=s["id"], View=1, ROFF=1.0e6, RON=0.005,
                               BOpen1=2, BOpen2=2, BOpen3=2)
                self.label_at(br, "N2", bus_label(l["from_bus"]), dx=-2)
                self.wire(self.port(br, "N1"), self.port(ln, "N1"))
                # breaker state signal: 1 = open, 0 = closed (PSCAD breaker convention)
                sc = self.comp("master:const", x0 - 8, y - 2, Name=s["id"] + "_open", Value=1.0, Dim=1)
                ox, oy = self.port(sc, "OUT")
                self.comp("master:datalabel", ox + 2, oy, Name=s["id"])
                self.wire((ox, oy), (ox + 2, oy))
            else:
                self.label_at(ln, "N1", bus_label(l["from_bus"]), dx=-2)
            self.label_at(ln, "N2", bus_label(l["to_bus"]), dx=2)

    def bus_stations(self, d, x0, y0, np_, nq, load_scale):
        loads = {ld["bus"]: ld for ld in d["loads"]}
        vlg = d["system"]["nominal_voltage_kV"] / math.sqrt(3)
        for n in range(0, 15):
            y = y0 + 10 * n
            kv = 110.0 if n == 0 else d["system"]["nominal_voltage_kV"]
            self.comp("master:nodelabel", x0, y, Name=bus_label(n))
            bo = self.comp("master:breakout", x0 + 2, y, Com=0, Dis=1)
            self.wire((x0, y), self.port(bo, "N"))
            for pi, ph in enumerate("ABC"):
                pname = "N%d" % (pi + 1)
                px, py = self.port(bo, pname)
                x = px + 3
                self.wire((px, py), (x, py))
                vm = self.comp("master:voltmetergnd", x, py, Name="V_B%d_%s" % (n, ph))
                self.record("V_B%d_%s" % (n, ph), "Bus voltages", "kV L-G", kv, -kv)
                if n in loads:
                    xl = x
                    for sec, tag in (("residential", "R"), ("commercial_industrial", "CI")):
                        sd = loads[n][sec]
                        if not sd["S_kVA"]:
                            continue
                        xl += 4
                        self.wire((xl - 4, py), (xl, py))
                        ld = self.comp("master:fixed_load", xl, py + 1, Name="Load_%s%d_%s" % (tag, n, ph),
                                       PO=sd["P_kW_derived"] / 3000.0 * load_scale,
                                       QO=sd["Q_kvar_derived"] / 3000.0 * load_scale,
                                       VBO=vlg, VPU=1.0, PQdef=0, Parts=1, NP=np_, NQ=nq,
                                       FR=50.0, NCYC=10, Dtls=0)

    def fault(self, bus, ftype, tf, df, x0, y0, ron=0.001):
        """Timed fault at a bus: ftype '3ph' (ABC-G) or '1ph' (A-G)."""
        self.comp("master:nodelabel", x0, y0, Name=bus_label(bus))
        ph = dict(A=1, B=1, C=1) if ftype == "3ph" else dict(A=1, B=0, C=0)
        fl = self.comp("master:tpflt", x0 + 4, y0, Name="FLT_B%d" % bus, Ctype=0, Grnd=1, View=1,
                       RON=ron, ROFF=1.0e6, G=1, Ifla="If_A", Iflb="If_B", Iflc="If_C", **ph)
        self.wire((x0, y0), self.port(fl, "N"))
        tm = self.comp("master:tfault", x0 + 10, y0 - 4, TF=tf, DF=df, REP=0)
        # in single-line view the timed-fault input port is exposed as "IS"
        fport = "FT" if ("FT" in fl.ports() or fl.port("FT") is not None) else "IS"
        self.wire(self.port(tm, "Y"), self.port(fl, fport))
        for p in "ABC":
            self.record("If_" + p, "Fault current", "kA", 10, -10)

    def scan_source(self, bus, f, x0, y0, vm_kv=1.0, r_ohm=2000.0):
        """Single-phase (A-G) injection for a frequency scan: AC voltage source of vm_kv at f Hz
        behind r_ohm, connected phase A of the bus to ground. Z(f) = V_A(f) / I(f) is evaluated in Python."""
        self.comp("master:nodelabel", x0, y0, Name=bus_label(bus))
        bo = self.comp("master:breakout", x0 + 2, y0, Com=0, Dis=1)
        self.wire((x0, y0), self.port(bo, "N"))
        src = self.comp("master:source_1", x0 + 8, y0 - 2, Name="SCAN", Type=1, Grnd=1, Spec=0, Cntrl=0, AC=1,
                        Vm=vm_kv, Tc=0.02, Ph=0.0, f=f, R=r_ohm, CUR="I_scan")
        pa = self.port(bo, "N1"); na = self.port(src, "NA")
        if tuple(pa) != tuple(na):
            self.wire(pa, na)
        self.record("I_scan", "Scan", "kA", 0.01, -0.01)

    def recorders(self, x0, y0):
        for k, (sig, group, units, vmax, vmin) in enumerate(self.signals):
            y = y0 + 2 * k
            self.comp("master:datalabel", x0, y, Name=sig)
            pg = self.comp("master:pgb", x0 + 4, y, Name=sig, Group=group, Units=units, Max=vmax, Min=vmin)
            self.wire((x0, y), self.port(pg, "Signl"))

HV_EMF_KV = 110.48   # Thevenin EMF giving 110.0 kV at bus 0 for the benchmark load (calibrated 2026-09-04)

def build(pscad, dt=50.0, dur=1.0, np_=0, nq=0, tap_scale=1.0, load_scale=1.0, hv_ev=HV_EMF_KV, out_dir=OUT_DIR, name=NAME,
          fault=None, scan=None, log=print):
    """fault: None or dict(bus=int, type='3ph'|'1ph', tf=float, df=float)"""
    d = json.load(open(DATA, encoding="utf-8"))
    os.makedirs(out_dir, exist_ok=True)
    prj = pscad.create_case(name, folder=out_dir)
    prj.parameters(time_duration=dur, time_step=dt, sample_step=dt, PlotType="OUT",
                   output_filename=name + ".out",
                   description="CIGRE-MV-PSCAD: PSCAD implementation of the CIGRE European MV benchmark "
                               "(CIGRE TB 575, 2014; Rudion et al. 2006). Independent implementation, "
                               "not a CIGRE or MHI publication. Generated by build_cigre_mv.py.")
    main = prj.canvas("Main")
    b = Builder(main, log)
    log("source and transformers"); b.source_and_transformers(d, 4, 8, tap_scale, hv_ev)
    log("lines"); b.lines(d, 40, 4)
    log("bus stations"); b.bus_stations(d, 4, 40, np_, nq, load_scale)
    if fault:
        log("fault"); b.fault(fault["bus"], fault["type"], fault["tf"], fault["df"], 40, 70)
    if scan:
        log("scan source"); b.scan_source(scan["bus"], scan["f"], 40, 80)
    log("recorders"); b.recorders(80, 4)
    prj.save()
    log("saved %s (%d recorded signals)" % (os.path.join(out_dir, name + ".pscx"), len(b.signals)))
    return prj

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dt", type=float, default=50.0)
    ap.add_argument("--dur", type=float, default=1.0)
    ap.add_argument("--np", type=float, default=0.0)
    ap.add_argument("--nq", type=float, default=0.0)
    ap.add_argument("--hv_ev", type=float, default=HV_EMF_KV)
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    with pscad_session() as pscad:
        prj = build(pscad, dt=a.dt, dur=a.dur, np_=a.np, nq=a.nq, hv_ev=a.hv_ev)
        if a.run:
            t0 = time.time(); prj.run(); print("run finished in %.1fs" % (time.time() - t0), flush=True)
            msgs = prj.messages()
            bad = [m for m in msgs if m.status != "normal"]
            for m in bad[:30]:
                print("  MSG", m.status, m.text[:160], flush=True)
            if any(m.status == "error" for m in bad):
                print(str(prj.output())[-2500:])
                raise SystemExit("errors")
