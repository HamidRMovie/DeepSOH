# deepSOH: physics-based state of health for lithium-ion batteries

Code and data behind the figures in the deepSOH manuscript. deepSOH is the
state vector of a physics-based degradation model, comprising the cyclable
lithium, the two electrode capacities, and the thicknesses of the SEI layer and
of plated lithium. This repository lets you both re-simulate the study and
re-plot every figure.

It bundles a modified copy of [PyBaMM](https://github.com/pybamm-team/PyBaMM)
(v22.8) that carries the SEI, lithium-plating and kinetics changes the model
relies on. Stock PyBaMM will not reproduce the results.

## Layout

    pybamm/                              modified PyBaMM (BSD-3, see LICENSE.txt)
    deepSOH/corrected_platin_thick/
        deepsoh_p4_model.py             P4 model setup and state-restart helper
        batfuns_original_Corrected_Cp.py  cycle simulation and base parameters
    deepSOH_final_august22_2026/
        data/                           simulation outputs the notebooks read
        outputs/                        figures and metric tables the notebooks write
        matlab/                         MATLAB plot scripts, .fig and .png figures
        sim/                            scripts that re-run the simulations
        P4_01_Observability_*.ipynb     observability metrics (Figures 6 and 7)
        P4_02_Independent_Perturbations_*.ipynb   perturbation figure (Figure 5)
        P4_03_Delta_Ratio_*.ipynb       three-cell delta-ratio figure (Figure 3)

## Requirements

Python 3.9 or later with `numpy`, `scipy`, `pandas`, `casadi`, `matplotlib` and
`jupyter`. Install the bundled PyBaMM's own dependencies, then put the three
source folders on the path (the scripts do this themselves from their own
location). MATLAB R2024b or later is needed only for the `.m` plot scripts.

## Reproduce the figures without re-simulating

The three notebooks are replot-only. They read `data/` and write `outputs/` and
the MATLAB `.mat` files, so every figure is regenerated in about a minute
without running PyBaMM. Run each notebook from the `deepSOH_final_august22_2026`
folder, then run the MATLAB scripts in `matlab/` to rebuild the `.fig` and
`.png` figures.

## Re-run the simulations

The scripts in `sim/` re-run the underlying simulations against the bundled
PyBaMM and overwrite the corresponding `data/` files, after which the notebooks
replot from the new data. Each script takes roughly ten to twenty minutes.

## Notes

- The model is built from four constants that were originally fitted to the
  cell-07 eSOH and OCV measurements (the fresh active-material fractions, the
  initial state of charge and the cell temperature). These are frozen in
  `deepsoh_p4_model.py`, so no experimental data is needed. The duty-cycle
  optimization that produced the second-use protocol is not included.
- Windows path length: the deepest file in the bundled PyBaMM sits about 164
  characters below the repository root. On Windows without long-path support,
  clone into a short directory such as `C:\deepSOH` so the full path stays
  under the 260-character limit. This does not affect Linux or macOS.
