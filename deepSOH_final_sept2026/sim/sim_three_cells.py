"""Three cells with the same capacity and resistance at the end of first use (EOFU) but a
different split of the surface film between SEI and plated lithium (Figure 3).

The film resistance x area, rho_SEI*delta_SEI + rho_pl*delta_pl, is kept at its EOFU value
and split between SEI and plating; n_Li, C_p and C_n are the EOFU values. Each cell runs
through the second use to the 60% capacity termination. C/20 tests are then run at the
same three cycles for every cell: cycle 1, and mid-life and end of life of the
fastest-dying cell (end of life = last cycle at or above 3.0 Ah).

Writes data/P4_three_cells.mat:
  cell_names     1 x 3, fastest-dying first
  alpha_SEI      1 x 3 SEI share of the film resistance
  initial_state  5 x 3 deepSOH state of each cell at the start of second use
  second_life    trajectory struct, one column per cell (NaN-padded)
  rpt            C/20 tests: cycles (1 x 3); time_h, voltage_V, current_A
                 (sample x test x cell, NaN-padded); n_samples (test x cell)
"""
import sys
from pathlib import Path
import numpy as np
from scipy.io import loadmat
sys.path.insert(0, str(Path(__file__).resolve().parent))
import p4_io, p4_sim  # noqa: E402

CELL_NAMES = ("low_SEI_high_plating", "moderate_SEI_moderate_plating", "high_SEI_low_plating")
ALPHA_OUTER = (0.1, 0.9)        # SEI share of the film resistance of the first and last cell
MIDDLE_DELTA_PL = 52e-9         # [m] plated lithium of the middle cell
END_OF_LIFE_AH = 3.0


def matched_states(eofu):
    pv = p4_sim.model.BASE_PARAMETER_VALUES
    rho_sei = float(np.asarray(pv["SEI resistivity [Ohm.m]"]).squeeze())
    rho_pl = float(np.asarray(pv["Li plating resistivity [Ohm.m]"]).squeeze())
    film = rho_sei * eofu[3] + rho_pl * eofu[4]
    alpha = np.array([ALPHA_OUTER[0], 1.0 - MIDDLE_DELTA_PL * rho_pl / film, ALPHA_OUTER[1]])
    states = np.tile(eofu.reshape(5, 1), (1, 3))
    states[3, :] = alpha * film / rho_sei
    states[4, :] = (1.0 - alpha) * film / rho_pl
    return alpha, states


def main(workers=3):
    eofu = loadmat(p4_sim.DATA_DIR / "P4_first_life.mat")["eofu_state"].ravel()
    alpha, x0 = matched_states(eofu)
    print("second lives ...", flush=True)
    jobs = [{"label": name, "state": x0[:, c].tolist(), "state_ref": eofu.tolist(),
             "solver": "rk23"} for c, name in enumerate(CELL_NAMES)]
    runs = p4_sim.run_second_lives(jobs, workers=min(workers, 3), work_dir=p4_sim.DATA_DIR / "_work_three_cells")

    lives = [int(r["cycle"][p4_sim.end_of_life_index(r["capacity_Ah"], END_OF_LIFE_AH)]) for r in runs]
    fastest = min(lives)
    test_cycles = [1, int(round(fastest / 2)), fastest]
    print("end of life:", dict(zip(CELL_NAMES, lives)), "-> C/20 tests at cycles", test_cycles, flush=True)

    tests = [[None] * 3 for _ in range(3)]            # [test][cell]
    for c, r in enumerate(runs):
        for s, cyc in enumerate(test_cycles):
            j = int(np.flatnonzero(r["cycle"] == cyc)[0])
            state = [r[k][j] for k in ("nLi_mol", "Cp_Ah", "Cn_Ah", "delta_SEI_m", "delta_pl_m")]
            tests[s][c] = p4_sim.run_c20_test(state, eofu)
    n = max(len(tests[s][c]["time_h"]) for s in range(3) for c in range(3))
    rpt = {"cycles": np.array([test_cycles], dtype=float), "n_samples": np.zeros((3, 3))}
    for f in ("time_h", "voltage_V", "current_A"):
        rpt[f] = np.full((n, 3, 3), np.nan)
        for s in range(3):
            for c in range(3):
                v = tests[s][c][f]
                rpt[f][:len(v), s, c] = v
                rpt["n_samples"][s, c] = len(v)

    path = p4_io.save_mat(p4_sim.DATA_DIR / "P4_three_cells.mat", {
        "cell_names": p4_io.cellstr(CELL_NAMES), "alpha_SEI": alpha.reshape(1, 3),
        "initial_state": x0, "eofu_state": eofu.reshape(5, 1),
        "second_life": p4_io.stack_runs(runs), "rpt": rpt,
        "c20_test_protocol": p4_sim.C20_TEST, **p4_sim.run_info("rk23")})
    print("saved", path)


if __name__ == "__main__":
    main()
