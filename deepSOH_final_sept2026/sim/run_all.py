"""Run every P4 simulation in order and write all .mat files to ../data.

The first life comes first: every other run starts from its end-of-first-use state.
About 1 h 30 min with 11 workers; --skip-dop853 leaves out the solver check (~30 min).

  python sim/run_all.py
  python sim/run_all.py --skip-dop853
"""
import argparse, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import sim_first_life, sim_three_cells, sim_perturbations, sim_observability  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--skip-dop853", action="store_true", help="leave out the DOP853 solver check")
ap.add_argument("--workers", type=int, default=11)
args = ap.parse_args()
if args.workers < 1:
    ap.error("--workers must be at least 1")

t0 = time.perf_counter()
sim_first_life.main()
sim_three_cells.main(args.workers)
sim_perturbations.main(args.workers)
for cell in ("nominal",) + sim_observability.THREE_CELLS:
    sim_observability.main(cell, "rk23", 0.01, args.workers)
if not args.skip_dop853:
    sim_observability.main("high_SEI_low_plating", "dop853", 0.01, args.workers)
print(f"all simulations done in {(time.perf_counter() - t0) / 60:.0f} min")
