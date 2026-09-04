# CIGRE European MV Distribution Network Benchmark – extracted parameters

Extracted 2026-09-04 from two documents the user holds locally:

- **TB 575**: CIGRE TF C6.04, *Benchmark Systems for Network Integration of Renewable and Distributed Energy Resources*, Technical Brochure 575, April 2014 (`Source/Cigre Brochure.pdf`, 119 PDF pages). All page references below are **PDF page indices** (printed page = PDF page − 18 in chapters 6 and 9).
- **Paper 2006**: Rudion, Orths, Styczynski, Strunz, *Design of benchmark of medium voltage distribution network for investigation of DG integration*, IEEE PES GM 2006 (`Source/MV benchmark Paper.pdf`, 6 pages).

Machine-readable twin: `data/cigre_mv_european_tb575.json`. Numbers are reproduced exactly as printed; anything I computed myself is marked *derived*.

---

## 1. System overview

Source: TB 575 PDF p.51–52

| Item | Value |
|---|---|
| Nominal MV voltage | 20 kV |
| Frequency | 50 Hz |
| Upstream level | 110 kV subtransmission (220 kV alternative, Sec. 6.3.5 / 6.4.1) |
| Buses | 0 (110 kV) and 1…14 (20 kV) |
| Feeders | Feeder 1 = buses 1–11 (mostly cable); Feeder 2 = buses 12–14 (overhead) |
| Structure | Radial when S1, S2, S3 open; meshed when S2/S3 closed; feeders tied when S1 closed |
| Load balance | Symmetric; 10 % unbalance suggested if wanted (p.56) |
| Grounding | Only qualitative: "typically ungrounded or impedance-grounded" (p.51) |
| Total length feeder 1 (*derived*) | 15.07 km (segments 1–12) |
| Total length feeder 2 incl. tie line (*derived*) | 9.88 km (segments 13–15) |

Cross-check with Paper 2006 (p.2): 20 kV, fed from 110 kV, rural character, subnetwork 1 ≈ 15 km, radial when tie switches "T" open — **agrees**. The paper's subnetwork 2 is linked to subnetwork 1 through an optional MVDC coupler between buses 8 and 14; the brochure replaces this with a 2.0 km overhead line and switch S1.

## 2. HV grid equivalent

Source: TB 575 PDF p.54 (Table 6.14), p.25 (Table 4.2), p.57

| Parameter | Value | Note |
|---|---|---|
| Nominal voltage | 110 kV | Table 6.14 |
| Short-circuit power S_sc | 5000 MVA | Table 6.14 |
| R/X | 0.1 | Table 6.14 |
| Z (*derived*) | 2.42 Ω | 110² / 5000 |
| X, R (*derived*) | 2.408 Ω, 0.2408 Ω | from R/X = 0.1 |

Generic European ranges of Table 4.2 (p.25), for the resource-side benchmark and not specific to this network: LV 0.4 kV, 1–10 MVA, R/X 0.70–11.00; MV 20 kV, 100–1000 MVA, R/X 0.40–2.00; HV 220 kV, 5000–20000 MVA, R/X 0.07–0.60.

The DER case study of Sec. 6.4.1 (p.57) sets the HV side at 220 kV.

Paper 2006 gives no source-impedance data (row 0–1 in its Table 3 is blank).

## 3. Transformers

Source: TB 575 PDF p.54 (Table 6.13), p.104 (Table 9.7), p.56 (Table 6.17)

| From | To | Connection | V1 / V2 | S_rated | Z_tr (referred to 20 kV side) | Z on own base (*derived*, Z_base = 16 Ω) |
|---|---|---|---|---|---|---|
| 0 | 1 | 3-ph Dyn1 | 110 / 20 kV | 25 MVA | 0.016 + j1.92 Ω | 0.1 % + j12.0 % |
| 0 | 12 | 3-ph Dyn1 | 110 / 20 kV | 25 MVA | 0.016 + j1.92 Ω | 0.1 % + j12.0 % |

Tap-changer specification used for the reference power flow (p.54): primary ±5 % in 2.5 % no-load steps; secondary ±10 % in 0.625 % on-load steps. Settings used in Table 9.6 (p.104, Table 9.7):

| Transformer | Primary tap | Secondary tap |
|---|---|---|
| 0–1 (feeder 1) | 0 % | +6.250 % |
| 0–12 (feeder 2) | 0 % | +3.125 % |

