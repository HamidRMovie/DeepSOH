# Archived: August 2026 version of the deepSOH study

Replaced in September 2026 by `deepSOH_final_sept2026/` (in the repository root), which
recreates every simulation and figure by itself: Python only simulates and writes `.mat`
files, and MATLAB does all the analysis and draws the figures. Nothing in the new folder uses
this one; it is kept for reference only.

In this version, Jupyter notebooks (`P4_01` to `P4_03`) computed the observability metrics
from CSV data in `data/` and exported `.mat` files for the MATLAB plot scripts in `matlab/`.
The scripts in `sim/` expect to sit directly under the repository root, so they do not run
from this archive location.

The new folder was checked against this one: on the same data its MATLAB analysis matches
the notebooks to within numerical round-off, Figure 3 is pixel-identical, and the regenerated
first-life and three-cell data are bit-identical. Two things changed on purpose. Figures 6
and 7 now start from the same end-of-first-use state as every other figure (this version
used a first life simulated with a looser solver); this moves the values of the combined
measurement sets by about 1% or less, while the single-signal curves, which are the most
sensitive to the solver, move more. And every curve in Figure 5 now ends at its last point
at or above 3.0 Ah, one sample earlier, the end-of-life rule Figure 3 always used.
