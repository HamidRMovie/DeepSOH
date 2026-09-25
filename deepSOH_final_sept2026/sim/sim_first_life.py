"""First life of the P4 cell, up to the end of first use (EOFU).

Writes data/P4_first_life.mat:
  first_life   trajectory struct (cycle, capacity_Ah, resistance_Ohm, ..., one column)
  eofu_state   5 x 1 deepSOH state at EOFU [nLi; Cp; Cn; delta_SEI; delta_pl]; every
               second life in the other files starts from it or from a change of it
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import p4_io, p4_sim  # noqa: E402


def main():
    t, eofu = p4_sim.run_first_life("rk23")
    path = p4_io.save_mat(p4_sim.DATA_DIR / "P4_first_life.mat", {
        "first_life": p4_io.stack_runs([t]),
        "eofu_state": eofu.reshape(5, 1),
        **p4_sim.run_info("rk23")})
    print("EOFU state [nLi, Cp, Cn, delta_SEI, delta_pl]:", eofu.tolist())
    print("saved", path)


if __name__ == "__main__":
    main()
