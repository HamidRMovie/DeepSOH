"""Runs for the empirical observability Gramian of one cell (Figures 6 and 7, bounds).

The nominal run starts from the cell's deepSOH state; for each of the five states, one
run starts with that state multiplied by (1 + epsilon) and one by (1 - epsilon). All runs
go through the second use to the 60% capacity termination. MATLAB computes Psi, the
Gramian and the prediction variances from these trajectories.

  python sim_observability.py --cell nominal                 (Figures 6 and 7)
  python sim_observability.py --cell low_SEI_high_plating    (one of the three cells)
  options: --solver rk23|dop853  --epsilon 0.01  --workers 11

Writes data/P4_observability_<cell>.mat (with _dop853 appended for that solver):
  cell_name, epsilon
  run_names      1 x 11: nominal, nLi_plus, nLi_minus, Cp_plus, ..., delta_pl_minus
  base_state     5 x 1 state of the nominal run
  initial_state  5 x 11
  second_life    trajectory struct, one column per run (NaN-padded)
"""
import argparse, sys
from pathlib import Path
import numpy as np
from scipy.io import loadmat
sys.path.insert(0, str(Path(__file__).resolve().parent))
import p4_io, p4_sim  # noqa: E402

THREE_CELLS = ("low_SEI_high_plating", "moderate_SEI_moderate_plating", "high_SEI_low_plating")


def base_state(cell):
    eofu = loadmat(p4_sim.DATA_DIR / "P4_first_life.mat")["eofu_state"].ravel()
    if cell == "nominal":
        return eofu, eofu
    d = loadmat(p4_sim.DATA_DIR / "P4_three_cells.mat")
    names = [str(x[0]) for x in d["cell_names"].ravel()]
    return d["initial_state"][:, names.index(cell)], eofu


def main(cell, solver, epsilon, workers):
    base, eofu = base_state(cell)
    names, states = ["nominal"], [base.copy()]
    for i, state in enumerate(p4_io.STATE_NAMES):
        for sign, tag in ((1, "plus"), (-1, "minus")):
            x = base.copy()
            x[i] *= 1 + sign * epsilon
            names.append(f"{state}_{tag}")
            states.append(x)
    print(f"{cell}, {solver}: {len(names)} runs ...", flush=True)
    jobs = [{"label": n, "state": s.tolist(), "state_ref": eofu.tolist(), "solver": solver}
            for n, s in zip(names, states)]
    suffix = "" if solver == "rk23" else f"_{solver}"
    runs = p4_sim.run_second_lives(jobs, workers,
                                   p4_sim.DATA_DIR / f"_work_observability_{cell}{suffix}")
    path = p4_io.save_mat(p4_sim.DATA_DIR / f"P4_observability_{cell}{suffix}.mat", {
        "cell_name": cell, "epsilon": float(epsilon), "run_names": p4_io.cellstr(names),
        "base_state": base.reshape(5, 1), "initial_state": np.column_stack(states),
        "second_life": p4_io.stack_runs(runs), **p4_sim.run_info(solver)})
    print("saved", path)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--cell", required=True, choices=("nominal",) + THREE_CELLS)
    ap.add_argument("--solver", default="rk23", choices=sorted(p4_sim.SOLVERS))
    ap.add_argument("--epsilon", type=float, default=0.01)
    ap.add_argument("--workers", type=int, default=11)
    a = ap.parse_args()
    if a.workers < 1:
        ap.error("--workers must be at least 1")
    main(a.cell, a.solver, a.epsilon, a.workers)
