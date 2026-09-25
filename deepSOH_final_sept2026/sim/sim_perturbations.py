"""One deepSOH state changed at a time at the start of second use (Figure 5).

Writes data/P4_perturbations.mat:
  case_names       1 x 6
  perturbed_state  1 x 6 name of the changed state ('' for the nominal case)
  multiplier       1 x 6 factor applied to that state
  initial_state    5 x 6
  second_life      trajectory struct, one column per case (NaN-padded), to the 60%
                   capacity termination
"""
import sys
from pathlib import Path
import numpy as np
from scipy.io import loadmat
sys.path.insert(0, str(Path(__file__).resolve().parent))
import p4_io, p4_sim  # noqa: E402

# (case name, index of the changed state in [nLi, Cp, Cn, delta_SEI, delta_pl], factor)
CASES = (("nominal", None, 1.0),
         ("nLi_x0p95", 0, 0.95),
         ("Cp_x0p85", 1, 0.85),
         ("Cn_x0p90", 2, 0.90),
         ("plating_x1p5", 4, 1.5),
         ("SEI_x2", 3, 2.0))


def main(workers=6):
    eofu = loadmat(p4_sim.DATA_DIR / "P4_first_life.mat")["eofu_state"].ravel()
    x0 = np.tile(eofu.reshape(5, 1), (1, len(CASES)))
    for j, (_, i, factor) in enumerate(CASES):
        if i is not None:
            x0[i, j] *= factor
    print("second lives ...", flush=True)
    jobs = [{"label": name, "state": x0[:, j].tolist(), "state_ref": eofu.tolist(),
             "solver": "rk23"} for j, (name, _, _) in enumerate(CASES)]
    runs = p4_sim.run_second_lives(jobs, workers=min(workers, len(CASES)),
                                   work_dir=p4_sim.DATA_DIR / "_work_perturbations")
    names = [c[0] for c in CASES]
    changed = ["" if c[1] is None else p4_io.STATE_NAMES[c[1]] for c in CASES]
    path = p4_io.save_mat(p4_sim.DATA_DIR / "P4_perturbations.mat", {
        "case_names": p4_io.cellstr(names), "perturbed_state": p4_io.cellstr(changed),
        "multiplier": np.array([[c[2] for c in CASES]]), "initial_state": x0,
        "eofu_state": eofu.reshape(5, 1), "second_life": p4_io.stack_runs(runs),
        **p4_sim.run_info("rk23")})
    print("saved", path)


if __name__ == "__main__":
    main()