Alternative transformers for direct connection to the 220 kV transmission benchmark (p.56, Table 6.17): both 3-ph Dyn1, 220/20 kV, 25 MVA, 0.19 + j1.91 Ω referred to 20 kV (*derived*: 1.1875 % + j11.9375 %).

Neutral treatment of the Dyn1 star point is **not** specified.

Paper 2006: names them TR1 and TR2, 110/20 kV, no impedance or rating given — **no conflict, but no confirmation**.

## 4. Buses

Source: TB 575 PDF p.52 (Figure 6.5)

Bus 0: 110 kV. Buses 1–11: 20 kV, feeder 1. Buses 12–14: 20 kV, feeder 2. Bus 2 carries no load.

## 5. Line segments

Source: TB 575 PDF p.54 (Table 6.12); lengths also on the figure p.52

| Seg | From | To | Cond. ID | Length [km] | Installation | Switch in series |
|---|---|---|---|---|---|---|
| 1 | 1 | 2 | 2 | 2.82 | underground | – |
| 2 | 2 | 3 | 2 | 4.42 | underground | – |
| 3 | 3 | 4 | 2 | 0.61 | underground | – |
| 4 | 4 | 5 | 2 | 0.56 | underground | – |
| 5 | 5 | 6 | 2 | 1.54 | underground | – |
| 6 | 6 | 7 | 2 | 0.24 | underground | S2 |
| 7 | 7 | 8 | 2 | 1.67 | underground | – |
| 8 | 8 | 9 | 2 | 0.32 | underground | – |
| 9 | 9 | 10 | 2 | 0.77 | underground | – |
| 10 | 10 | 11 | 2 | 0.33 | underground | – |
| 11 | 11 | 4 | 2 | 0.49 | underground | S3 |
| 12 | 3 | 8 | 2 | 1.30 | underground | – |
| 13 | 12 | 13 | 1 | 4.89 | overhead | – |
| 14 | 13 | 14 | 1 | 2.99 | overhead | – |
| 15 | 14 | 8 | 1 | 2.00 | overhead | S1 |

Cross-check with Paper 2006 Table 3 (p.5): all 14 common lengths are identical (2.82, 4.42, 0.61, 0.56, 1.54, 0.24, 1.67, 0.32, 0.77, 0.33, 0.49, 1.3, 4.89, 2.99) — **agrees**. The paper has no 14–8 segment (MVDC coupler instead).

## 6. Line types – sequence parameters

Source: TB 575 PDF p.54 (Table 6.12)

| Cond. ID | Installation | R1 [Ω/km] | X1 [Ω/km] | B1 [µS/km] | R0 [Ω/km] | X0 [Ω/km] | B0 [µS/km] | C1 (*derived*) [nF/km] | C0 (*derived*) [nF/km] |
|---|---|---|---|---|---|---|---|---|---|
| 1 | overhead | 0.510 | 0.366 | 3.172 | 0.658 | 1.611 | 1.280 | 10.097 | 4.074 |
| 2 | underground | 0.501 | 0.716 | 47.493 | 0.817 | 1.598 | 47.493 | 151.175 | 151.175 |

The brochure says these were obtained with modified Carson equations and Kron reduction (Sec. 9.3.1, p.109–113) with earth resistivity 100 Ω·m and, for the cable, the tape shield as return path (Sec. 9.3.2.1, p.113). The intermediate phase-domain matrices are not printed.

Cross-check with Paper 2006 Table 3 (p.5): the paper gives per-segment R', X', C' from the original German network, which **differ** from the brochure's two uniform types (see Section 14). Paper values for segment 1–2: 0.579 Ω/km, 0.367 Ω/km, 158.88 nF/km; brochure: 0.501, 0.716, 151.2 nF/km.

## 7. Line types – conductor data and geometry

Source: TB 575 PDF p.53 (Figure 6.6, Tables 6.9, 6.10, 6.11)

Geometry (Table 6.9):

| Installation | a [m] | b [m] | Meaning |
|---|---|---|---|
| Overhead | 9.5 | 1.0 | a = conductor height above ground, b = horizontal spacing between adjacent phases; three conductors in a flat arrangement, no neutral wire |
| Underground | 0.7 | 0.3 | a = burial depth, b = spacing between the three single-core cables laid flat |

