"""Reproduce TB 575 Table 9.6 from the published data by adopting the brochure's own
modelling conventions, and quantify what each convention is worth.

Two conventions are varied, giving four pandapower load flows of the same data file:

  tap  = "referred"  transformer impedance (12 % on 25 MVA) referred through the *tapped*
                     ratio, i.e. the ohmic value on the 20 kV side scales with (1 + tap)^2.
                     This is what PSCAD, pandapower and a hand calculation do by default.
  tap  = "untapped"  the 12 % is held on the untapped 110/20 kV base and the tap acts only
                     on the ideal ratio, so the ohmic value on the 20 kV side is fixed at
                     0.12 * 20^2 / 25 = 1.92 ohm regardless of tap.
  load = "P"         constant power (the benchmark statement of the loads).
  load = "Z"         constant impedance at nominal 20 kV.

For each case the bus voltages are compared with Table 9.6 and the transformer LV
currents with the brochure's branch table. A three-phase Thevenin fault at bus 1 (loads
ignored, same EMF as scripts/sc_reference.py) shows the effect of the tap convention on
short-circuit duty. Output: results/tb575_conventions.json. Python 3.11, pandapower 3.x.
"""
import os, sys, math, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pandapower as pp
from validate_cigre_mv import DATA, ROOT, W

d = json.load(open(DATA, encoding="utf-8"))
OUT = os.path.join(ROOT, "results", "tb575_conventions.json")


def build(tap_convention, load_model):
    net = pp.create_empty_network(f_hz=50, sn_mva=25)
    b = {0: pp.create_bus(net, 110, name="Bus 0")}
    for i in range(1, 15):
        b[i] = pp.create_bus(net, 20, name="Bus %d" % i)
    hv = d["hv_equivalent"]["network_specific"]
    pp.create_ext_grid(net, b[0], vm_pu=1.0, va_degree=0.0, s_sc_max_mva=hv["short_circuit_power_MVA"], rx_max=hv["R_over_X"])
    for tr in d["transformers"]:
        R, X = tr["Z_ohm_ref_V2"]["R"], tr["Z_ohm_ref_V2"]["X"]; zb = tr["V2_kV"] ** 2 / tr["S_rated_MVA"]
        tap = tr["tap_setting_used_in_power_flow"]["secondary_pct"]
        # pandapower refers vk through the tapped LV voltage; to hold the ohmic impedance on the
        # untapped base, shrink vk by the square of the tap ratio.
        k = 1.0 if tap_convention == "referred" else 1.0 / (1 + tap / 100) ** 2
        pp.create_transformer_from_parameters(net, b[tr["from_bus"]], b[tr["to_bus"]], sn_mva=tr["S_rated_MVA"],
            vn_hv_kv=tr["V1_kV"], vn_lv_kv=tr["V2_kV"], vkr_percent=R / zb * 100 * k, vk_percent=math.hypot(R, X) / zb * 100 * k,
            pfe_kw=0, i0_percent=0, shift_degree=-30, tap_side="lv", tap_neutral=0, tap_min=-16, tap_max=16,
            tap_step_percent=0.625, tap_pos=round(tap / 0.625), tap_changer_type="Ratio", name=tr["id"])
    sw = {s["line_segment"] for s in d["switches"]}
    for l in d["lines"]:
        pp.create_line_from_parameters(net, b[l["from_bus"]], b[l["to_bus"]], l["length_km"], l["R1_ohm_per_km"], l["X1_ohm_per_km"],
            l["B1_uS_per_km"] / W * 1e3, max_i_ka=0.2, r0_ohm_per_km=l["R0_ohm_per_km"], x0_ohm_per_km=l["X0_ohm_per_km"],
            c0_nf_per_km=l["B0_uS_per_km"] / W * 1e3, name="Seg %d" % l["segment"], in_service=(l["segment"] not in sw))
    z = 100.0 if load_model == "Z" else 0.0
    for ld in d["loads"]:
        for sec in ("residential", "commercial_industrial"):
            sd = ld[sec]
            if sd["S_kVA"]:
                pp.create_load(net, b[ld["bus"]], p_mw=sd["P_kW_derived"] / 1e3, q_mvar=sd["Q_kvar_derived"] / 1e3,
                               const_z_p_percent=z, const_z_q_percent=z)
    pp.runpp(net, init="dc", max_iteration=50, numba=False)
    return net, b


