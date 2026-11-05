# Models behind "Lithographic Microrobot Swarms"

First-principles models used in the report. Python 3 + numpy.

| File | What it computes | Run |
| --- | --- | --- |
| `physics.py` | Reynolds number, Brownian heading loss, power available per robot size by source, battery life, optical link budget (bit/s vs distance), chemical signalling times, SRAM area | `python3 physics.py` |
| `cost.py` | Robots per 300 mm wafer and cost per working robot (low/base/high), 1M-robot swarm cost, shuttle prototype counts | `python3 cost.py` |
| `swarm_sim.py` | 400-robot heat-source search: solo run-and-tumble vs. swarm sharing 8-bit readings with neighbours (range, message-loss sweeps; 5 seeds each). Writes `swarm_results.json` | `python3 swarm_sim.py` (about 3.5 min) |

All inputs are stated assumptions in the code comments; the cost model's base case reproduces the published ~$0.01 per robot at the Penn/Michigan robot size (210 x 340 um).
