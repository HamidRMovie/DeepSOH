"""PyBaMM setup shared by the P4 simulation scripts: solver, protocols, restart from a
deepSOH state, and the states and outputs saved for every run.

Also a worker: `python p4_sim.py <jobs.json> <index>` runs one second life of a job list
written by run_second_lives(), in its own process.
"""
from __future__ import annotations
import importlib, json, os, shutil, subprocess, sys, time
from pathlib import Path
import numpy as np
import scipy

SCIPY_VERSION = tuple(int(v) for v in scipy.__version__.split(".")[:2])

for _v in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_v] = "1"

REPO = Path(__file__).resolve().parents[2]              # PyBaMM_P4
MODEL_DIR = REPO / "deepSOH" / "corrected_platin_thick"
DATA_DIR = Path(__file__).resolve().parents[1] / "data"
for _d in (REPO, REPO / "deepSOH", MODEL_DIR):
    if str(_d) in sys.path:
        sys.path.remove(str(_d))
    sys.path.insert(0, str(_d))
model = importlib.import_module("deepsoh_p4_model")      # the P4 degradation model
model.UPPER_VOLTAGE = 4.1

sys.path.insert(0, str(Path(__file__).resolve().parent))
import p4_io  # noqa: E402

# ---------------------------------------------------------------- settings
FIRST_LIFE = {"charge_C": 1.5, "discharge_C": 1.25, "lower_V": 3.1, "upper_V": 4.1,
              "rest_h": 0.1, "cv_cutoff": "C/50", "cycles": 100}
SECOND_LIFE = {"charge_C": 2.0, "discharge_C": 1.25, "lower_V": 3.0, "upper_V": 4.1,
               "rest_h": 0.1, "cv_cutoff": "C/50", "max_cycles": 260,
               "termination": "60% capacity"}
C20_TEST = {"rate": "C/20", "upper_V": 4.2, "lower_V": 3.0, "cv_cutoff": "C/100",
            "initial_soc": 0.0, "solver_mode": "safe", "rtol": 1e-6, "atol": 1e-6, "dt_max": 0.1}
SOLVERS = {
    "rk23": {"method": "RK23", "rtol": 1e-7, "atol_floor": 1e-14,
             "atol_relative_to_y0": 1e-9, "first_step_cycles": 10.0},
    "dop853": {"method": "DOP853", "rtol": 1e-7, "atol_floor": 1e-14,
               "atol_relative_to_y0": 1e-9, "max_step_cycles": 1.0},
}
# irreversible expansion (Pannala et al. 2024): output equation on the states
EXPANSION = {"b_SEI": 544.61, "b_pl": 11004.28, "b_LAM": 413.85,
             "eps_n_fresh": float(model.EPS_N_FRESH),
             "formula": ("expansion_um = b_SEI*delta_SEI_m*1e6 + b_pl*delta_pl_m^2*1e12"
                         " + b_LAM*(eps_n_fresh - eps_n)")}


def use_solver(name):
    """Route the cycle-adaptive integrator through the chosen solver settings."""
    cfg = SOLVERS[name]
    g = model.batfuns_corrected.cycle_adaptive_simulation_V2.__globals__
    if "_p4_original_solve_ivp" not in g:
        g["_p4_original_solve_ivp"] = g["solve_ivp"]
    original = g["_p4_original_solve_ivp"]

    def solve_ivp(fun, t_span, y0, **kw):
        kw["method"] = cfg["method"]
        kw["rtol"] = cfg["rtol"]
        kw["atol"] = np.maximum(cfg["atol_floor"],
                                cfg["atol_relative_to_y0"] * np.abs(np.asarray(y0, dtype=float)))
        if "first_step_cycles" in cfg:
            kw["first_step"] = cfg["first_step_cycles"]
        if "max_step_cycles" in cfg:
            kw["max_step"] = cfg["max_step_cycles"]
        else:
            kw.pop("max_step", None)
        return original(fun, t_span, y0, **kw)

    g["solve_ivp"] = solve_ivp


