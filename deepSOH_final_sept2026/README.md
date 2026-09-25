# deepSOH, P4 model: simulations and figures

This folder recreates every simulation and figure of the P4 deepSOH study from scratch.
It needs nothing outside this repository.

- **Python** (`sim/`) only runs the PyBaMM simulations. It writes the states and outputs of
  every run to one `.mat` file per problem in `data/`.
- **MATLAB** (`matlab/`) does all the analysis (sensitivities, observability Gramian,
  prediction variance, prediction-error bounds, end-of-life cuts) and draws every figure
  into `figures/`.

```
deepSOH_final_sept2026/
  README.md          this file
  requirements.txt   Python packages, at the tested versions
  sim/               Python: simulations only
  data/              .mat files written by sim/ and read by matlab/
  matlab/            all analysis and figures
  figures/           figures written by matlab/ (.png and .fig)
```

The previous version of this study (August 2026: Jupyter notebooks, CSV data, older MATLAB
scripts) is kept for reference in `../deepSOH_archive/deepSOH_final_august22_2026/`. Nothing
in this folder uses it.

## How to run

### 1. Python environment (once)

Python 3.9. From the repository root:

```
pip install -r deepSOH_final_sept2026/requirements.txt
```

`requirements.txt` pins the versions the data was made with (Python 3.9.13, Windows 11).

The simulation scripts import the **modified PyBaMM in this repository** (`pybamm/` at the
repository root, version 22.8 with the degradation physics) and the P4 model
(`deepSOH/corrected_platin_thick/deepsoh_p4_model.py`) directly; they put the repository
root first on the Python path. Stock PyBaMM will not reproduce the results, so do not
install PyBaMM from PyPI in the same environment. No experimental data is needed: the
values fitted to the cell data are constants in the model file.

