"""Re-run the six plotted Figure-5 perturbation cases to a 3.0 Ah floor.

The historical runs stopped at 80% retention (just under 3.6 Ah). This script
re-simulates the six cases shown in the paper's Figure 5 (nominal, nLi x0.95,
Cp x0.85, Cn x0.90, plating x1.5, SEI x2) from their exact stored initial
states, with the same tight RK23 solver and second-use protocol, until the
experiment's 60% capacity termination so every case passes below 3.0 Ah.
The MATLAB plot script applies the 3.0 Ah cut (CAP_CUT).

Each re-run is validated against the stored trajectory (initial state to
2e-5 relative, capacity at cycles 30 and 60 to 5e-4 relative) before the
data files are rewritten. The six unplotted cases keep their original rows.

Rewrites, in data/independent_perturbations/:
  - P4_perturbed_second_life_trajectories.csv  (six cases replaced)
  - P4_historical_perturbation_initial_states.csv  (run stats refreshed)
  - P4_historical_perturbations_summary.json  (extension note appended)
"""
from __future__ import annotations
import importlib, json, os, sys, time
from pathlib import Path
import numpy as np
import pandas as pd

# Repository root, derived from this file so the script runs from any checkout.
MODEL_ROOT = Path(__file__).resolve().parents[2]
MODEL_DIR = MODEL_ROOT / "deepSOH" / "corrected_platin_thick"
DATA = MODEL_ROOT / "deepSOH_final_august22_2026" / "data" / "independent_perturbations"

SECOND_PROTOCOL = (2.0, 1.25, 3.0, 0.1)
SECOND_UPPER_VOLTAGE = 4.1
SECOND_MAX_CYCLES = 260
SOLVER_CONFIG = {"method": "RK23", "rtol": 1e-7, "atol_floor": 1e-14,
                 "atol_relative_to_y0": 1e-9, "first_step_cycles": 10.0}
STATE_COLUMNS = ("nLi_mol", "Cp_Ah", "Cn_Ah", "delta_SEI_m", "delta_pl_m")
CASES = ("nominal", "nLi_x0p95", "Cp_x0p85", "Cn_x0p90", "plating_x1p5", "SEI_x2")

for e in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[e] = "1"
for _d in (MODEL_ROOT, MODEL_ROOT / "deepSOH", MODEL_DIR):
    s = str(_d)
    if s in sys.path:
        sys.path.remove(s)
    sys.path.insert(0, s)
optimizer = importlib.import_module("deepsoh_p4_model")
optimizer.UPPER_VOLTAGE = SECOND_UPPER_VOLTAGE


def install_tight_rk23():
    g = optimizer.batfuns_corrected.cycle_adaptive_simulation_V2.__globals__
    key = "_pertregen_original_solve_ivp"
    if key not in g:
        g[key] = g["solve_ivp"]
    orig = g[key]

    def tight(fun, t_span, y0, **kw):
        y0a = np.asarray(y0, dtype=float)
        kw["method"] = SOLVER_CONFIG["method"]
        kw["rtol"] = SOLVER_CONFIG["rtol"]
        kw["atol"] = np.maximum(SOLVER_CONFIG["atol_floor"],
                                SOLVER_CONFIG["atol_relative_to_y0"] * np.abs(y0a))
        kw["first_step"] = SOLVER_CONFIG["first_step_cycles"]
        kw.pop("max_step", None)
        return orig(fun, t_span, y0, **kw)
    g["solve_ivp"] = tight


def fmt(v):
    return f"{float(v):.2f}".rstrip("0").rstrip(".")


def build_cycle(protocol, upper):
    charge_c, discharge_c, lower_v, rest_h = protocol
    return (f"Discharge at {fmt(discharge_c)}C until {fmt(lower_v)}V",
            f"Rest for {optimizer.POST_DISCHARGE_REST_SECONDS:g} sec",
            f"Charge at {fmt(charge_c)}C until {fmt(upper)}V",
            f"Hold at {fmt(upper)}V until C/{optimizer.CV_CUTOFF_DENOMINATOR}",
            f"Rest for {fmt(rest_h)} hours")


def extract_components(result):
    cyc = np.asarray(result["Cycle number"], dtype=float); cyc -= cyc[0]
    cap = np.asarray(result["Capacity [A.h]"], dtype=float)
    res = np.asarray(result["Local ECM resistance [Ohm]"], dtype=float)
    d_sei = np.asarray(result["X-averaged SEI thickness [m]"], dtype=float)
    d_pl = np.asarray(result["X-averaged effective lithium plating thickness [m]"], dtype=float)
    eps_n = np.asarray(result["X-averaged negative electrode active material volume fraction"], dtype=float)
    eps_p = np.asarray(result["X-averaged positive electrode active material volume fraction"], dtype=float)
    e_sei = 544.61 * d_sei * 1e6
    e_pl = 11004.28 * d_pl ** 2 * 1e12
    e_lam = 413.85 * (float(optimizer.EPS_N_FRESH) - eps_n)
    return {"cycle": cyc, "capacity_Ah": cap, "capacity_retention": cap / cap[0],
            "resistance_Ohm": res, "expansion_um": e_sei + e_pl + e_lam,
            "expansion_SEI_um": e_sei, "expansion_plating_um": e_pl, "expansion_LAMn_um": e_lam,
            "nLi_mol": np.asarray(result["Total lithium in particles [mol]"], dtype=float),
            "Cp_Ah": np.asarray(result["C_p"], dtype=float),
            "Cn_Ah": np.asarray(result["C_n"], dtype=float),
            "delta_SEI_m": d_sei, "delta_pl_m": d_pl, "eps_n": eps_n, "eps_p": eps_p}


