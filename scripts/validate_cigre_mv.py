"""Validate a CIGRE-MV-PSCAD run against (a) a pandapower load flow built from the same
data file and (b) the brochure's reference power flow (TB 575 Table 9.6).

Runs under Python 3.11 (needs numpy, pandapower). Reads the PSCAD .inf/.out exports.
Usage: python validate_cigre_mv.py [--case pscad/CIGRE-MV-PSCAD] [--t0 0.8 --t1 1.0]
"""
import os, sys, glob, math, json, argparse
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
DATA = os.path.join(ROOT, "data", "cigre_mv_european_tb575.json")
W = 2 * math.pi * 50.0

def read_outputs(case_dir, name):
    inf = glob.glob(os.path.join(case_dir, name + "*", name + ".inf"))[0]
    names = [ln.split('Desc="')[1].split('"')[0] for ln in open(inf) if "Desc=" in ln]
    outs = sorted(glob.glob(os.path.join(os.path.dirname(inf), name + "_*.out")))
    cols, t = [], None
    for o in outs:
        d = np.loadtxt(o, skiprows=1)
        if t is None:
            t = d[:, 0]
        cols.append(d[:, 1:])
    data = np.hstack(cols)
    return t, dict(zip(names, data.T))

def phasor(t, x, t0, t1):
    m = (t >= t0) & (t < t1)
    A = np.column_stack([np.cos(W * t[m]), np.sin(W * t[m]), np.ones(m.sum())])
    c, *_ = np.linalg.lstsq(A, x[m], rcond=None)
    return complex(c[0], -c[1]) / math.sqrt(2)      # rms phasor, cos reference

