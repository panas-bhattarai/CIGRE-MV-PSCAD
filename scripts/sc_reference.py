"""Short-circuit reference for CIGRE-MV-PSCAD: IEC 60909-style calculation with pandapower
(c = 1.0, loads ignored) plus a hand Thevenin calculation at bus 1. Python 3.11."""
import os, sys, math, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pandapower as pp, pandapower.shortcircuit as sc
from validate_cigre_mv import DATA, W

d = json.load(open(DATA, encoding="utf-8"))
def build_net():
    net = pp.create_empty_network(f_hz=50, sn_mva=25)
    b = {0: pp.create_bus(net, 110)}
    for i in range(1, 15): b[i] = pp.create_bus(net, 20)
    hv = d["hv_equivalent"]["network_specific"]
    pp.create_ext_grid(net, b[0], vm_pu=1.0, s_sc_max_mva=hv["short_circuit_power_MVA"], rx_max=hv["R_over_X"],
                       s_sc_min_mva=hv["short_circuit_power_MVA"], rx_min=hv["R_over_X"], x0x_max=1.0, r0x0_max=hv["R_over_X"], x0x_min=1.0, r0x0_min=hv["R_over_X"])
    for tr in d["transformers"]:
        R, X = tr["Z_ohm_ref_V2"]["R"], tr["Z_ohm_ref_V2"]["X"]; zb = tr["V2_kV"]**2 / tr["S_rated_MVA"]
        tap = tr["tap_setting_used_in_power_flow"]["secondary_pct"]
        vk = math.hypot(R, X)/zb*100; vkr = R/zb*100
        pp.create_transformer_from_parameters(net, b[tr["from_bus"]], b[tr["to_bus"]], sn_mva=25, vn_hv_kv=110, vn_lv_kv=20,
            vkr_percent=vkr, vk_percent=vk, pfe_kw=0, i0_percent=0, shift_degree=-30, vector_group="Dyn",
            vk0_percent=vk, vkr0_percent=vkr, mag0_percent=100, mag0_rx=0, si0_hv_partial=0.9,
            tap_side="lv", tap_neutral=0, tap_min=-16, tap_max=16, tap_step_percent=0.625, tap_pos=round(tap/0.625), tap_changer_type="Ratio", name=tr["id"])
    sw = {s["line_segment"] for s in d["switches"]}
    for l in d["lines"]:
        pp.create_line_from_parameters(net, b[l["from_bus"]], b[l["to_bus"]], l["length_km"], l["R1_ohm_per_km"], l["X1_ohm_per_km"],
            l["B1_uS_per_km"]/W*1e3, max_i_ka=0.2, r0_ohm_per_km=l["R0_ohm_per_km"], x0_ohm_per_km=l["X0_ohm_per_km"],
            c0_nf_per_km=l["B0_uS_per_km"]/W*1e3, endtemp_degree=20, in_service=(l["segment"] not in sw))
    return net, b

out = {}
for fault in ("3ph", "1ph"):
    net, b = build_net()
    try:
        sc.calc_sc(net, fault=fault, case="max", ip=True, branch_results=False, use_pre_fault_voltage=False)
    except TypeError:
        sc.calc_sc(net, fault=fault, case="max", ip=True, branch_results=False)
    # pandapower applies c=1.1 for case max at HV; override: rerun with c via ext_grid? Scale result linearly instead.
    for n in (1, 11):
        ik = float(net.res_bus_sc.ikss_ka[b[n]]); ip = float(net.res_bus_sc.ip_ka[b[n]])
        out["%s_bus%d" % (fault, n)] = dict(ikss_kA_c1p1=ik, ikss_kA_c1p0=ik/1.1, ip_kA_c1p1=ip)
        print("%s at bus %2d: Ik'' = %.4f kA (c=1.1)  -> %.4f kA at c=1.0 ; ip = %.3f kA" % (fault, n, ik, ik/1.1, ip))

# Hand Thevenin at bus 1, three-phase, with the actual EMF 110.48 kV and the tap-scaled transformer impedance
hv = d["hv_equivalent"]["network_specific"]; tr = d["transformers"][0]
v2 = 20*(1+tr["tap_setting_used_in_power_flow"]["secondary_pct"]/100)
zs = hv["nominal_voltage_kV"]**2/hv["short_circuit_power_MVA"]; xs = zs/math.sqrt(1+hv["R_over_X"]**2); rs = hv["R_over_X"]*xs
k2 = (v2/110)**2
Zs = complex(rs, xs)*k2
zb = v2**2/25; Zt = complex(0.001*zb, 0.12*zb)
E = 110.48/math.sqrt(3)*(v2/110)
I3 = E/abs(Zs+Zt)
print("hand 3ph bus 1: Zs' = %.4f+j%.4f, Zt = %.4f+j%.4f ohm (LV, tap-scaled), E_ph = %.3f kV -> Ik = %.4f kA" % (Zs.real, Zs.imag, Zt.real, Zt.imag, E, I3))
# single phase: Z0 of Dyn transformer = Zt (delta HV blocks source zero seq), Z1=Z2=Zs+Zt
I1 = 3*E/abs(2*(Zs+Zt)+Zt)
print("hand 1ph bus 1 (Z0 = Zt): Ik = %.4f kA" % I1)
out["hand_bus1"] = dict(I3ph_kA=I3, I1ph_kA=I1, E_ph_kV=E, Zs_LV=[Zs.real, Zs.imag], Zt_LV=[Zt.real, Zt.imag])
json.dump(out, open(os.path.join(os.path.dirname(DATA), "..", "results", "sc_reference.json"), "w"), indent=1)