Keep scipy below 1.14 to reproduce the data exactly: the model uses
`scipy.interpolate.interp2d`, which scipy 1.14 removed (the scripts then fall back to the
model's own replacement). On Windows without long-path support, clone the repository into
a short folder such as `C:\deepSOH`: the deepest file of the bundled PyBaMM is about 165
characters below the repository root, and Windows limits full paths to 260.

### 2. Simulations (Python)

From this folder:

```
python sim/run_all.py                  # everything, about 1 to 1.5 h with 11 workers
python sim/run_all.py --skip-dop853    # without the DOP853 solver check, 30 to 60 min
python sim/run_all.py --workers 6      # at most 6 simulations at a time (default 11)
```

`run_all.py` runs the scripts below in order. Each can also be run on its own, in this
order: every script needs `P4_first_life.mat` (every run starts from its end-of-first-use
state), and `sim_observability.py` for any of the three cells also needs
`P4_three_cells.mat`, which holds their starting states.

```
python sim/sim_first_life.py                                         # 5 min
python sim/sim_three_cells.py                                        # 3 to 9 min
python sim/sim_perturbations.py                                      # 4 to 6 min
python sim/sim_observability.py --cell nominal                       # 5 to 11 min
python sim/sim_observability.py --cell low_SEI_high_plating          # 5 to 10 min
python sim/sim_observability.py --cell moderate_SEI_moderate_plating # 4 to 9 min
python sim/sim_observability.py --cell high_SEI_low_plating          # 6 to 13 min
python sim/sim_observability.py --cell high_SEI_low_plating --solver dop853   # 30 min
```

The second lives run in parallel, one Python process each (`--workers`, default 11, in
`run_all.py` and `sim_observability.py`). Run times are from a 14-core laptop; the longer
times are with other work running on it.

### 3. Figures (MATLAB)

MATLAB R2020a or newer (tested with R2024b), no toolboxes. In MATLAB, go to the `matlab/`
folder and run

```
P4_plot_all
```

It takes about 15 seconds and writes every figure to `figures/`. Each figure script can also
be run on its own. Figures are drawn off screen; open the `.fig` files to look at them in
MATLAB.

## What each file does

### sim/ (Python)

| File | What it does | Writes |
|---|---|---|
| `run_all.py` | Runs every simulation below, in order. | all of `data/` |
| `p4_sim.py` | Shared PyBaMM setup, imported by the other scripts: the solver settings (RK23 or DOP853), the first-life, second-life and C/20 test protocols, restarting the model from a deepSOH state, extracting the states and outputs of a run (including the irreversible-expansion output equation), and running several second lives in parallel. | nothing by itself |
| `p4_io.py` | The layout of the `.mat` files: stacks runs into matrices (one column per run, NaN-padded), converts names to MATLAB cell arrays, saves. No PyBaMM. | nothing by itself |
| `sim_first_life.py` | First life of the P4 cell (100 cycles) up to the end of first use (EOFU). | `P4_first_life.mat` |
| `sim_three_cells.py` | Three cells with the same EOFU capacity and resistance but a different split of the surface film between SEI and plated lithium (10/90, 26/74 with plating pinned at 52 nm, 90/10 of the film resistance). Runs their second lives, then C/20 tests at cycle 1 and at mid-life and end of life of the fastest-dying cell. | `P4_three_cells.mat` |
| `sim_perturbations.py` | One deepSOH state changed at a time at the start of second use (n_Li x 0.95, C_p x 0.85, C_n x 0.9, delta_pl x 1.5, delta_SEI x 2) and the nominal case. | `P4_perturbations.mat` |
| `sim_observability.py` | For one cell (`--cell`), the nominal run and, for each of the five states, one run with that state times (1 + epsilon) and one times (1 - epsilon), epsilon = 0.01 (`--epsilon`). | `P4_observability_<cell>.mat` |

All second lives use the same cycle (1.25C discharge to 3.0 V, 10 s rest, 2C charge to
4.1 V, CV at 4.1 V to C/50, 0.1 h rest) and run until the capacity falls to 60% of its
starting value. The
3.0 Ah end of life is cut later, in MATLAB.

### matlab/

| File | What it does | Writes to `figures/` |
|---|---|---|
| `P4_plot_all.m` | Runs every figure script below. | all figures |
| `P4_settings.m` | Every analysis setting, in one place: the 3.0 Ah end of life, the record window of Figures 6 and 7, the measurement sets, the measurement uncertainties used for the bounds, the cycle of the printed bound widths, the solver-check cell, colors and labels. Every figure script runs it first. Edit this file to change a setting. Plot layout (figure sizes, axis limits such as Figure 5's 0 to 140 cycles) is in each figure script. | |
| `P4_fig3_three_cells.m` | Figure 3: capacity, resistance and expansion of the three matched cells, and their C/20 voltage curves. | `P4_03_delta_ratio` |
| `P4_fig5_perturbations.m` | Figure 5: capacity and resistance when one state is changed at a time. | `P4_02_independent_perturbations_life` |
| `P4_fig6_fig7_observability.m` | Figure 6: smallest singular value of the observability Gramian from capacity and resistance. Figure 7: average prediction variance V(H) of the future capacity and resistance for seven measurement sets. Also prints V(H) at the last horizon for all nine sets. | `P4_01_observability_sigma_min`, `P4_01_observability_ioptimality_remaining` |
| `P4_fig7_three_cells.m` | Figure 7 for each of the three matched cells. | `P4_three_cells_prediction_variance` |
| `P4_fig_bounds_three_cells.m` | Bounds (+/- 3 sigma) on the average prediction error of capacity and resistance for the three cells, one row per measurement set; prints the bound half-widths (the +/- value) at cycle 52 (`boundsSummaryCycle`). | `P4_three_cell_bounds` |
| `P4_solver_check.m` | Figure 7 from RK23 runs vs DOP853 runs for one cell (`solverCheckCell`), and their ratio. Skipped if the DOP853 data is missing. | `P4_solver_check` |
| `observability_sensitivities.m` | Function. Loads one observability file and returns the sensitivities Psi (eq. 20), the cycles and the nominal outputs, cut at the nominal run's end of life. | |
| `prediction_variance.m` | Function. Average prediction variance (eq. 25) for every horizon, for a given measurement set, measurement uncertainty and predicted outputs. | |
| `end_of_life_index.m` | Function. Last sample before the capacity first drops below the end-of-life capacity. | |
| `save_figure.m` | Function. Saves a figure as `.fig` and `.png` (150 dpi) and closes it; the `.fig` opens visible. | |
| `P4_expansion_uncertainty_notes.md` | Where the 10 um expansion uncertainty in `P4_settings.m` comes from, with references. | |

The four paper figures keep the file names used in the manuscript, so the `.png` files can be
copied into the manuscript's `Figures/` folder unchanged.

### data/ (written by sim/)

| File | Contents |
|---|---|
| `P4_first_life.mat` | `first_life` (trajectory struct, one column) and `eofu_state`, the deepSOH state at the end of first use. Every second life starts from this state or from a change of it. |
| `P4_three_cells.mat` | `cell_names` (fastest-dying first), `alpha_SEI` (SEI share of the film resistance), `initial_state`, `eofu_state` (the state the restarts are built around), `second_life`, and `rpt`, the C/20 tests: `rpt.cycles`, and `rpt.time_h`, `rpt.voltage_V`, `rpt.current_A` as sample x test x cell with `rpt.n_samples` (test x cell). |
| `P4_perturbations.mat` | `case_names`, `perturbed_state`, `multiplier`, `initial_state`, `eofu_state`, `second_life`. |
| `P4_observability_<cell>.mat` | `cell_name`, `epsilon`, `run_names` (nominal, nLi_plus, nLi_minus, Cp_plus, ..., delta_pl_minus), `base_state`, `initial_state`, `second_life`. `<cell>` is `nominal` or one of `low_SEI_high_plating`, `moderate_SEI_moderate_plating`, `high_SEI_low_plating`; `_dop853` is appended for the DOP853 runs. |

**Trajectory structs** (`first_life`, `second_life`): `cycle` is K x 1 (cycle 0 is the start),
`n_samples` is 1 x (number of runs) and gives the length of each run, and every other field
is K x (number of runs), one column per run, NaN after a run ends. Fields: `capacity_Ah`, `resistance_Ohm`,
`expansion_um` (irreversible) and its parts `expansion_SEI_um`, `expansion_plating_um`,
`expansion_LAM_um`, the deepSOH states `nLi_mol`, `Cp_Ah`, `Cn_Ah`, `delta_SEI_m`,
`delta_pl_m`, and the active material fractions `eps_n`, `eps_p`. States are always ordered
[nLi; Cp; Cn; delta_SEI; delta_pl].

Every file also records how it was made: `solver`, `first_life_protocol`,
`second_life_protocol`, `expansion_model` (coefficients and formula), `units`,
`state_names`, `state_units` (and `c20_test_protocol` in `P4_three_cells.mat`).

In Python, read a file with `scipy.io.loadmat`.

### figures/ (written by matlab/)

| File | Figure |
|---|---|
| `P4_03_delta_ratio` | Fig. 3 of the paper |
| `P4_02_independent_perturbations_life` | Fig. 5 |
| `P4_01_observability_sigma_min` | Fig. 6 |
| `P4_01_observability_ioptimality_remaining` | Fig. 7 |
| `P4_three_cells_prediction_variance` | Fig. 7 for each of the three cells |
| `P4_three_cell_bounds` | prediction-error bounds for the three cells |
| `P4_solver_check` | RK23 vs DOP853 |

## Settings you may want to change (`matlab/P4_settings.m`)

| Setting | Meaning | Value |
|---|---|---|
| `capacityCut` | End of second life [Ah]; each curve keeps its last point at or above it. | 3.0 |
| `observabilityLastCycle` | Last cycle of the record in Figures 6 and 7, the window of the paper's figures. `[]` = the nominal cell's end of life (cycle 125). V(H) averages over all remaining cycles, so this changes every point of Figure 7. | 120 |
| `setNames`, `setChannels`, `plotSets` | The measurement sets, their channels, and which of them are plotted. | 9 sets, 7 plotted |
| `sigma3`, `quotedAt`, `bandZ` | Measurement uncertainty of one measurement per channel (quoted at 3 sigma) and the width of the bounds (+/- 3 sigma). Used only for the bounds figure. | capacity 0.1 Ah, resistance 2 mOhm, expansion 10 um, n_Li 0.1 Ah of lithium, C_p 0.022 Ah, C_n 0.052 Ah |
| `boundsSummaryCycle` | Cycle at which the bounds script prints the bound half-widths. | 52 |
| `solverCheckCell` | Cell compared in the solver check; must match the DOP853 run in `sim/run_all.py`. | `high_SEI_low_plating` |

A settings change needs only `P4_plot_all`, not new simulations. Changing a protocol, the
solver, epsilon or a starting state needs the simulations again.

## Method, as implemented

- **Sensitivity (eq. 20)**, `observability_sensitivities.m`:
  `Psi(k, channel, i) = (y_plus - y_minus) / (2*epsilon)`, the change of each output per unit
  relative change of state i. Figures 6 and 7 divide each channel by the nominal run's value
  at cycle 0, so Psi is dimensionless.
- **Gramian (eq. 21)**: `W(H) = sum over the first H cycles of Psi_M' * R^-1 * Psi_M`, where M
  are the recorded channels and R the variances of their measurement noise. Figures 6 and 7
  use the normalized Psi with R = I, the same relative noise on every channel. Figure 6 shows
  the smallest singular value of W for capacity and resistance (cycles 0 and 1 are not
  drawn: W cannot be full rank yet).
- **Average prediction variance (eq. 25)**, `prediction_variance.m`: with a record of cycles
  0 to H-1, the mean over the remaining cycles (H to end of life), and over the predicted
  outputs, of `Psi_m * W(H)^-1 * Psi_m'`, reported at cycle H. W is not inverted directly:
  the SVD of the stacked, noise-weighted rows gives W^-1, which stays accurate when W is
  nearly singular. In Figure 7, V is the prediction variance divided by the common noise
  variance, so the noise level itself drops out; changing it would scale every curve by the
  same factor. The bounds instead use the unnormalized Psi with the 1-sigma uncertainties
  `sigma3 / quotedAt` of `P4_settings.m`, compute V separately for capacity (Ah^2) and for
  resistance (Ohm^2), and draw the bound at cycle H as `+/- bandZ * sqrt(V)`.
- **End of life**: the last cycle before the capacity first drops below 3.0 Ah, the same
  rule in Python (choice of the C/20 test cycles) and MATLAB (every figure).

The simulations are deterministic: rerunning them gives the same data. The nominal run is the
same in every file (the nominal cell of Figures 6 and 7 is the nominal case of Figure 5, and
each cell's observability runs start exactly from its Figure 3 curve).
