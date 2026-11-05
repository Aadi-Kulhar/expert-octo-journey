"""Per-robot cost model for wafer-printed microrobots (300 mm, 55 nm-class CMOS + post-CMOS MEMS).

Every input is an assumption stated in the report. Low / base / high scenarios bracket uncertainty.
Calibration check: base case at the Penn/Michigan robot size (210 x 340 um) should land near the
published ~$0.01 per robot.
"""
import math, json

wafer_d_mm, edge_excl_mm = 300, 3
usable_mm2 = math.pi * (wafer_d_mm / 2 - edge_excl_mm) ** 2

scen = {
    #            CMOS wafer $, post-CMOS layers, $/layer, release+test $/wafer, street overhead, yield
    "low":  dict(cmos=2000, layers=8,  per_layer=100, backend=300,  overhead=0.20, yld=0.85),
    "base": dict(cmos=2500, layers=12, per_layer=150, backend=600,  overhead=0.25, yld=0.70),
    "high": dict(cmos=3500, layers=16, per_layer=250, backend=1500, overhead=0.35, yld=0.45),
}

def wafer_cost(s):
    return s["cmos"] + s["layers"] * s["per_layer"] + s["backend"]

def robots_per_wafer(w_um, h_um, s):
    area_mm2 = (w_um * 1e-3) * (h_um * 1e-3) * (1 + s["overhead"])
    return usable_mm2 / area_mm2 * s["yld"]

print(f"Usable wafer area: {usable_mm2:,.0f} mm2")
for k, s in scen.items():
    print(f"{k}: total processed wafer cost ${wafer_cost(s):,.0f}")

sizes = [(50, 50), (100, 100), (210, 340), (300, 300), (500, 500), (1000, 1000)]
rows = []
for w, h in sizes:
    r = {"size": f"{w}x{h}"}
    for k, s in scen.items():
        n = robots_per_wafer(w, h, s)
        r[f"n_{k}"] = n
        r[f"cost_{k}"] = wafer_cost(s) / n
    rows.append(r)
    print(f"{w:>5}x{h:<5} good robots/wafer base {r['n_base']:>12,.0f}   cost/robot low ${r['cost_low']:.5f}"
          f"  base ${r['cost_base']:.5f}  high ${r['cost_high']:.5f}")

# Swarm cost at base for a 1 M robot swarm at each size
print()
for r in rows:
    print(f"{r['size']}: 1M-robot swarm silicon cost base ${r['cost_base']*1e6:,.0f}; "
          f"wafers needed {1e6/r['n_base']:.2f}")

# Prototype path: one MPW die (assume 10 mm2 usable at 130 nm shuttle, $15k for 100 dies per
# ChipFoundry pricing reported by eeNews Europe), die-level post-processing in a university cleanroom.
die_mm2 = 10
for w, h in [(100, 100), (210, 340)]:
    per_die = die_mm2 / ((w*1e-3)*(h*1e-3)*1.4)   # extra 40 % overhead for die-level processing
    print(f"MPW prototype {w}x{h}: ~{per_die:,.0f} robots per die, ~{per_die*100:,.0f} robots per 100-die run")

# NRE / program cost (estimates)
nre = {
    "55nm full mask set": (400e3, 1.0e6),
    "180nm full mask set": (60e3, 150e3),
    "post-CMOS MEMS masks (12-16 layers)": (40e3, 120e3),
    "MPW prototype run (130nm, 100 dies)": (15e3, 15e3),
}
for k, (lo, hi) in nre.items():
    print(f"{k}: ${lo:,.0f} - ${hi:,.0f}")

json.dump(rows, open("cost_rows.json", "w"), indent=1)