def cycle_steps(p):
    f = lambda v: f"{float(v):.2f}".rstrip("0").rstrip(".")
    return (f"Discharge at {f(p['discharge_C'])}C until {f(p['lower_V'])}V",
            f"Rest for {model.POST_DISCHARGE_REST_SECONDS:g} sec",
            f"Charge at {f(p['charge_C'])}C until {f(p['upper_V'])}V",
            f"Hold at {f(p['upper_V'])}V until C/{model.CV_CUTOFF_DENOMINATOR}",
            f"Rest for {f(p['rest_h'])} hours")


def trajectory(result):
    """States and outputs of a cycle-adaptive run, one value per cycle (cycle 0 first)."""
    get = lambda key: np.asarray(result[key], dtype=float)
    cycle = get("Cycle number")
    d_sei = get("X-averaged SEI thickness [m]")
    d_pl = get("X-averaged effective lithium plating thickness [m]")
    eps_n = get("X-averaged negative electrode active material volume fraction")
    e = EXPANSION
    t = {"cycle": cycle - cycle[0],
         "capacity_Ah": get("Capacity [A.h]"),
         "resistance_Ohm": get("Local ECM resistance [Ohm]"),
         "expansion_SEI_um": e["b_SEI"] * d_sei * 1e6,
         "expansion_plating_um": e["b_pl"] * d_pl ** 2 * 1e12,
         "expansion_LAM_um": e["b_LAM"] * (e["eps_n_fresh"] - eps_n),
         "nLi_mol": get("Total lithium in particles [mol]"),
         "Cp_Ah": get("C_p"), "Cn_Ah": get("C_n"),
         "delta_SEI_m": d_sei, "delta_pl_m": d_pl, "eps_n": eps_n,
         "eps_p": get("X-averaged positive electrode active material volume fraction")}
    t["expansion_um"] = t["expansion_SEI_um"] + t["expansion_plating_um"] + t["expansion_LAM_um"]
    return t


def initial_state(t):
    return np.array([t["nLi_mol"][0], t["Cp_Ah"][0], t["Cn_Ah"][0],
                     t["delta_SEI_m"][0], t["delta_pl_m"][0]], dtype=float)


def run_first_life(solver="rk23"):
    use_solver(solver)
    if SCIPY_VERSION >= (1, 14):          # scipy 1.14 removed interp2d, which the first life uses
        model.scipy_interpolate.interp2d = model.scipy_114_compatible_interp2d
    exp = model.pybamm.Experiment([cycle_steps(FIRST_LIFE)] * (FIRST_LIFE["cycles"] + 1),
                                  termination="1% capacity")
    res = model.cycle_adaptive_simulation_V2(
        model.pybamm.lithium_ion.SPM(dict(model.SPM_MODEL_OPTIONS)),
        model.BASE_PARAMETER_VALUES.copy(), exp, model.INITIAL_SOC, save_at_cycles=1)
    t = trajectory(res)
    if not np.isclose(t["cycle"][-1], FIRST_LIFE["cycles"], atol=1e-8):
        raise RuntimeError(f"first life ended at cycle {t['cycle'][-1]:g}")
    eofu = np.asarray(model.extract_deepsoh_state(res, -1), dtype=float)
    return t, eofu


def run_second_life(state, state_ref, solver="rk23"):
    """Second use from a deepSOH state [nLi, Cp, Cn, delta_SEI, delta_pl]; state_ref is the
    end-of-first-use state the restart is built around."""
    use_solver(solver)
    model.scipy_interpolate.interp2d = model.scipy_114_compatible_interp2d
    exp = model.pybamm.Experiment([cycle_steps(SECOND_LIFE)] * (SECOND_LIFE["max_cycles"] + 1),
                                  termination=SECOND_LIFE["termination"])
    params = model.parameter_values_for_state(np.asarray(state, dtype=float),
                                              np.asarray(state_ref, dtype=float))
    res = model.cycle_adaptive_simulation_V2(
        model.pybamm.lithium_ion.SPM(dict(model.SPM_MODEL_OPTIONS)),
        params.copy(), exp, SOC_0=1, save_at_cycles=1)
    t = trajectory(res)
    err = np.max(np.abs(initial_state(t) - state) / np.abs(state_ref))
    if err > 2e-6:
        raise AssertionError(f"initial state reproduced only to {err:.1e}")
    return t


