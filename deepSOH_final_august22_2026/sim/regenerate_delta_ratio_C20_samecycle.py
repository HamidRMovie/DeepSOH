"""Re-run the delta-ratio C/20 RPTs at the SAME cycles for all three cases.

The begin/middle/end cycles are taken from the fastest-dying case
(minimum safe_last_cycle): cycle 1, round(RUL/2), and RUL. Every case is then
probed at those same three cycles, so the C/20 comparison is at matched cycle
(not matched state-of-health). Overwrites P4_three_matched_second_life_C20_RPTs.csv.
The second-life trajectories (already run to 3 Ah) are reused as-is.
"""
from __future__ import annotations
import importlib, json, os, sys
from pathlib import Path
import numpy as np
import pandas as pd

# Repository root, derived from this file so the script runs from any checkout.
MODEL_ROOT = Path(__file__).resolve().parents[2]
MODEL_DIR = MODEL_ROOT / "deepSOH" / "corrected_platin_thick"
DATA = MODEL_ROOT / "deepSOH_final_august22_2026" / "data" / "delta_ratio"

RPT_UPPER_VOLTAGE, RPT_LOWER_VOLTAGE = 4.2, 3.0
RPT_RATE, RPT_CV_CUTOFF = "C/20", "C/100"
RPT_SOLVER = {"mode": "safe", "rtol": 1e-6, "atol": 1e-6, "dt_max": 0.1}
STAGE_ORDER = ("beginning", "middle", "end")

for _d in (MODEL_ROOT, MODEL_ROOT / "deepSOH", MODEL_DIR):
    s = str(_d)
    if s in sys.path:
        sys.path.remove(s)
    sys.path.insert(0, s)
optimizer = importlib.import_module("deepsoh_p4_model")
optimizer.UPPER_VOLTAGE = 4.1


def run_one_c20_rpt(sel, state_ref):
    optimizer.scipy_interpolate.interp2d = optimizer.scipy_114_compatible_interp2d
    tgt = np.array([sel[k] for k in ("nLi_mol", "Cp_Ah", "Cn_Ah", "delta_SEI_m", "delta_pl_m")], dtype=float)
    pv = optimizer.parameter_values_for_state(tgt, state_ref)
    exp = optimizer.pybamm.Experiment([(f"Charge at {RPT_RATE} until {RPT_UPPER_VOLTAGE}V",
                                        f"Hold at {RPT_UPPER_VOLTAGE}V until {RPT_CV_CUTOFF}",
                                        f"Discharge at {RPT_RATE} until {RPT_LOWER_VOLTAGE}V")],
                                       termination="50% capacity")
    sim = optimizer.pybamm.Simulation(
        optimizer.pybamm.lithium_ion.SPM(dict(optimizer.SPM_MODEL_OPTIONS)),
        experiment=exp, parameter_values=pv, solver=optimizer.pybamm.CasadiSolver(**RPT_SOLVER))
    sol = sim.solve(initial_soc=0)
    t = np.asarray(sol["Time [s]"].entries, dtype=float)
    v = np.asarray(sol["Terminal voltage [V]"].entries, dtype=float)
    c = np.asarray(sol["Current [A]"].entries, dtype=float)
    return pd.DataFrame({"case": sel["case"], "label": sel["label"], "stage": sel["stage"],
                         "requested_cycle": sel["requested_cycle"], "actual_cycle": sel["actual_cycle"],
                         "time_s": t, "time_h": t / 3600, "voltage_V": v, "current_A": c})


def main():
    for e in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        os.environ[e] = "1"
    traj = pd.read_csv(DATA / "P4_three_matched_second_life_trajectories.csv")
    states = pd.read_csv(DATA / "P4_matched_initial_states.csv")
    summary = json.loads((DATA / "P4_three_matched_second_life_summary.json").read_text())
    state_ref = np.array([summary["EOFU_reference_state"][n] for n in optimizer.STATE_NAMES], dtype=float)

    # begin/middle/end cycles from the fastest-dying case
    fastest = states.loc[states["safe_last_cycle"].idxmin()]
    rul_fast = int(fastest["safe_last_cycle"])
    fixed = {"beginning": 1, "middle": int(round(rul_fast / 2)), "end": rul_fast}
    print(f"Fastest-dying case: {fastest['case']} (RUL {rul_fast}). "
          f"Fixed cycles: {fixed['beginning']}/{fixed['middle']}/{fixed['end']}", flush=True)

    rows = []
    for _, st in states.iterrows():
        case = st["case"]
        blk = traj[traj["case"] == case].sort_values("cycle")
        cyc = blk["cycle"].to_numpy(dtype=float)
        for stage in STAGE_ORDER:
            want = fixed[stage]
            j = int(np.argmin(np.abs(cyc - want)))
            r = blk.iloc[j]
            sel = {"case": case, "label": st["label"], "stage": stage,
                   "requested_cycle": want, "actual_cycle": int(round(float(r["cycle"]))),
                   "nLi_mol": float(r["nLi_mol"]), "Cp_Ah": float(r["Cp_Ah"]),
                   "Cn_Ah": float(r["Cn_Ah"]), "delta_SEI_m": float(r["delta_SEI_m"]),
                   "delta_pl_m": float(r["delta_pl_m"])}
            print(f"  C/20 {case} {stage}: cycle {sel['actual_cycle']} "
                  f"(cap {float(r['capacity_Ah']):.3f} Ah)", flush=True)
            rows.append(run_one_c20_rpt(sel, state_ref))
    out = pd.concat(rows, ignore_index=True)
    out.to_csv(DATA / "P4_three_matched_second_life_C20_RPTs.csv", index=False)
    print("Wrote", DATA / "P4_three_matched_second_life_C20_RPTs.csv", flush=True)


if __name__ == "__main__":
    main()
