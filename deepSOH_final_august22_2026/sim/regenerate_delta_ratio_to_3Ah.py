"""Re-run the P4 matched-resistance delta-ratio second lives to a 3 Ah floor.

Reproduces the accepted P4 method (tight historical RK23) from
GPT/.../P4_three_matched_second_life, but the second use now runs until the
absolute capacity reaches 3.0 Ah instead of the 80% relative floor. Writes new
CSV/JSON into deepSOH_final_august22_2026/data/delta_ratio/.
"""
from __future__ import annotations
import importlib, json, os, sys, time
from pathlib import Path
import numpy as np
import pandas as pd

# Repository root, derived from this file so the script runs from any checkout.
MODEL_ROOT = Path(__file__).resolve().parents[2]
MODEL_DIR = MODEL_ROOT / "deepSOH" / "corrected_platin_thick"
OUTPUT_ROOT = MODEL_ROOT / "deepSOH_final_august22_2026" / "data" / "delta_ratio"

FIRST_PROTOCOL = (1.5, 1.25, 3.1, 0.1)
FIRST_CYCLES = 100
FIRST_UPPER_VOLTAGE = 4.1
SECOND_PROTOCOL = (2.0, 1.25, 3.0, 0.1)
SECOND_UPPER_VOLTAGE = 4.1
SECOND_MAX_CYCLES = 1500
CAPACITY_FLOOR_AH = 3.0                 # <-- new absolute floor
# middle case pins delta_pl to exactly 52 nm (changed 2026-08-30; was 0.5)
ALPHA_SEI_FILM_ASR = np.asarray((0.1, 1.0 - 52e-9 / 7.036158841434001e-08, 0.9), dtype=float)

SOLVER_CONFIG = {"method": "RK23", "rtol": 1e-7, "atol_floor": 1e-14,
                 "atol_relative_to_y0": 1e-9, "first_step_cycles": 10.0}
RPT_UPPER_VOLTAGE, RPT_LOWER_VOLTAGE = 4.2, 3.0
RPT_RATE, RPT_CV_CUTOFF = "C/20", "C/100"
RPT_SOLVER = {"mode": "safe", "rtol": 1e-6, "atol": 1e-6, "dt_max": 0.1}

CASE_INFO = (
    ("low_SEI_high_plating", "Low SEI / high plating", "#666666", "o"),
    ("moderate_SEI_moderate_plating", "26% SEI / 74% plating", "#E69F00", "s"),
    ("high_SEI_low_plating", "High SEI / low plating", "#0072B2", "^"),
)
STAGE_ORDER = ("beginning", "middle", "end")

for _d in (MODEL_ROOT, MODEL_ROOT / "deepSOH", MODEL_DIR):
    s = str(_d)
    if s in sys.path:
        sys.path.remove(s)
    sys.path.insert(0, s)
optimizer = importlib.import_module("deepsoh_p4_model")
optimizer.UPPER_VOLTAGE = FIRST_UPPER_VOLTAGE


def scalar(v):
    return float(np.asarray(v).squeeze())


def install_tight_rk23():
    g = optimizer.batfuns_corrected.cycle_adaptive_simulation_V2.__globals__
    key = "_regen3ah_original_solve_ivp"
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


def safe_index_3ah(comp):
    cap = comp["capacity_Ah"]
    below = np.flatnonzero(cap < CAPACITY_FLOOR_AH)
    idx = int(below[0]) - 1 if below.size else len(cap) - 1
    if idx < 0:
        raise RuntimeError("Second life starts below the 3 Ah floor")
    return idx


def table(comp, **ids):
    n = len(comp["cycle"])
    return pd.DataFrame({**{k: [v] * n for k, v in ids.items()}, **comp})


def run_first_life():
    install_tight_rk23()
    exp = optimizer.pybamm.Experiment(
        [build_cycle(FIRST_PROTOCOL, FIRST_UPPER_VOLTAGE)] * (FIRST_CYCLES + 1),
        termination="1% capacity")
    res = optimizer.cycle_adaptive_simulation_V2(
        optimizer.pybamm.lithium_ion.SPM(dict(optimizer.SPM_MODEL_OPTIONS)),
        optimizer.BASE_PARAMETER_VALUES.copy(), exp, optimizer.INITIAL_SOC, save_at_cycles=1)
    comp = extract_components(res)
    if not np.isclose(comp["cycle"][-1], FIRST_CYCLES, atol=1e-8):
        raise RuntimeError(f"First life ended at {comp['cycle'][-1]:g}")
    state_ref = np.asarray(optimizer.extract_deepsoh_state(res, -1), dtype=float)
    return comp, state_ref


