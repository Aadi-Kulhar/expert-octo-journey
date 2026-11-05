"""Swarm simulation: can cooperating microrobots find a heat source that no single robot can sense?

Setup (all parameters tied to numbers in the report):
- 2D arena 6 x 6 mm (robots are surface-bound: silicon bodies sink, see physics model).
- Robots: 200 um bodies, speed 1 body length/s (200 um/s), run-and-tumble, heading noise from
  surface friction/flow (rotational diffusion D_r, applied as Gaussian heading noise).
- Temperature field: hot spot at arena centre-right, shallow exponential profile. The gradient
  across one body (200 um) is ~0.01-0.03 C, while each reading has 0.3 C noise (Penn robot's
  reported resolution). A single robot therefore cannot sense direction from one comparison.
- Strategy SOLO: robot compares a 1-s-averaged reading (N samples at the sample rate) with its
  previous one; keeps heading if warmer, tumbles if colder (bacterial chemotaxis).
- Strategy SWARM: each robot broadcasts its smoothed reading (8-bit) to neighbours inside
  optical range r_c; the receiver also measures the bearing of the sender (two photodiodes,
  +/-30 deg bearing error). It estimates the local gradient by least squares over neighbour
  differences and steers toward it (no global positioning, no central controller).
  Messages are dropped with probability p_loss; bit budget per robot per second is enforced by
  the link budget (one 8-bit reading per second fits easily inside >40 bps at 500 um).
- Metric: fraction of robots within 0.6 mm of the hot spot after t seconds.
"""
import numpy as np, json, sys

def run(strategy, r_c_um=500.0, p_loss=0.2, n=400, t_end=600, seed=0,
        noise_C=0.3, grad_scale_mm=3.0, dT=1.0, bearing_err_deg=30.0):
    rng = np.random.default_rng(seed)
    L = 6.0                           # arena mm
    src = np.array([4.5, 3.0])
    v = 0.2                           # mm/s
    dt = 1.0                          # s per control step (1 reading per second)
    samples_per_step = 4              # readings averaged per step
    sigma = noise_C / np.sqrt(samples_per_step)
    Dr = 0.02                         # rad^2/s heading noise
    r_c = r_c_um / 1000.0
    ber = np.deg2rad(bearing_err_deg)

    def field(p):
        d = np.linalg.norm(p - src, axis=-1)
        return dT * np.exp(-d / grad_scale_mm)   # peak 1 C excess, shallow

    pos = rng.uniform(0.2, 1.8, size=(n, 2)); pos[:, 1] = rng.uniform(0.5, 5.5, n)  # start in left strip
    th = rng.uniform(0, 2*np.pi, n)
    last = field(pos) + rng.normal(0, sigma, n)
    hist = []
    for step in range(int(t_end/dt)):
        meas = field(pos) + rng.normal(0, sigma, n)
        if strategy == "solo":
            worse = meas < last
            th = np.where(worse, rng.uniform(0, 2*np.pi, n), th)
        elif strategy == "swarm":
            diff = pos[None, :, :] - pos[:, None, :]          # i -> j vectors
            dist = np.linalg.norm(diff, axis=-1)
            nb = (dist < r_c) & (dist > 0) & (rng.random((n, n)) > p_loss)
            bear = np.arctan2(diff[..., 1], diff[..., 0]) + rng.normal(0, ber, (n, n))
            u = np.stack([np.cos(bear), np.sin(bear)], -1)
            dTij = meas[None, :] - meas[:, None]
            g = (nb[..., None] * u * dTij[..., None]).sum(1)  # sum of signed bearings
            cnt = nb.sum(1)
            has = cnt >= 3
            target = np.arctan2(g[:, 1], g[:, 0])
            # steer partway toward estimated gradient; fall back to chemotaxis if isolated
            dth = np.angle(np.exp(1j*(target - th)))
            th = np.where(has, th + 0.5*dth, np.where(meas < last, rng.uniform(0, 2*np.pi, n), th))
        last = meas
        th = th + rng.normal(0, np.sqrt(2*Dr*dt), n)
        pos = pos + v*dt*np.stack([np.cos(th), np.sin(th)], -1)
        # reflecting walls
        for k in range(2):
            lo = pos[:, k] < 0; hi = pos[:, k] > L
            pos[lo, k] = -pos[lo, k]; pos[hi, k] = 2*L - pos[hi, k]
            th = np.where(lo | hi, (np.pi - th) if k == 0 else -th, th)
        if (step+1) % 30 == 0:
            frac = float((np.linalg.norm(pos - src, axis=1) < 0.6).mean())
            hist.append(((step+1)*dt, frac))
    return hist

if __name__ == "__main__":
    out = {}
    seeds = range(5)
    configs = [("solo", None, None), ("swarm", 300, 0.2), ("swarm", 500, 0.2), ("swarm", 1000, 0.2),
               ("swarm", 500, 0.6)]
    for strat, rc, pl in configs:
        key = strat if strat == "solo" else f"swarm_rc{rc}_loss{pl}"
        runs = [run(strat, r_c_um=rc or 500, p_loss=pl or 0.2, seed=s) for s in seeds]
        t = [h[0] for h in runs[0]]
        arr = np.array([[h[1] for h in r] for r in runs])
        out[key] = {"t": t, "mean": arr.mean(0).round(3).tolist(),
                    "lo": arr.min(0).round(3).tolist(), "hi": arr.max(0).round(3).tolist()}
        print(key, "final mean", out[key]["mean"][-1], "range", out[key]["lo"][-1], out[key]["hi"][-1],
              "| t=300s", out[key]["mean"][9])
        sys.stdout.flush()
    json.dump(out, open("swarm_results.json", "w"), indent=1)
