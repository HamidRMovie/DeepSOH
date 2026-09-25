# deepSOH: physics-based state of health for lithium-ion batteries

Code and data behind the figures in the deepSOH manuscript. deepSOH is the state vector of
a physics-based degradation model: the cyclable lithium, the two electrode capacities, and
the thicknesses of the SEI layer and of plated lithium. This repository re-simulates the
study and re-plots every figure.

It bundles a modified copy of [PyBaMM](https://github.com/pybamm-team/PyBaMM) (v22.8) that
carries the SEI, lithium-plating and kinetics changes the model relies on. Stock PyBaMM will
not reproduce the results.

## Layout

    pybamm/                                  modified PyBaMM (BSD-3, see LICENSE.txt)
    deepSOH/corrected_platin_thick/
        deepsoh_p4_model.py                  P4 model setup and state-restart helper
        batfuns_original_Corrected_Cp.py     cycle simulation and base parameters
    deepSOH_final_sept2026/                  the study: Python simulations, MATLAB analysis
                                             and figures, data; see its README
    deepSOH_archive/
        deepSOH_final_august22_2026/         the August 2026 version (Jupyter notebooks),
                                             kept for reference

## Quick start

    pip install -r deepSOH_final_sept2026/requirements.txt
    python deepSOH_final_sept2026/sim/run_all.py      # all simulations, about 1 hour

then, in MATLAB, run `deepSOH_final_sept2026/matlab/P4_plot_all.m` to rebuild every figure
(about 15 seconds). The simulation data is included, so the figures can be rebuilt without
simulating. `deepSOH_final_sept2026/README.md` describes every file and setting.

## Notes

- The model is built from four constants originally fitted to the cell-07 eSOH and OCV
  measurements (the fresh active-material fractions, the initial state of charge and the cell
  temperature). They are frozen in `deepsoh_p4_model.py`, so no experimental data is needed.
  The duty-cycle optimization that produced the second-use protocol is not included.
- Windows path length: the deepest file in the bundled PyBaMM sits about 165 characters below
  the repository root. On Windows without long-path support, clone into a short folder such
  as `C:\deepSOH` so full paths stay under the 260-character limit. This does not affect
  Linux or macOS.