Overhead conductor (Table 6.10):

| Cond. ID | Type | Stranding | Area [mm²] | d_c [cm] | GMR [cm] | R'dc 20 °C [Ω/km] | R'ac 50 °C [Ω/km] |
|---|---|---|---|---|---|---|---|
| 1 | A1 (IEC 61089) | 7 | 63 | 1.02 | 0.370 | 0.4545 | 0.5100 |

Underground cable (Table 6.11):

| Cond. ID | Type | Stranding | Area [mm²] | d_c [cm] | GMR [cm] | R'dc 20 °C [Ω/km] | R'ac 90 °C [Ω/km] | t_i [mm] | t_j [mm] | t_ts [mm] | d_ov [mm] |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2 | NA2XS2Y | 19 | 120 | 1.24 | 0.480 | 0.253 | 0.338 | 5.5 | 2.5 | 0.2 | 34.2 |

t_i = insulation thickness, t_j = jacket thickness, t_ts = copper tape-shield thickness, d_ov = overall diameter. Layer order per Figure 6.6: conductor – insulation – tape shield – jacket.

Paper 2006 gives no conductor or geometry data.

## 8. Loads

Source: TB 575 PDF p.55 (Table 6.15)

Values are coincident peak apparent powers, balanced across the three phases; the coincidence factor is already applied. Buses 1 and 12 represent other feeders on the same substation transformer, not the feeder modelled in detail.

| Bus | S_res [kVA] | pf_res | S_ci [kVA] | pf_ci | P_res (*derived*) [kW] | Q_res (*derived*) [kvar] | P_ci (*derived*) [kW] | Q_ci (*derived*) [kvar] |
|---|---|---|---|---|---|---|---|---|
| 1 | 15300 | 0.98 | 5100 | 0.95 | 14994.00 | 3044.66 | 4845.00 | 1592.47 |
| 2 | – | – | – | – | – | – | – | – |
| 3 | 285 | 0.97 | 265 | 0.85 | 276.45 | 69.28 | 225.25 | 139.60 |
| 4 | 445 | 0.97 | – | – | 431.65 | 108.18 | – | – |
| 5 | 750 | 0.97 | – | – | 727.50 | 182.33 | – | – |
| 6 | 565 | 0.97 | – | – | 548.05 | 137.35 | – | – |
| 7 | – | – | 90 | 0.85 | – | – | 76.50 | 47.41 |
| 8 | 605 | 0.97 | – | – | 586.85 | 147.08 | – | – |
| 9 | – | – | 675 | 0.85 | – | – | 573.75 | 355.58 |
| 10 | 490 | 0.97 | 80 | 0.85 | 475.30 | 119.12 | 68.00 | 42.14 |
| 11 | 340 | 0.97 | – | – | 329.80 | 82.66 | – | – |
| 12 | 15300 | 0.98 | 5280 | 0.95 | 14994.00 | 3044.66 | 5016.00 | 1648.68 |
| 13 | – | – | 40 | 0.85 | – | – | 34.00 | 21.07 |
| 14 | 215 | 0.97 | 390 | 0.85 | 208.55 | 52.27 | 331.50 | 205.45 |

res = residential, ci = commercial/industrial. Q assumes lagging pf.

Coincidence rule from Appendix 9.3.4 (p.116): CF = 0.6·(1 + 1/N_ld) applied to the sum of N_ld individual loads; equivalent pf from the P and Q sums.

Cross-check with Paper 2006 Table 1 (p.3) — see Section 14 for the full table. With a 100 MVA base (0.01 pu = 1 MW) the paper matches the brochure to within ±2.5 kW / ±1.1 kvar at every bus except 1, 12 and 13.

## 9. Daily load profiles

Source: TB 575 PDF p.51 (Figure 6.4) — **digitised by me from the plotted curves**, not tabulated in the brochure. Accuracy roughly ±0.02 pu; half-hour samples are in the JSON.

| t [h] | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Residential | 0.25 | 0.21 | 0.19 | 0.18 | 0.19 | 0.24 | 0.42 | 0.61 | 0.64 | 0.63 | 0.67 | 0.61 | 0.73 |
| Comm./Ind. | 0.34 | 0.32 | 0.29 | 0.31 | 0.38 | 0.47 | 0.67 | 0.88 | 0.98 | 0.98 | 0.98 | 0.79 | 0.83 |

