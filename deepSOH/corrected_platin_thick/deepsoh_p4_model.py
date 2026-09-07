"""deepSOH P4 model setup.

Everything the regeneration scripts in ``sim/`` need to build the P4 model and
restart it from a prescribed deepSOH state. This is the model-definition part
of the study only. The duty-cycle search that produced the published protocol
is not included, and neither is the experimental cell data it was fitted to.

The base parameter set is the Mohtat parameter set with the P4 modifications
listed below. Four quantities were originally derived from the cell-07 eSOH and
OCV measurements and are frozen here as constants so that the model can be
built without redistributing that experimental data:

    EPS_N_FRESH, EPS_P_FRESH   fresh active-material volume fractions
    INITIAL_SOC                initial state of charge
    CELL_TEMPERATURE_C         cell temperature, 25 C

The modified PyBaMM in this repository supplies the SEI, plating and kinetics
physics. Stock PyBaMM will not reproduce the published results.
"""
from __future__ import annotations

import numpy as np
import scipy.interpolate as scipy_interpolate
import pybamm

import batfuns_original_Corrected_Cp as batfuns_corrected
from batfuns_original_Corrected_Cp import (
    cycle_adaptive_simulation_V2,
    get_parameter_values,
    graphite_volume_change_mohtat,
)

MODEL_VARIANT = "P4"
STATE_NAMES = ("nLi", "Cp", "Cn", "delta_SEI", "delta_pl")
OUTPUT_NAMES = ("Capacity", "Resistance")

SPM_MODEL_OPTIONS = {
    "SEI": "ec reaction limited",
    "loss of active material": "stress-driven",
    "lithium plating": "irreversible",
    "stress-induced diffusion": "false",
}

UPPER_VOLTAGE = 4.2
CV_CUTOFF_DENOMINATOR = 50
POST_DISCHARGE_REST_SECONDS = 10
DELTA_PL_PER_C_PLATED_REFERENCE = 7.659750616465e-11

# Frozen values from the cell-07 eSOH and OCV fit, see the module docstring.
EPS_N_FRESH = 0.5657277306154936
EPS_P_FRESH = 0.43496330660436655
INITIAL_SOC = 1.0
CELL_TEMPERATURE_C = 25.0

class CandidateInfeasibleError(RuntimeError):
    """Expected protocol-specific infeasibility, not a programming failure."""


def scalar(value):
    return float(np.asarray(value).squeeze())


def scipy_114_compatible_interp2d(x, y, z, kind="linear", **kwargs):
    """Reproduce the small interp2d subset used by this legacy PyBaMM copy."""
    if kind != "linear":
        raise NotImplementedError("Only linear interp2d compatibility is supported")
    interpolator = scipy_interpolate.RegularGridInterpolator(
        (np.asarray(y, dtype=float), np.asarray(x, dtype=float)),
        np.asarray(z, dtype=float),
        method="linear",
        bounds_error=bool(kwargs.get("bounds_error", False)),
        fill_value=kwargs.get("fill_value", np.nan),
    )

    def evaluate(x_new, y_new):
        x_values = np.atleast_1d(np.asarray(x_new, dtype=float))
        y_values = np.atleast_1d(np.asarray(y_new, dtype=float))
        x_mesh, y_mesh = np.meshgrid(x_values, y_values)
        points = np.column_stack((y_mesh.ravel(), x_mesh.ravel()))
        return interpolator(points).reshape(len(y_values), len(x_values))

    return evaluate


def extract_deepsoh_state(summary, index):
    c_plated = scalar(
        summary["X-averaged lithium plating concentration [mol.m-3]"][index]
    )
    if MODEL_VARIANT == "P4":
        delta_pl = scalar(
            summary["X-averaged effective lithium plating thickness [m]"][index]
        )
    else:
        delta_pl = DELTA_PL_PER_C_PLATED_REFERENCE * c_plated
    return np.asarray(
        [
            summary["Total lithium in particles [mol]"][index],
            summary["C_p"][index],
            summary["C_n"][index],
            summary["X-averaged SEI thickness [m]"][index],
            delta_pl,
        ],
        dtype=float,
    )