def pandapower_reference(d, load_scale=1.0, closed=()):
    import pandapower as pp
    net = pp.create_empty_network(f_hz=50, sn_mva=25)
    b = {0: pp.create_bus(net, 110, name="Bus 0")}
    for i in range(1, 15):
        b[i] = pp.create_bus(net, 20, name="Bus %d" % i)
    hv = d["hv_equivalent"]["network_specific"]
    pp.create_ext_grid(net, b[0], vm_pu=1.0, va_degree=0.0, s_sc_max_mva=hv["short_circuit_power_MVA"], rx_max=hv["R_over_X"])
    for tr in d["transformers"]:
        R, X = tr["Z_ohm_ref_V2"]["R"], tr["Z_ohm_ref_V2"]["X"]; zb = tr["V2_kV"] ** 2 / tr["S_rated_MVA"]
        tap = tr["tap_setting_used_in_power_flow"]["secondary_pct"]
        pp.create_transformer_from_parameters(net, b[tr["from_bus"]], b[tr["to_bus"]], sn_mva=tr["S_rated_MVA"],
            vn_hv_kv=tr["V1_kV"], vn_lv_kv=tr["V2_kV"], vkr_percent=R / zb * 100, vk_percent=math.hypot(R, X) / zb * 100,
            pfe_kw=0, i0_percent=0, shift_degree=-30, tap_side="lv", tap_neutral=0, tap_min=-16, tap_max=16,
            tap_step_percent=0.625, tap_pos=round(tap / 0.625), tap_changer_type="Ratio", name=tr["id"])
    sw = {s["line_segment"] for s in d["switches"] if s["id"] not in closed}
    for l in d["lines"]:
        pp.create_line_from_parameters(net, b[l["from_bus"]], b[l["to_bus"]], l["length_km"], l["R1_ohm_per_km"], l["X1_ohm_per_km"],
            l["B1_uS_per_km"] / W * 1e3, max_i_ka=0.2, r0_ohm_per_km=l["R0_ohm_per_km"], x0_ohm_per_km=l["X0_ohm_per_km"],
            c0_nf_per_km=l["B0_uS_per_km"] / W * 1e3, name="Seg %d" % l["segment"], in_service=(l["segment"] not in sw))
    for ld in d["loads"]:
        for sec in ("residential", "commercial_industrial"):
            sd = ld[sec]
            if sd["S_kVA"]:
                pp.create_load(net, b[ld["bus"]], p_mw=sd["P_kW_derived"] / 1e3 * load_scale, q_mvar=sd["Q_kvar_derived"] / 1e3 * load_scale)
    pp.runpp(net, init="flat")
    res = {}
    for i in range(15):
        res[i] = dict(v_kv=float(net.res_bus.vm_pu[b[i]] * net.bus.vn_kv[b[i]]), ang=float(net.res_bus.va_degree[b[i]]))
    trf = {tr["id"]: dict(i_lv_a=float(net.res_trafo.i_lv_ka[k] * 1e3), p_hv_mw=float(net.res_trafo.p_hv_mw[k]), q_hv_mvar=float(net.res_trafo.q_hv_mvar[k]))
           for k, tr in enumerate(d["transformers"])}
    return res, trf, float(net.res_ext_grid.p_mw[0]), float(net.res_ext_grid.q_mvar[0])

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", default=ROOT)
    ap.add_argument("--name", default="CIGRE_MV_PSCAD")
    ap.add_argument("--t0", type=float, default=0.8); ap.add_argument("--t1", type=float, default=1.0)
    ap.add_argument("--bias", type=float, default=1.0, help="fixed_load constant-power bias factor for the pandapower comparison")
    ap.add_argument("--out", default=os.path.join(ROOT, "results", "validation_cigre_mv.json"))
    ap.add_argument("--closed", default="", help="comma list of switches closed in the run, e.g. S2,S3")
    a = ap.parse_args()
    d = json.load(open(DATA, encoding="utf-8"))
    t, ch = read_outputs(a.case, a.name)
    print("samples: %d, t_end = %.3f s, channels = %d" % (len(t), t[-1], len(ch)))

    # EMT bus voltages
    emt = {}
    for n in range(15):
        va = phasor(t, ch["V_B%d_A" % n], a.t0, a.t1); vb = phasor(t, ch["V_B%d_B" % n], a.t0, a.t1); vc = phasor(t, ch["V_B%d_C" % n], a.t0, a.t1)
        vab = va - vb
        vlg = [abs(va), abs(vb), abs(vc)]
        emt[n] = dict(v_ll_kv=abs(vab), ang_ab=math.degrees(math.atan2(vab.imag, vab.real)), v_lg_kv=vlg,
                      unbalance_pct=(max(vlg) - min(vlg)) / np.mean(vlg) * 100)
    ref_ang0 = emt[0]["ang_ab"]
    for n in emt:
        emt[n]["ang_ab_rel"] = ((emt[n]["ang_ab"] - ref_ang0 + 180) % 360) - 180
    # transformer LV currents (rms A) and grid P/Q
    trf_emt = {}
    for tr in d["transformers"]:
        ia = abs(phasor(t, ch["I_%s_A" % tr["id"]], a.t0, a.t1)) * 1e3
        trf_emt[tr["id"]] = ia
    pg = float(np.mean(ch["P_grid"][(t >= a.t0) & (t < a.t1)])); qg = float(np.mean(ch["Q_grid"][(t >= a.t0) & (t < a.t1)]))

    # references
    pp_ref, pp_trf, pp_p, pp_q = pandapower_reference(d, load_scale=a.bias, closed=tuple(x for x in a.closed.split(",") if x))
    tb = {x["bus"]: x for x in d["powerflow_reference"]["buses"]}
    tb_br = d["powerflow_reference"].get("branches", [])

    print("\n%3s %9s %9s %9s | %8s %8s | %8s %8s %8s" % ("bus", "EMT kV", "pp kV", "TB kV", "EMT-pp%", "EMT-TB%", "EMT ang", "pp ang", "TB ang"))
    rows = []
    worst_pp = worst_tb = 0.0
    for n in range(15):
        e = emt[n]; p = pp_ref[n]; b = tb[n]
        tbkv = b["V_LL_rms_kV"]["AB"]; tbang = b["angle_deg"]["AB"]
        dpp = (e["v_ll_kv"] / p["v_kv"] - 1) * 100; dtb = (e["v_ll_kv"] / tbkv - 1) * 100
        worst_pp = max(worst_pp, abs(dpp)); worst_tb = max(worst_tb, abs(dtb))
        print("%3d %9.4f %9.4f %9.2f | %+8.3f %+8.3f | %8.2f %8.2f %8.2f" % (n, e["v_ll_kv"], p["v_kv"], tbkv, dpp, dtb, e["ang_ab_rel"], p["ang"], tbang))
        rows.append(dict(bus=n, emt_kv=e["v_ll_kv"], pp_kv=p["v_kv"], tb_kv=tbkv, err_pp_pct=dpp, err_tb_pct=dtb,
                         emt_ang=e["ang_ab_rel"], pp_ang=p["ang"], tb_ang=tbang, unbalance_pct=e["unbalance_pct"]))
    print("\nworst |EMT-pandapower| = %.3f %%   worst |EMT-brochure| = %.3f %%" % (worst_pp, worst_tb))
    print("max phase unbalance in EMT: %.4f %%" % max(r["unbalance_pct"] for r in rows))
    print("\ntransformer LV current (A rms):")
    for tid, ia in trf_emt.items():
        tbi = next((br for br in tb_br if str(br.get("from_bus")) == "0" and str(br.get("to_bus")) == str(next(x["to_bus"] for x in d["transformers"] if x["id"] == tid))), None)
        tbi_a = tbi["I_rms_A"]["A"] if tbi else float("nan")
        print("  %s: EMT %.1f  pandapower %.1f  brochure %.2f" % (tid, ia, pp_trf[tid]["i_lv_a"], tbi_a))
    print("grid P/Q: EMT %.3f MW / %.3f MVAr   pandapower %.3f / %.3f" % (pg, qg, pp_p, pp_q))
    json.dump(dict(window=[a.t0, a.t1], bias=a.bias, buses=rows, trafo_emt_A=trf_emt, grid_pq_emt=[pg, qg], grid_pq_pp=[pp_p, pp_q],
                   worst_pp_pct=worst_pp, worst_tb_pct=worst_tb), open(a.out, "w"), indent=1)
    print("saved", a.out)

if __name__ == "__main__":
    main()
