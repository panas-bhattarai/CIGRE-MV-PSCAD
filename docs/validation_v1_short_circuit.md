# CIGRE-MV-PSCAD, version 1: short-circuit validation

Date: 2026-09-04. Driver: `scripts/run_sc_cases.py` (builds the model once with a timed
fault block, then changes only the fault bus and the phase flags between runs).
Results: `results/sc_validation_noload.json` (network check) and
`results/sc_validation.json` (with benchmark loads).

## Method

- Fault block: master-library `tpflt` at the fault bus, fault-on resistance 0.001 ohm,
  applied at 0.5 s for 0.3 s by `tfault`. Fault current fundamental rms fitted by least
  squares over 0.7-0.8 s, after the DC offset has decayed. 50 us step.
- Hand calculation, same model definitions: Thevenin EMF 110.48 kV behind the 5000 MVA
  grid equivalent, referred to the transformer LV side with the tap-adjusted ratio
  (110/21.25 kV); transformer 0.001 + j0.12 pu on 25 MVA at the tapped LV voltage
  (0.018 + j2.168 ohm); line impedances summed along the radial path
  1-2-3-8-9-10-11 (9.96 km of cable). Zero-sequence: the delta HV winding blocks the
  upstream path, so Z0 = transformer + line zero-sequence. Single-phase current
  3E / |2 Z1 + Z0|. Loads and line capacitance ignored, as in IEC 60909 practice.

## Result 1: network check, loads reduced to 0.1 %

| Fault | Bus | EMT (kA rms) | Hand (kA rms) | Difference | First peak (kA) |
|---|---|---|---|---|---|
| Three-phase to ground | 1 | 5.479 | 5.458 | +0.38 % | 14.23 |
| Three-phase to ground | 11 | 1.158 | 1.158 | +0.08 % | 1.95 |
| Single-phase A-G | 1 | 5.553 | 5.532 | +0.38 % | 14.48 |
| Single-phase A-G | 11 | 0.899 | 0.899 | -0.05 % | 1.55 |

Positive, negative and zero-sequence impedances of the source, both transformers and the
lines therefore behave as specified, including the zero-sequence data that the earlier
Codex model had only estimated. Healthy-phase currents in the single-phase cases are zero,
as expected for a grounded fault on a grounded network.

## Result 2: with the benchmark loads connected (constant-power loads, exponent 0)

| Fault | Bus | EMT (kA rms) | Hand, no load | Difference |
|---|---|---|---|---|
| Three-phase | 1 | 5.468 | 5.458 | +0.18 % |
| Three-phase | 11 | 1.074 | 1.158 | -7.2 % |
| Single-phase | 1 | 5.539 | 5.532 | +0.14 % |
| Single-phase | 11 | 0.854 | 0.899 | -5.0 % |

At bus 1 the loads sit at or beyond the fault point and do not matter. At bus 11 the
loads on buses 3 to 10 lie between the source and the fault and take current, so the
fault current at the feeder end is 5 to 7 % lower than the no-load figure. This is
physical, not an error; IEC 60909 ignores it by convention, an EMT model does not.
Users comparing with hand or IEC calculations should disconnect or scale down the loads,
as Result 1 does.

## For reference: IEC 60909 values from pandapower (c = 1.0, taps ignored, nominal voltage)

Bus 1: 5.89 kA (3ph), 5.98 kA (1ph). Bus 11: 1.11 kA (3ph), 0.86 kA (1ph). These differ
from the model by up to 8 % at bus 1 because IEC practice uses the nominal 20 kV and the
rated impedance, whereas the model runs at the tapped 21.25 kV with the impedance referred
through the tapped ratio. The convention is documented; the physics is the same.

## Notes

- Fault currents at bus 1 of about 5.5 kA and a first peak of about 14 kA are consistent
  with a 25 MVA, 12 % transformer.
- Building the model through the automation library takes 3 to 5 minutes (about 600
  remote calls); a run of 1 s takes 12 s. The driver therefore builds once per session.