def build_matched_states(state_ref):
    rho_sei = scalar(optimizer.BASE_PARAMETER_VALUES["SEI resistivity [Ohm.m]"])
    rho_pl = scalar(optimizer.BASE_PARAMETER_VALUES["Li plating resistivity [Ohm.m]"])
    target_asr = rho_sei * state_ref[3] + rho_pl * state_ref[4]
    rows, templates = [], []
    for i, alpha in enumerate(ALPHA_SEI_FILM_ASR):
        key, label, color, marker = CASE_INFO[i]
        tgt = state_ref.copy()
        tgt[3] = alpha * target_asr / rho_sei
        tgt[4] = (1.0 - alpha) * target_asr / rho_pl
        built = rho_sei * tgt[3] + rho_pl * tgt[4]
        templates.append(optimizer.parameter_values_for_state(tgt, state_ref))
        rows.append({"case": key, "label": label,
                     "alpha_SEI_film_ASR": float(alpha), "alpha_plating_film_ASR": float(1 - alpha),
                     "nLi_mol": float(tgt[0]), "Cp_Ah": float(tgt[1]), "Cn_Ah": float(tgt[2]),
                     "delta_SEI_m": float(tgt[3]), "delta_pl_m": float(tgt[4]),
                     "target_film_ASR_Ohm_m2": float(target_asr),
                     "constructed_film_ASR_Ohm_m2": float(built),
                     "color": color, "marker": marker})
    return pd.DataFrame(rows), templates, rho_sei, rho_pl, target_asr


def simulate_second_case(case_row, template, state_ref):
    install_tight_rk23()
    optimizer.scipy_interpolate.interp2d = optimizer.scipy_114_compatible_interp2d
    exp = optimizer.pybamm.Experiment(
        [build_cycle(SECOND_PROTOCOL, SECOND_UPPER_VOLTAGE)] * (SECOND_MAX_CYCLES + 1),
        termination="50% capacity")
    t0 = time.perf_counter()
    res = optimizer.cycle_adaptive_simulation_V2(
        optimizer.pybamm.lithium_ion.SPM(dict(optimizer.SPM_MODEL_OPTIONS)),
        template.copy(), exp, SOC_0=1, save_at_cycles=1)
    elapsed = time.perf_counter() - t0
    comp = extract_components(res)
    idx = safe_index_3ah(comp)
    comp = {k: np.asarray(v)[:idx + 1] for k, v in comp.items()}
    tgt = np.array([case_row["nLi_mol"], case_row["Cp_Ah"], case_row["Cn_Ah"],
                    case_row["delta_SEI_m"], case_row["delta_pl_m"]], dtype=float)
    act = np.array([comp["nLi_mol"][0], comp["Cp_Ah"][0], comp["Cn_Ah"][0],
                    comp["delta_SEI_m"][0], comp["delta_pl_m"][0]], dtype=float)
    err = float(np.max(np.abs(act - tgt) / state_ref))
    if err > 2e-6:
        raise AssertionError(f"{case_row['case']}: init mismatch {err}")
    return comp, elapsed, err


def run_one_c20_rpt(selection, state_ref):
    optimizer.scipy_interpolate.interp2d = optimizer.scipy_114_compatible_interp2d
    tgt = np.array([selection[k] for k in ("nLi_mol", "Cp_Ah", "Cn_Ah", "delta_SEI_m", "delta_pl_m")], dtype=float)
    pv = optimizer.parameter_values_for_state(tgt, state_ref)
    exp = optimizer.pybamm.Experiment([(f"Charge at {RPT_RATE} until {RPT_UPPER_VOLTAGE}V",
                                        f"Hold at {RPT_UPPER_VOLTAGE}V until {RPT_CV_CUTOFF}",
                                        f"Discharge at {RPT_RATE} until {RPT_LOWER_VOLTAGE}V")],
                                       termination="50% capacity")
    sim = optimizer.pybamm.Simulation(
        optimizer.pybamm.lithium_ion.SPM(dict(optimizer.SPM_MODEL_OPTIONS)),
        experiment=exp, parameter_values=pv,
        solver=optimizer.pybamm.CasadiSolver(**RPT_SOLVER))
    sol = sim.solve(initial_soc=0)
    t = np.asarray(sol["Time [s]"].entries, dtype=float)
    v = np.asarray(sol["Terminal voltage [V]"].entries, dtype=float)
    c = np.asarray(sol["Current [A]"].entries, dtype=float)
    return pd.DataFrame({"case": selection["case"], "label": selection["label"],
                         "stage": selection["stage"], "actual_cycle": selection["actual_cycle"],
                         "time_s": t, "time_h": t / 3600, "voltage_V": v, "current_A": c})