| t [h] | 13 | 14 | 15 | 16 | 17 | 18 | 19 | 20 | 21 | 22 | 23 | 24 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Residential | 0.66 | 0.56 | 0.49 | 0.47 | 0.64 | 0.80 | 0.92 | 0.82 | 0.68 | 0.56 | 0.39 | 0.28 |
| Comm./Ind. | 0.86 | 0.86 | 0.86 | 0.79 | 0.55 | 0.50 | 0.46 | 0.42 | 0.39 | 0.36 | 0.35 | 0.34 |

Values are per-unit of each node's peak apparent power. Residential peak ≈ 0.92 near 19 h; commercial/industrial reaches 1.0 between about 8 and 10 h.

Paper 2006 shows the same two curves (Figs. 4 and 5, p.3) as pictures only.

## 10. Configuration switches

Source: TB 575 PDF p.52 (Figure 6.5 and text), p.103

| Switch | In segment | Between buses | Length [km] | Effect when closed | Base case |
|---|---|---|---|---|---|
| S1 | 15 | 14 – 8 | 2.00 | ties feeder 2 to feeder 1 | open |
| S2 | 6 | 6 – 7 | 0.24 | closes loop 3-8-7-6-5-4 in feeder 1 | open |
| S3 | 11 | 11 – 4 | 0.49 | closes loop 8-9-10-11-4 in feeder 1 | open |

Positions are read from the figure (S3 drawn at the bus-4 end of segment 11, S2 at the bus-7 end of segment 6). If separate substations are assumed for the two feeders, the brochure recommends adding 110 kV subtransmission lines from Sec. 5.3.4 between the HV equivalent and each transformer.

Paper 2006 Fig. 3 (p.2) marks "T" (open in normal operation) at the same two places in subnetwork 1 (4–11 near bus 4, 7–6 near bus 7) — **agrees**.

## 11. DER units (case study, Sec. 6.4)

Source: TB 575 PDF p.58 (Table 6.18); modelling notes p.57

| Bus | Type | P_max [kW] |
|---|---|---|
| 3 | Photovoltaic | 20 |
| 4 | Photovoltaic | 20 |
| 5 | Photovoltaic | 30 |
| 5 | Battery | 600 |
| 5 | Residential fuel cell | 33 |
| 6 | Photovoltaic | 30 |
| 7 | Wind turbine | 1500 |
| 8 | Photovoltaic | 30 |
| 9 | Photovoltaic | 30 |
| 9 | CHP diesel | 310 |
| 9 | CHP fuel cell | 212 |
| 10 | Photovoltaic | 40 |
| 10 | Battery | 200 |
| 10 | Residential fuel cell | 14 |
| 11 | Photovoltaic | 10 |

PV and wind were modelled as stochastic sources, fuel cells and CHP as deterministic; the simulation tool was PSS NETOMAC with the HV side at 220 kV.

Cross-check with Paper 2006 Table 2 (p.4): identical list — **agrees**.

## 12. Reference power flow (radial base case)

Source: TB 575 PDF p.103–104 (Tables 9.6 and 9.7). Configuration: S1, S2, S3 open; taps of Section 3. Voltages are line-to-line rms; angle of bus 0 phase AB is the reference. Only phase AB is listed here; BC and CA are the same magnitude shifted by −120° / +120° (all three in the JSON).

| Bus | V_AB [kV] | angle [°] | V/V_nom (*derived*) |
|---|---|---|---|
| 0 | 110 | 0 | 1.0000 |
| 1 | 20.52 | 23.66 | 1.0260 |
| 2 | 20.09 | 22.75 | 1.0045 |
| 3 | 19.43 | 21.25 | 0.9715 |
| 4 | 19.40 | 21.16 | 0.9700 |
| 5 | 19.38 | 21.10 | 0.9690 |
| 6 | 19.35 | 21.03 | 0.9675 |
| 7 | 19.33 | 21.03 | 0.9665 |
| 8 | 19.33 | 21.04 | 0.9665 |
| 9 | 19.31 | 21.00 | 0.9655 |
| 10 | 19.29 | 20.95 | 0.9645 |
| 11 | 19.29 | 20.94 | 0.9645 |
| 12 | 20.04 | 24.50 | 1.0020 |
| 13 | 19.94 | 24.45 | 0.9970 |
| 14 | 19.88 | 24.43 | 0.9940 |

