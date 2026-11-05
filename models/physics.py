"""First-principles scaling model for wafer-printed microrobots.

All inputs are textbook constants or stated engineering assumptions (labelled).
Outputs feed the 'Physics and requirements' section of the report.
"""
import math

kB, T = 1.380649e-23, 310.0          # J/K, body temperature (K)
mu, rho = 1.0e-3, 1000.0             # water viscosity (Pa s), density (kg/m3)
nu = mu / rho

sizes_um = [10, 30, 100, 300, 1000]  # robot edge length (characteristic size)

print("=== Fluid / Brownian scaling (v = 1 body length per second) ===")
print(f"{'L um':>6} {'Re':>9} {'Stokes F (N)':>13} {'P_mech (W)':>11} "
      f"{'D_trans um2/s':>13} {'heading lost (s)':>16} {'drift vs diffusion over 1 s':>27}")
for L in sizes_um:
    Lm = L * 1e-6
    R = Lm / 2
    v = Lm                          # one body length per second
    Re = v * Lm / nu
    F = 6 * math.pi * mu * R * v
    P = F * v
    Dt = kB * T / (6 * math.pi * mu * R)
    Dr = kB * T / (8 * math.pi * mu * R ** 3)
    t_heading = 1 / (2 * Dr)        # time for ~1 rad^2 heading variance (2D)
    peclet = v * 1.0 / math.sqrt(2 * Dt * 1.0)
    print(f"{L:>6} {Re:>9.2e} {F:>13.2e} {P:>11.2e} {Dt*1e12:>13.3e} {t_heading:>16.2e} {peclet:>27.1f}")

print()
print("=== Power available to a square robot of edge L (W) ===")
# Assumptions (labelled in the report):
#  PV efficiency 15 % for small Si cells under monochromatic light (conservative).
#  Sun 1000 W/m2; bright lab LED/laser field 10 kW/m2 (1 W/cm2); indoor 5 W/m2.
#  Near-IR through 1 cm tissue: skin MPE ~3 kW/m2 at 800 nm, attenuation ~e^-2 to e^-4 per cm
#  Ultrasound: FDA diagnostic limit I_spta 720 mW/cm2 = 7.2 kW/m2, assume 1 % capture
#   efficiency for a sub-wavelength receiver (literature reports far lower for links).
#  Glucose/enzymatic biofuel cell: 10 uW/cm2.  Thin-film Li battery: 0.5 Wh/cm3 at 5 um.
eta_pv = 0.15
for L in sizes_um:
    A = (L * 1e-6) ** 2
    sun = 1000 * A * eta_pv
    lab = 1e4 * A * eta_pv
    indoor = 5 * A * eta_pv
    tissue = 3000 * math.exp(-3) * A * eta_pv
    us = 7200 * A * 0.01
    bio = 10e-6 / 1e-4 * A
    batt_J = 0.5 * 3600 / 1e-6 * (A * 5e-6)   # Wh/cm3 -> J/m3 ; volume
    print(f"L={L:>5} um: lab light {lab:.1e}  sun {sun:.1e}  indoor {indoor:.1e}  "
          f"NIR@1cm tissue {tissue:.1e}  ultrasound {us:.1e}  biofuel {bio:.1e}  "
          f"battery {batt_J:.1e} J -> {batt_J/100e-9/60:.1f} min at 100 nW")

print()
print("=== Optical robot-to-robot link budget ===")
# Emitter: isotropic micro-LED, wall-plug efficiency eta_led.
# Receiver: photodiode area A_rx, needs N_ph photons per bit (OOK, shot-noise limited + margin).
h, c = 6.626e-34, 3e8
lam = 520e-9
E_ph = h * c / lam
A_rx = (20e-6) ** 2          # 20 x 20 um photodiode
N_ph = 2000                   # photons per bit at receiver (incl. ambient-light margin)
for eta_led in (0.01, 0.05):
    for P_tx in (25e-9, 100e-9):   # electrical power spent on transmit
        row = []
        for d_um in (50, 100, 200, 300, 500, 1000, 2000):
            d = d_um * 1e-6
            frac = A_rx / (4 * math.pi * d ** 2)
            frac = min(frac, 0.5)
            E_bit_elec = N_ph * E_ph / frac / eta_led
            bps = P_tx / E_bit_elec
            row.append((d_um, bps))
        print(f"eta_led={eta_led:.2f} P_tx={P_tx*1e9:.0f} nW: " +
              "  ".join(f"{d}um:{b:,.0f}bps" for d, b in row))

print()
print("=== Chemical signalling (diffusion time t = L^2 / 2D, small molecule D = 1e-9 m2/s) ===")
for d_um in (10, 100, 1000):
    print(f"{d_um} um: {((d_um*1e-6)**2/(2*1e-9)):.2f} s")

print()
print("=== Electronics budget (estimates) ===")
# Subthreshold 55 nm logic ~ 1-5 pJ/instruction incl. memory access (assumption)
for e_pj in (1, 5):
    print(f"{e_pj} pJ/instr: 75 nW -> {75e-9/(e_pj*1e-12):,.0f} instructions/s")
# SRAM area: 55 nm 6T cell ~0.5 um2, 22 nm ~0.1 um2, 2x array overhead
for node, cell in (("55nm", 0.5), ("22nm FD-SOI", 0.11)):
    kbytes = 4
    area = kbytes * 8192 * cell * 2
    print(f"{node}: {kbytes} kB SRAM ~ {area:,.0f} um2 = {area/ (210*340) *100:.1f}% of a 210x340 um robot")
