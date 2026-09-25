"""Data layout of the .mat files. No PyBaMM here, so this module can be imported anywhere.

Every trajectory field listed in TRAJECTORY_FIELDS is saved as a matrix with one column
per run and one row per cycle, NaN-padded where runs end at different cycles. The cycle
column is shared. MATLAB loads these as fields of a struct named after the phase, e.g.
second_life.capacity_Ah(:, j) is run j.
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
from scipy.io import savemat

STATE_NAMES = ("nLi", "Cp", "Cn", "delta_SEI", "delta_pl")
STATE_UNITS = ("mol", "Ah", "Ah", "m", "m")

# name -> unit; the order is the order written to the .mat
TRAJECTORY_FIELDS = {
    "capacity_Ah": "Ah",
    "resistance_Ohm": "Ohm",
    "expansion_um": "um, irreversible, = SEI + plating + LAM parts below",
    "expansion_SEI_um": "um",
    "expansion_plating_um": "um",
    "expansion_LAM_um": "um",
    "nLi_mol": "mol, cyclable lithium",
    "Cp_Ah": "Ah, positive electrode capacity",
    "Cn_Ah": "Ah, negative electrode capacity",
    "delta_SEI_m": "m, SEI thickness",
    "delta_pl_m": "m, plated lithium thickness",
    "eps_n": "-, negative electrode active material volume fraction",
    "eps_p": "-, positive electrode active material volume fraction",
}


def stack_runs(runs):
    """runs: list of dicts, each with 'cycle' and every TRAJECTORY_FIELDS key (1-D arrays).
    Returns a dict for one .mat struct: cycle (K x 1), each field (K x nRuns) NaN-padded,
    and n_samples (1 x nRuns)."""
    n = [len(r["cycle"]) for r in runs]
    k = max(n)
    longest = runs[int(np.argmax(n))]["cycle"]
    for r in runs:
        c = np.asarray(r["cycle"], dtype=float)
        if not np.allclose(c, np.asarray(longest[:len(c)], dtype=float), rtol=0, atol=1e-9):
            raise ValueError("runs do not share one cycle grid")
    out = {"cycle": np.asarray(longest, dtype=float).reshape(-1, 1)}
    for name in TRAJECTORY_FIELDS:
        m = np.full((k, len(runs)), np.nan)
        for j, r in enumerate(runs):
            m[:len(r[name]), j] = np.asarray(r[name], dtype=float)
        out[name] = m
    out["n_samples"] = np.asarray(n, dtype=float).reshape(1, -1)
    return out


def cellstr(names):
    """A Python list of strings -> a MATLAB cell array of char (1 x n)."""
    a = np.empty((1, len(names)), dtype=object)
    for j, s in enumerate(names):
        a[0, j] = str(s)
    return a


def field_units():
    """Struct of the units of every trajectory field, saved next to the data."""
    return {name: unit for name, unit in TRAJECTORY_FIELDS.items()}


def save_mat(path, variables):
    """Write variables (a dict) to a .mat file readable by MATLAB with load()."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    savemat(str(path), variables, do_compression=True, oned_as="column")
    return path