Branch currents, phase A (rms A, angle °):

| Branch | I [A] | angle [°] |
|---|---|---|
| HV bus – 0 | 256.06 | −19.78 |
| 0 – 1 | 727.89 | 9.75 |
| 1 – 2 | 125.27 | 5.41 |
| 2 – 3 | 125.98 | 4.37 |
| 3 – 4 | 48.98 | 8.30 |
| 4 – 5 | 36.57 | 8.25 |
| 5 – 6 | 15.79 | 6.97 |
| 8 – 7 | 2.52 | −10.59 |
| 3 – 8 | 62.31 | 1.79 |
| 8 – 9 | 43.43 | −0.83 |
| 9 – 10 | 25.21 | 5.73 |
| 10 – 11 | 9.48 | 6.89 |
| 0 – 12 | 612.21 | 10.95 |
| 12 – 13 | 18.27 | −1.17 |
| 13 – 14 | 17.18 | −1.08 |

Sanity check (*derived*): √3 · 20.52 kV · 727.89 A = 25.87 MVA through TR1 and √3 · 20.04 · 612.21 = 21.25 MVA through TR2, consistent with the large bus-1 and bus-12 loads plus the feeders. No losses, P/Q flows, or results for meshed/tied configurations are given.

Paper 2006 (p.3) reports 19.7 MW peak through TR1 and 3.5 MW peak drawn beyond bus 2 without DG; these are time-series results with the daily profiles, not directly comparable to the brochure's snapshot.

## 13. Uncertainties and gaps for an EMT model

Things the brochure does not provide (or provides only partially) that an EMT model needs:

1. **Zero-sequence / earth-return detail.** R0, X0, B0 are given per type, but not the full 3×3 (or 4×4 with shield) phase-domain matrices, shield resistances, or the shield bonding arrangement of the NA2XS2Y cable (single-point vs both-ends bonded). Geometry (Tables 6.9–6.11) and the Carson method (Sec. 9.3) are given, so the matrices can be regenerated, but the earth resistivity (100 Ω·m) is only a "typical value".
2. **Frequency dependence.** Only 50 Hz lumped values; no conductor/earth frequency-dependent data. The geometry allows building a frequency-dependent line/cable model, but the brochure's own numbers are constant-parameter.
3. **Cable semiconducting layers and permittivity.** Only insulation/jacket/tape thicknesses and overall diameter; no insulation permittivity, no semicon layer thicknesses, no jacket permittivity.
4. **Transformer**: no saturation curve, no no-load losses/magnetising current, no winding capacitances, no leakage split between windings, no zero-sequence impedance (a Dyn1 core-type value would have to be assumed).
5. **Neutral grounding of the 20 kV star point** (solid, resistance, Petersen coil, or isolated) is not specified; only "ungrounded or impedance-grounded" as a regional remark.
6. **HV source**: R/X = 0.1 and S_sc = 5000 MVA give the positive-sequence impedance; zero-sequence source impedance and the transformer HV neutral treatment are not given.
7. **Switch/breaker models**: S1–S3 have no ratings, timing, or arc data.
8. **Loads**: only S and pf at peak; no ZIP/voltage-dependence or motor share, no per-phase unbalance (10 % suggested only as a guideline), no harmonics.
9. **DER**: only P_max; no converter topology, control, reactive capability, short-circuit contribution, or filter data. The daily generation curves of Fig. 6.8 are pictures only.
10. **Load profiles** exist only as a figure; the tabulated values here are digitised (±0.02 pu).
11. **Transformer tap** is given as the setting used in the power flow, not as an OLTC controller (deadband, delay).
12. **Power flow reference** exists only for the radial case; nothing to validate meshed or tied operation, and no loss figures.
13. **Line ratings / ampacity** are not given.

## 14. Values where the paper and brochure differ

