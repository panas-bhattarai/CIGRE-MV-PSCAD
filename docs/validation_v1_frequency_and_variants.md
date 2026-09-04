# CIGRE-MV-PSCAD, version 1: frequency scan, time-step check, meshed configuration

Date: 2026-09-04. Scripts: `scripts/run_freq_scan.py`, `scripts/fscan_reference.py`,
`scripts/run_variants.py`, `scripts/validate_cigre_mv.py`. Results in
`results/fscan_b11_emt.json`, `results/fscan_b11_reference.json`,
`results/validation_radial_12p5us.json`, `results/validation_meshed.json`.

## 1. Frequency scan at bus 11 (phase A to ground driving-point impedance)

Method. A single-phase AC voltage source (1 kV behind 2000 ohm, master-library `source_1`)
is connected between phase A of bus 11 and ground, so it injects about 0.7 A at the test
frequency on top of the normal 50 Hz operation. Eleven runs at 120 to 2950 Hz, 20 us step,
0.6 s each. V and I at the test frequency are extracted by least squares over 0.4 to 0.6 s,
with the 50 Hz component fitted simultaneously so it does not leak. Loads set to exponent 2
(constant impedance) so the network is linear.

Reference. Positive- and zero-sequence nodal admittance matrices built from the same data
file: lumped PI lines with frequency-scaled reactances and constant resistance, transformer
leakage referred through the tapped ratio, grid Thevenin (positive sequence only, since the
delta HV winding blocks zero sequence), loads as parallel R and L sized at 20 kV. The open
tie lines are kept as dangling PI sections connected at their bus end, exactly as in the
model. Z_AG = (2 Z1 + Z0) / 3.

| f (Hz) | Reference, ohm / deg | EMT, ohm / deg | Magnitude diff | Angle diff |
|---|---|---|---|---|
| 120 | 27.07 / 63.1 | 27.19 / 62.8 | +0.45 % | -0.3 |
| 270 | 53.42 / 52.4 | 53.61 / 52.4 | +0.35 % | 0.0 |
| 450 | 74.08 / 38.3 | 74.10 / 38.3 | +0.02 % | 0.0 |
| 850 | 87.07 / 13.8 | 87.06 / 13.7 | -0.01 % | 0.0 |
| 1150 | 75.17 / 3.3 | 75.06 / 3.3 | -0.14 % | 0.0 |
| 1550 | 55.76 / 9.8 | 55.63 / 10.1 | -0.23 % | +0.2 |
| 2050 | 64.59 / 35.1 | 65.37 / 35.4 | +1.21 % | +0.2 |
| 2950 | 82.98 / 40.4 | 84.44 / 40.9 | +1.77 % | +0.6 |

Two things were learned on the way and are worth keeping:

- The raw EMT angle was too high by exactly 360 f dt degrees. PSCAD writes the source
  current channel one time step after the voltage channels, so any impedance or power
  computed from exported V and I must advance the current by one step. The table above is
  corrected. (The Codex notes recorded the same one-step offset for load currents.)
- Leaving the open tie lines out of the reference gave errors of up to 8 % around 1.2 to
  1.6 kHz. Their capacitance is still on the feeder even with the breaker open. The model
  is right; the simplified reference was wrong.

The residual 1 to 2 % above 2 kHz is consistent with the trapezoidal integration at 20 us
and with the lumped PI representation, which is the expected limit of a PI-section model.
The first parallel resonance of the feeder is calculated at about 4.6 kHz.

## 2. Time-step check: radial case at 12.5 us

Worst bus-voltage difference from the pandapower reference (loads scaled by the 12.5 us
load bias of 1.0056): **0.018 %**, versus 0.017 % at 50 us. Transformer currents within
0.02 %. Phase unbalance 0.003 %. The 50 us step is adequate for steady-state and
fundamental-frequency work; use 12.5 to 20 us for harmonic or switching-transient studies.

## 3. Meshed configuration: S2 and S3 closed, S1 open, 50 us

Switch states are changed by setting the constants S2_open and S3_open to 0 on the canvas;
nothing else changes. pandapower reference with the same segments in service.

| Bus | EMT kV | pandapower kV | Difference |
|---|---|---|---|
| 3 | 19.228 | 19.232 | -0.023 % |
| 4 | 19.175 | 19.179 | -0.023 % |
| 7 | 19.138 | 19.142 | -0.023 % |
| 11 | 19.158 | 19.162 | -0.024 % |

Worst difference over all buses **0.024 %**. Closing the loops raises the feeder-end
voltage at bus 11 from 19.07 to 19.16 kV, as expected. The brochure gives no meshed results
to compare with.