def thevenin_3ph_bus1(tap_convention):
    """Three-phase fault at bus 1, loads ignored, EMF as in scripts/sc_reference.py."""
    hv = d["hv_equivalent"]["network_specific"]; tr = d["transformers"][0]
    v2 = tr["V2_kV"] * (1 + tr["tap_setting_used_in_power_flow"]["secondary_pct"] / 100)
    zs = hv["nominal_voltage_kV"] ** 2 / hv["short_circuit_power_MVA"]
    xs = zs / math.sqrt(1 + hv["R_over_X"] ** 2); rs = hv["R_over_X"] * xs
    Zs = complex(rs, xs) * (v2 / hv["nominal_voltage_kV"]) ** 2          # source, through the ideal (tapped) ratio
    zb = (v2 if tap_convention == "referred" else tr["V2_kV"]) ** 2 / tr["S_rated_MVA"]
    Zt = complex(0.001 * zb, 0.12 * zb)
    E = 110.48 / math.sqrt(3) * (v2 / hv["nominal_voltage_kV"])
    return dict(Ik_kA=E / abs(Zs + Zt), Zt_ohm_LV=[Zt.real, Zt.imag], Zs_ohm_LV=[Zs.real, Zs.imag], E_ph_kV=E)


tb = {x["bus"]: x for x in d["powerflow_reference"]["buses"]}
tb_i = {}
for br in d["powerflow_reference"]["branches"]:
    if str(br["from_bus"]) == "0":
        tb_i[int(br["to_bus"])] = br["I_rms_A"]["A"]

out = dict(cases={}, fault_bus1_3ph={}, notes=__doc__.strip())
print("%-22s %10s %10s %10s   %s" % ("case", "worst|dV|%", "mean dV %", "worst|dI|%", "per-bus error vs Table 9.6 (%)"))
for tapc in ("referred", "untapped"):
    for lm in ("P", "Z"):
        net, b = build(tapc, lm)
        rows = []
        for i in range(15):
            v = float(net.res_bus.vm_pu[b[i]] * net.bus.vn_kv[b[i]]); ref = tb[i]["V_LL_rms_kV"]["AB"]
            rows.append(dict(bus=i, v_kv=v, tb_kv=ref, err_pct=(v / ref - 1) * 100, ang=float(net.res_bus.va_degree[b[i]]), tb_ang=tb[i]["angle_deg"]["AB"]))
        trf = {}
        for k, tr in enumerate(d["transformers"]):
            ia = float(net.res_trafo.i_lv_ka[k] * 1e3); ref = tb_i[tr["to_bus"]]
            trf[tr["id"]] = dict(i_lv_a=ia, tb_a=ref, err_pct=(ia / ref - 1) * 100)
        errs = [r["err_pct"] for r in rows[1:]]
        worst = max(abs(e) for e in errs); worst_i = max(abs(t["err_pct"]) for t in trf.values())
        name = "tap=%s/load=%s" % (tapc, lm)
        out["cases"][name] = dict(tap_convention=tapc, load_model=lm, buses=rows, trafo=trf,
                                  worst_bus_err_pct=worst, mean_bus_err_pct=sum(errs) / len(errs), worst_trafo_err_pct=worst_i)
        print("%-22s %10.3f %10.3f %10.3f   %s" % (name, worst, sum(errs) / len(errs), worst_i, " ".join("%+.2f" % e for e in errs)))

for tapc in ("referred", "untapped"):
    out["fault_bus1_3ph"][tapc] = thevenin_3ph_bus1(tapc)
ia, ib = out["fault_bus1_3ph"]["referred"]["Ik_kA"], out["fault_bus1_3ph"]["untapped"]["Ik_kA"]
out["fault_bus1_3ph"]["untapped_over_referred_pct"] = (ib / ia - 1) * 100
print("\n3ph fault at bus 1 (loads ignored): referred %.3f kA, untapped %.3f kA, difference %+.1f %%" % (ia, ib, (ib / ia - 1) * 100))
json.dump(out, open(OUT, "w"), indent=1)
print("saved", OUT)