def main():
    states = pd.read_csv(DATA / "P4_historical_perturbation_initial_states.csv")
    states_ix = states.set_index("case")
    stored = pd.read_csv(DATA / "P4_perturbed_second_life_trajectories.csv")
    state_ref = np.array([states_ix.loc["nominal", c] for c in STATE_COLUMNS], dtype=float)

    install_tight_rk23()
    optimizer.scipy_interpolate.interp2d = optimizer.scipy_114_compatible_interp2d
    exp = optimizer.pybamm.Experiment(
        [build_cycle(SECOND_PROTOCOL, SECOND_UPPER_VOLTAGE)] * (SECOND_MAX_CYCLES + 1),
        termination="60% capacity")

    new_blocks, stats = [], {}
    for case in CASES:
        tgt = np.array([states_ix.loc[case, c] for c in STATE_COLUMNS], dtype=float)
        template = optimizer.parameter_values_for_state(tgt, state_ref)
        t0 = time.perf_counter()
        res = optimizer.cycle_adaptive_simulation_V2(
            optimizer.pybamm.lithium_ion.SPM(dict(optimizer.SPM_MODEL_OPTIONS)),
            template.copy(), exp, SOC_0=1, save_at_cycles=1)
        elapsed = time.perf_counter() - t0
        comp = extract_components(res)
        act = np.array([comp[c][0] for c in STATE_COLUMNS], dtype=float)
        err = float(np.max(np.abs(act - tgt) / state_ref))
        if err > 2e-5:
            raise AssertionError(f"{case}: init mismatch {err:.2e}")
        s = stored[(stored.case == case) & (stored.phase == "second_life")]
        for chk in (30, 60):
            old = float(s[s.cycle == chk].capacity_Ah.iloc[0])
            j = int(np.argmin(np.abs(comp["cycle"] - chk)))
            new = float(comp["capacity_Ah"][j])
            if abs(new - old) / old > 5e-4:
                raise AssertionError(f"{case}: cycle {chk} {new:.5f} vs stored {old:.5f}")
        n = len(comp["cycle"])
        block = pd.DataFrame({"phase": ["second_life"] * n, "case": [case] * n,
                              "label": [states_ix.loc[case, "label"]] * n, **comp})
        new_blocks.append(block)
        stats[case] = {"safe_last_cycle": int(comp["cycle"][-1]),
                       "safe_final_retention": float(comp["capacity_retention"][-1]),
                       "simulation_seconds": elapsed,
                       "maximum_scaled_initial_error": err}
        cap = comp["capacity_Ah"]
        b30 = np.flatnonzero(cap < 3.0)
        print(f"{case}: {int(comp['cycle'][-1])} cycles, final {cap[-1]:.3f} Ah, "
              f"crosses 3.0 Ah after cycle {int(comp['cycle'][b30[0]-1]) if b30.size else 'never'}"
              f"  ({elapsed:.0f}s)", flush=True)

    keep = stored[~stored.case.isin(CASES)]
    combined = pd.concat([pd.concat(new_blocks, ignore_index=True), keep], ignore_index=True)
    combined.to_csv(DATA / "P4_perturbed_second_life_trajectories.csv", index=False)

    for case, st in stats.items():
        for col, val in st.items():
            states.loc[states.case == case, col] = val
    states.to_csv(DATA / "P4_historical_perturbation_initial_states.csv", index=False)

    summary = json.loads((DATA / "P4_historical_perturbations_summary.json").read_text(encoding="utf-8"))
    summary["second_use_extension_2026_09_01"] = {
        "note": ("The six plotted cases were re-simulated from their stored initial "
                 "states to the experiment's 60% capacity termination so the life "
                 "figure can be cut at 3.0 Ah instead of 3.6 Ah. Reproduction of the "
                 "historical trajectories was verified at cycles 30 and 60 to 5e-4 "
                 "relative before replacement. Unplotted cases keep the original runs."),
        "script": "sim/regenerate_perturbations_to_3Ah.py",
        "figure_cut_Ah": 3.0,
        "cases": {c: stats[c]["safe_last_cycle"] for c in CASES},
    }
    (DATA / "P4_historical_perturbations_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8")
    print("data files rewritten", flush=True)


if __name__ == "__main__":
    main()