1. **Line electrical parameters.** The paper (Table 3, p.5) lists per-segment values from the original German network; the brochure standardises on two conductor types. Examples (paper → brochure):
   - 1–2: R' 0.579 → 0.501 Ω/km; X' 0.367 → 0.716 Ω/km; C' 158.88 nF/km → 151.2 nF/km (*derived* from 47.493 µS/km).
   - 2–3: R' 0.164 → 0.501; X' 0.113 → 0.716; C' printed as 6608 nF/km → 151.2.
   - 12–13: R' 0.337 → 0.510; X' 0.358 → 0.366; C' 162.88 nF/km → 10.1 nF/km (*derived* from 3.172 µS/km).
   - 13–14: R' 0.202 → 0.510; X' 0.122 → 0.366; C' 4784 nF/km → 10.1.
   The paper's C' values in the thousands of nF/km are not plausible for a 20 kV XLPE cable and are probably a units or typesetting error; they should not be used. The brochure values are the benchmark of record.
2. **Bus 1 and bus 12 aggregated loads.** Paper (100 MVA base) vs brochure (*derived* from S and pf):
   - Bus 1 industry: P 5000 vs 4845 kW (−155 kW); Q 1000 vs 1592.47 kvar (+592 kvar).
   - Bus 1 household: Q 3100 vs 3044.66 kvar (−55 kvar).
   - Bus 12 household: Q 3000 vs 3044.66 kvar (+45 kvar); bus 12 industry: P 5000 vs 5016 kW, Q 1700 vs 1648.68 kvar.
   - Bus 13 industry: P 32 vs 34 kW, Q 20 vs 21.07 kvar.
   All other buses agree within ±2.5 kW and ±1.1 kvar, i.e. within the rounding of the paper's p.u. values. Full table:

| Bus | Type | Paper P [kW] | TB575 P [kW] | ΔP [kW] | Paper Q [kvar] | TB575 Q [kvar] | ΔQ [kvar] |
|---|---|---|---|---|---|---|---|
| 1 | Household | 15000 | 14994.00 | −6.00 | 3100 | 3044.66 | −55.34 |
| 1 | Industry | 5000 | 4845.00 | −155.00 | 1000 | 1592.47 | +592.47 |
| 3 | Household | 276 | 276.45 | +0.45 | 69 | 69.28 | +0.28 |
| 3 | Industry | 224 | 225.25 | +1.25 | 139 | 139.60 | +0.60 |
| 4 | Household | 432 | 431.65 | −0.35 | 108 | 108.18 | +0.18 |
| 5 | Household | 725 | 727.50 | +2.50 | 182 | 182.33 | +0.33 |
| 6 | Household | 550 | 548.05 | −1.95 | 138 | 137.35 | −0.65 |
| 7 | Industry | 77 | 76.50 | −0.50 | 48 | 47.41 | −0.59 |
| 8 | Household | 588 | 586.85 | −1.15 | 147 | 147.08 | +0.08 |
| 9 | Industry | 574 | 573.75 | −0.25 | 356 | 355.58 | −0.42 |
| 10 | Industry | 68 | 68.00 | 0.00 | 42 | 42.14 | +0.14 |
| 10 | Household | 477 | 475.30 | −1.70 | 120 | 119.12 | −0.88 |
| 11 | Household | 331 | 329.80 | −1.20 | 83 | 82.66 | −0.34 |
| 12 | Household | 15000 | 14994.00 | −6.00 | 3000 | 3044.66 | +44.66 |
| 12 | Industry | 5000 | 5016.00 | +16.00 | 1700 | 1648.68 | −51.32 |
| 13 | Industry | 32 | 34.00 | +2.00 | 20 | 21.07 | +1.07 |
| 14 | Industry | 330 | 331.50 | +1.50 | 205 | 205.45 | +0.45 |
| 14 | Household | 207 | 208.55 | +1.55 | 52 | 52.27 | +0.27 |

3. **Feeder tie.** Paper: optional 2 MVA MVDC coupler between buses 8 and 14 (1.7 MW in the original network, Fig. 2 legend). Brochure: 2.0 km overhead line (type 1) with switch S1.
4. **Transformer and source data.** Paper gives none; brochure gives Table 6.13 / 6.14. Not a contradiction, but the paper cannot confirm them.
5. **Naming.** Paper: subnetwork 1/2, TR1/TR2, load types household/industry. Brochure: feeder 1/2, transformers 0–1 and 0–12, residential / commercial-industrial.

Items that **agree** between the two sources: voltage level and frequency, bus numbering 0–14, all 14 common line lengths, load buses and load types (bus 2 unloaded), tie-switch locations in feeder 1, the complete DER list, and the shape of the two daily load profiles.
