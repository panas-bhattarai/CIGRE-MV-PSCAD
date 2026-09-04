# Test: PSCAD master-library fixed load as a constant-power load

Date: 2026-09-04. Case built and run entirely through the automation library:
`scripts/test_fixed_load.py` and `scripts/test_fixed_load_settle.py`. Case files in
`pscad/tests/fixed_load/`, numeric results in `results/fixed_load_test.json` and
`results/fixed_load_settle.json`.

## Question

Can the master-library component `fixed_load` (one per phase, voltage exponents NP and NQ)
reproduce a load-flow constant-P/Q operating point when the terminal voltage is below
nominal, so that the benchmark release needs no custom load component?

## Set-up

- Three-phase source `source3R`, 20 kV L-L, 50 Hz, R = 0.001 ohm, X = 0.01 ohm (stiff).
- Three `fixed_load` blocks, one per phase, internal ground. Values: CIGRE MV bus 3
  residential load, 285 kVA at pf 0.97, i.e. 276.45 kW and 69.28 kvar three-phase,
  entered per phase with rated L-G voltage 11.547 kV, PQ defined at rated voltage,
  1 part, NCYC = 10 cycles, no frequency dependence.
- Ammeter and line-to-ground voltmeter per phase recorded to file; P and Q computed in
  Python from least-squares fundamental phasors over the last 0.2 s. The source's own
  P/Q output agrees with this to 0.1 kW.
- Source voltage 20.0 kV (1.0 pu) and 18.0 kV (0.9 pu). Time step 50 us unless stated.

## Results

| Case | Exponents | Terminal V (pu) | P (kW) | Q (kvar) | Error vs setpoint |
|---|---|---|---|---|---|
| exp0_V1.00 | NP = NQ = 0 | 1.000 | 278.57 | 69.82 | +0.77 % |
| exp0_V0.90 | NP = NQ = 0 | 0.900 | 278.57 | 69.82 | +0.77 % |
| exp2_V1.00 | NP = NQ = 2 | 1.000 | 276.45 | 69.28 | 0.00 % |
| exp2_V0.90 | NP = NQ = 2 | 0.900 | 223.92 | 56.12 | -19.00 % (= 0.9^2) |

Settling and time-step check, exponent 0 at 0.9 pu:

| Run | 0.2-0.4 s | 0.8-1.0 s | 2.8-3.0 s |
|---|---|---|---|
| 3 s at 50 us | +0.77 % | +0.77 % | +0.77 % |
| 1 s at 12.5 us | +0.56 % | +0.56 % | not run |

## Findings

1. **Exponent 0 works as a constant-power load.** P and Q are identical at 1.0 pu and
   0.9 pu, so the component does hold power against voltage within the range the
   benchmark needs. Exponent 2 behaves exactly as constant impedance (0.00 % at nominal,
   voltage-squared droop below it), which confirms the test rig and the measurement.
2. **Exponent 0 carries a small positive bias**, +0.77 % at 50 us and +0.56 % at 12.5 us,
   identical for P and Q, present from the first window and constant for 3 s. It is not
   a settling effect. Equal P and Q bias points to the component's internal voltage
   measurement reading about 0.3-0.4 % low, so the admittance it sets is slightly high.
   The EMTDC source is not shipped, so the mechanism cannot be confirmed.
3. The bias would shift the feeder-wide load by under 1 % and the bus voltages by
   roughly 0.1 %, which is inside the 1 % class agreement the brochure table allows but
   outside the 0.1 % agreement we want against the pandapower rebuild.

## Options for the release

- **A. Master-library load, bias documented.** No custom code at all; the release is
  fully portable. State the +0.6-0.8 % constant-power bias and its time-step dependence
  in the documentation. Validation tolerance against the exact load flow becomes 0.2 %
  on voltage rather than 0.1 %.
- **B. Master-library load with setpoint correction.** Divide the entered P and Q by the
  measured bias factor for the release time step. Exact at that step, but it is a
  calibration that must be redone if the step changes; not recommended for a benchmark.
- **C. Own constant-PQ component** (resistor plus controlled current with a lag and a
  low-voltage floor), designed and documented by us. Exact to 1e-6, but the release then
  contains custom code that users must trust. Keep as the option if A is judged too loose.

Recommendation: A for the base release, with C offered later as an optional library.

## Side finding: running PSCAD from Claude Code

The Claude Code harness sets the environment variable `NoDefaultCurrentDirectoryInExePath=1`.
PSCAD inherits it and its simulation launcher batch file then fails with
"'case.exe' is not recognized as an internal or external command". The helper
`scripts/pscad_session.py` removes the variable before launching PSCAD. This affected
every automated run earlier today, including the first smoke test, and is unrelated to
the model or to licensing.