def run_c20_test(state, state_ref):
    """C/20 charge, CV hold, C/20 discharge from 0% SOC, at a deepSOH state."""
    c = C20_TEST
    model.scipy_interpolate.interp2d = model.scipy_114_compatible_interp2d
    params = model.parameter_values_for_state(np.asarray(state, dtype=float),
                                              np.asarray(state_ref, dtype=float))
    exp = model.pybamm.Experiment([(f"Charge at {c['rate']} until {c['upper_V']}V",
                                    f"Hold at {c['upper_V']}V until {c['cv_cutoff']}",
                                    f"Discharge at {c['rate']} until {c['lower_V']}V")],
                                  termination="50% capacity")
    sim = model.pybamm.Simulation(
        model.pybamm.lithium_ion.SPM(dict(model.SPM_MODEL_OPTIONS)), experiment=exp,
        parameter_values=params,
        solver=model.pybamm.CasadiSolver(mode=c["solver_mode"], rtol=c["rtol"],
                                         atol=c["atol"], dt_max=c["dt_max"]))
    sol = sim.solve(initial_soc=c["initial_soc"])
    get = lambda key: np.asarray(sol[key].entries, dtype=float)
    return {"time_h": get("Time [s]") / 3600, "voltage_V": get("Terminal voltage [V]"),
            "current_A": get("Current [A]")}


def end_of_life_index(capacity, cut=3.0):
    """Last sample before the capacity first drops below cut (same rule as the MATLAB).
    Raises if the run starts below the cut or never drops below it."""
    below = np.flatnonzero(np.asarray(capacity) < cut)
    if below.size == 0:
        raise RuntimeError(f"the run never drops below {cut} Ah; raise SECOND_LIFE['max_cycles']")
    if below[0] == 0:
        raise RuntimeError(f"the run starts below {cut} Ah")
    return int(below[0]) - 1


# ---------------------------------------------------------------- parallel second lives
def run_second_lives(jobs, workers, work_dir):
    """jobs: list of dicts {label, state (5 floats), state_ref (5 floats), solver}.
    Each job runs in its own Python process; returns the trajectories in job order."""
    work_dir = Path(work_dir)
    if work_dir.exists():
        shutil.rmtree(work_dir)
    work_dir.mkdir(parents=True)
    spec = work_dir / "jobs.json"
    spec.write_text(json.dumps(jobs), encoding="utf-8")
    pending, running, t0 = list(range(len(jobs))), {}, time.perf_counter()
    while pending or running:
        while pending and len(running) < workers:
            i = pending.pop(0)
            log = open(work_dir / f"job_{i}.log", "w", encoding="utf-8")
            running[i] = (subprocess.Popen([sys.executable, str(Path(__file__).resolve()),
                                            str(spec), str(i)],
                                           stdout=log, stderr=subprocess.STDOUT), log)
        for i in [i for i, (p, _) in running.items() if p.poll() is not None]:
            p, log = running.pop(i)
            log.close()
            if p.returncode != 0:
                for q, qlog in running.values():
                    q.terminate()
                    q.wait()
                    qlog.close()
                raise RuntimeError(f"job {jobs[i]['label']} failed; see {work_dir}/job_{i}.log")
            print(f"  {jobs[i]['label']:<22} done ({time.perf_counter() - t0:.0f} s)", flush=True)
        time.sleep(2)
    out = []
    for i in range(len(jobs)):
        with np.load(work_dir / f"job_{i}.npz") as z:
            out.append({k: z[k] for k in z.files})
        end_of_life_index(out[-1]["capacity_Ah"])     # every run must pass below 3.0 Ah
    shutil.rmtree(work_dir)
    return out


def _worker(spec, index):
    job = json.loads(Path(spec).read_text(encoding="utf-8"))[index]
    t = run_second_life(job["state"], job["state_ref"], job["solver"])
    np.savez(Path(spec).parent / f"job_{index}.npz", **t)


def run_info(solver):
    """Settings saved with every data file."""
    return {"solver": dict(SOLVERS[solver], name=solver), "first_life_protocol": FIRST_LIFE,
            "second_life_protocol": SECOND_LIFE, "expansion_model": EXPANSION,
            "state_names": p4_io.cellstr(p4_io.STATE_NAMES),
            "state_units": p4_io.cellstr(p4_io.STATE_UNITS), "units": p4_io.field_units()}


if __name__ == "__main__":
    _worker(sys.argv[1], int(sys.argv[2]))