def main():
    for e in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        os.environ[e] = "1"
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    print("First life ...", flush=True)
    first_comp, state_ref = run_first_life()
    first_table = table(first_comp, phase="first_life")

    states, templates, rho_sei, rho_pl, target_asr = build_matched_states(state_ref)
    print(states[["case", "delta_SEI_m", "delta_pl_m"]].to_string(index=False), flush=True)

    tables, extra = [], {}
    for i, (_, row) in enumerate(states.iterrows()):
        case = row["case"]
        print(f"Second life to 3 Ah: {case} ...", flush=True)
        comp, elapsed, err = simulate_second_case(row.to_dict(), templates[i], state_ref)
        tables.append(table(comp, phase="second_life", case=case, label=row["label"]))
        extra[case] = {"comp": comp, "elapsed": elapsed, "err": err}
        print(f"  {case}: safe_last_cycle={int(comp['cycle'][-1])} "
              f"final_cap={comp['capacity_Ah'][-1]:.4f} Ah  ({elapsed:.0f}s)", flush=True)
    second_table = pd.concat(tables, ignore_index=True)

    # augment states table
    for col, fn in (("initial_capacity_Ah", lambda c: c["capacity_Ah"][0]),
                    ("initial_resistance_Ohm", lambda c: c["resistance_Ohm"][0]),
                    ("safe_last_cycle", lambda c: int(c["cycle"][-1])),
                    ("safe_final_capacity_Ah", lambda c: c["capacity_Ah"][-1]),
                    ("safe_final_retention", lambda c: c["capacity_retention"][-1])):
        states[col] = [fn(extra[k]["comp"]) for k in states["case"]]
    states["simulation_seconds"] = [extra[k]["elapsed"] for k in states["case"]]
    states["maximum_scaled_initial_error"] = [extra[k]["err"] for k in states["case"]]

    # C/20 RPTs at beginning / middle / end of each case's 3 Ah life
    sel_rows = []
    for _, row in states.iterrows():
        case = row["case"]
        blk = second_table[second_table["case"] == case].sort_values("cycle")
        last = int(round(float(blk["cycle"].max())))
        req = {"beginning": min(1, last), "middle": int(round(last / 2)), "end": last}
        cyc = blk["cycle"].to_numpy(dtype=float)
        for stage in STAGE_ORDER:
            j = int(np.argmin(np.abs(cyc - req[stage])))
            r = blk.iloc[j]
            sel_rows.append({"case": case, "label": row["label"], "stage": stage,
                             "requested_cycle": int(req[stage]), "actual_cycle": int(round(float(r["cycle"]))),
                             "nLi_mol": float(r["nLi_mol"]), "Cp_Ah": float(r["Cp_Ah"]),
                             "Cn_Ah": float(r["Cn_Ah"]), "delta_SEI_m": float(r["delta_SEI_m"]),
                             "delta_pl_m": float(r["delta_pl_m"])})
    rpt_tables = []
    for sel in sel_rows:
        print(f"C/20 RPT: {sel['case']} {sel['stage']} (cycle {sel['actual_cycle']}) ...", flush=True)
        rpt_tables.append(run_one_c20_rpt(sel, state_ref))
    rpt_table = pd.concat(rpt_tables, ignore_index=True)

    # write outputs (overwrite the delta_ratio data used by NB03)
    first_table.to_csv(OUTPUT_ROOT / "P4_optimized_first_life_trajectory.csv", index=False)
    second_table.to_csv(OUTPUT_ROOT / "P4_three_matched_second_life_trajectories.csv", index=False)
    states.to_csv(OUTPUT_ROOT / "P4_matched_initial_states.csv", index=False)
    rpt_table.to_csv(OUTPUT_ROOT / "P4_three_matched_second_life_C20_RPTs.csv", index=False)
    summary = {"model": "P4", "second_use_floor": "3.0 Ah absolute",
               "solver": SOLVER_CONFIG, "capacity_floor_Ah": CAPACITY_FLOOR_AH,
               "first_protocol": FIRST_PROTOCOL, "second_protocol": SECOND_PROTOCOL,
               "EOFU_reference_state": dict(zip(optimizer.STATE_NAMES, state_ref.tolist())),
               "rho_SEI_Ohm_m": rho_sei, "rho_plating_Ohm_m": rho_pl,
               "target_film_ASR_Ohm_m2": float(target_asr),
               "cases": states[["case", "safe_last_cycle", "safe_final_capacity_Ah",
                                 "safe_final_retention"]].to_dict("records")}
    (OUTPUT_ROOT / "P4_three_matched_second_life_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8")

    print("\nDONE. safe_last_cycle by case:", flush=True)
    print(states[["case", "initial_capacity_Ah", "initial_resistance_Ohm",
                  "safe_last_cycle", "safe_final_capacity_Ah"]].to_string(index=False), flush=True)


if __name__ == "__main__":
    main()