def parameter_values_for_state(target_state, state_ref):
    target_state = np.asarray(target_state, dtype=float)
    state_ref = np.asarray(state_ref, dtype=float)
    nli_target, cp_target, cn_target, delta_sei_target, delta_pl_target = target_state
    values = BASE_PARAMETER_VALUES.copy()

    eps_n_target = scalar(
        values.evaluate(
            cn_target * 3600
            / (PARAM.n.L * PARAM.n.prim.c_max * PARAM.F * PARAM.A_cc)
        )
    )
    eps_p_target = scalar(
        values.evaluate(
            cp_target * 3600
            / (PARAM.p.L * PARAM.p.prim.c_max * PARAM.F * PARAM.A_cc)
        )
    )
    if not (0 < eps_n_target < 1 and 0 < eps_p_target < 1):
        raise CandidateInfeasibleError(
            f"Invalid active-material fractions: {eps_n_target}, {eps_p_target}"
        )

    if MODEL_VARIANT == "P4":
        particle_radius = scalar(values.evaluate(PARAM.n.prim.R_typ))
        current_area = 3.0 * eps_n_target / particle_radius
        c_plated_target = (
            delta_pl_target
            / DELTA_PL_PER_C_PLATED_REFERENCE
            * current_area
            / FIXED_A_TYP_PLATING_REF
        )
    else:
        current_area = None
        c_plated_target = delta_pl_target / DELTA_PL_PER_C_PLATED_REFERENCE

    values.update(
        {
            "Negative electrode active material volume fraction": eps_n_target,
            "Positive electrode active material volume fraction": eps_p_target,
            "Initial inner SEI thickness [m]": 0.0,
            "Initial outer SEI thickness [m]": delta_sei_target,
            "Initial plated lithium concentration [mol.m-3]": c_plated_target,
            "Use current-area plating thickness": 1.0 if MODEL_VARIANT == "P4" else 0.0,
            "Initial temperature [K]": 273.15 + 25,
            "Ambient temperature [K]": 273.15 + 25,
        },
        check_already_exists=False,
    )

    esoh_solution = pybamm.Simulation(
        pybamm.lithium_ion.ElectrodeSOH(), parameter_values=values
    ).solve(
        [0],
        inputs={
            "V_min": 3.0,
            "V_max": UPPER_VOLTAGE,
            "C_n": cn_target,
            "C_p": cp_target,
            "n_Li": nli_target,
        },
        solver=pybamm.AlgebraicSolver(),
    )
    c_n_max = scalar(values.evaluate(PARAM.n.prim.c_max))
    c_p_max = scalar(values.evaluate(PARAM.p.prim.c_max))
    x_100 = scalar(esoh_solution["x_100"].data[0])
    y_100 = scalar(esoh_solution["y_100"].data[0])
    values.update(
        {
            "Initial concentration in negative electrode [mol.m-3]": x_100 * c_n_max,
            "Initial concentration in positive electrode [mol.m-3]": y_100 * c_p_max,
        }
    )

    if MODEL_VARIANT == "P4":
        achieved_delta_pl = (
            DELTA_PL_PER_C_PLATED_REFERENCE
            * scalar(values["Initial plated lithium concentration [mol.m-3]"])
            * FIXED_A_TYP_PLATING_REF
            / current_area
        )
    else:
        achieved_delta_pl = (
            DELTA_PL_PER_C_PLATED_REFERENCE
            * scalar(values["Initial plated lithium concentration [mol.m-3]"])
        )
    achieved = np.asarray(
        [
            scalar(values.evaluate(PARAM.n_Li_particles_init)),
            scalar(values.evaluate(PARAM.p.cap_init)),
            scalar(values.evaluate(PARAM.n.cap_init)),
            scalar(values["Initial outer SEI thickness [m]"]),
            achieved_delta_pl,
        ]
    )
    scaled_error = np.abs(achieved - target_state) / state_ref
    if np.max(scaled_error) > 1e-8:
        raise AssertionError(
            f"Restart target mismatch: target={target_state}, achieved={achieved}, "
            f"scaled_error={scaled_error}"
        )
    return values

def make_base_model_and_parameters():
    """Build the P4 model and its base parameter set from frozen constants."""
    model = pybamm.lithium_ion.SPM(dict(SPM_MODEL_OPTIONS))
    values = get_parameter_values()
    values.update(
        {
            "Negative electrode active material volume fraction": EPS_N_FRESH,
            "Positive electrode active material volume fraction": EPS_P_FRESH,
            "Initial temperature [K]": 273.15 + CELL_TEMPERATURE_C,
            "Ambient temperature [K]": 273.15 + CELL_TEMPERATURE_C,
            "Positive electrode LAM constant proportional term [s-1]": 4.0312e-08,
            "Negative electrode LAM constant proportional term [s-1]": 7.8e-8,
            "Positive electrode LAM constant proportional term 2 [s-1]": -1.4406e-09,
            "Negative electrode LAM constant proportional term 2 [s-1]": -4.9170e-09,
            "Positive electrode LAM constant exponential term": 1.0776,
            "Negative electrode LAM constant exponential term": 1.0776,
            "Negative electrode volume change": graphite_volume_change_mohtat,
            "SEI kinetic rate constant [m.s-1]": 4.608e-16,
            "EC diffusivity [m2.s-1]": 4.56607447e-19,
            "SEI growth activation energy [J.mol-1]": 1.874e4,
            "Lithium plating kinetic rate constant [m.s-1]": 2.3586e-09,
            "Initial inner SEI thickness [m]": 0.0,
            "Initial outer SEI thickness [m]": 5e-9,
            "SEI resistivity [Ohm.m]": 90000.0,
            "Li plating resistivity [Ohm.m]": 90000.0,
            "Negative electrode partial molar volume [m3.mol-1]": 7e-6,
            "Negative electrode LAM min stress [Pa]": 0,
            "Negative electrode LAM max stress [Pa]": 0,
            "Positive electrode LAM min stress [Pa]": 0,
            "Positive electrode LAM max stress [Pa]": 0,
            "Initial plated lithium concentration [mol.m-3]": 0.0,
            "Use current-area plating thickness": 1.0,
        },
        check_already_exists=False,
    )
    return model, values


SPM, BASE_PARAMETER_VALUES = make_base_model_and_parameters()
PARAM = SPM.param
FIXED_A_TYP_PLATING_REF = scalar(
    BASE_PARAMETER_VALUES.evaluate(PARAM.a_typ_plating_ref)
)
V_BAR_PLATED_LI = scalar(BASE_PARAMETER_VALUES.evaluate(PARAM.V_bar_plated_Li))
np.testing.assert_allclose(
    V_BAR_PLATED_LI / FIXED_A_TYP_PLATING_REF,
    DELTA_PL_PER_C_PLATED_REFERENCE,
    rtol=1e-10,
)
