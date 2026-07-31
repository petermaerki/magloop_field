import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import os

# Parameter
D_m = 1.0
R_m = D_m / 2
I_A = 10.5
f_Hz = 14.1e6

lim_x_m = 4
lim_y_m = 3


def h_field_retarded(rho, z_dist, R, I, f_Hz):
    """
    Retarded H-field magnitude of an oscillating magnetic dipole (small circular loop).
    Includes near-field (1/r³), intermediate (1/r²), and far-field (1/r) terms.
    Valid when R << lambda (magnetic dipole approximation).

    rho    : radial distance in loop plane [m]
    z_dist : axial distance along loop axis [m]
    R      : loop radius [m]
    I      : loop current peak amplitude [A]
    f_Hz   : frequency [Hz]

    |H_r|²  = (m/4π)² · 4cos²θ · (1/r⁶ + k²/r⁴)
    |H_θ|²  = (m/4π)² · sin²θ  · (1/r⁶ − k²/r⁴ + k⁴/r²)
    Note: (1 − u + u²) > 0 for all u=(kr)², so H_theta_sq is always non-negative.
    """
    c = 299792458.0
    k = 2.0 * np.pi * f_Hz / c
    m = I * np.pi * R**2  # magnetic dipole moment [A·m²]
    fac = m / (4.0 * np.pi)

    rho = np.asarray(rho, dtype=float)
    z_dist = np.asarray(z_dist, dtype=float)
    r = np.sqrt(rho**2 + z_dist**2)
    r = np.maximum(r, 1e-9)  # avoid singularity at origin
    cos_theta = z_dist / r
    sin_theta = rho / r

    H_r_sq = fac**2 * 4 * cos_theta**2 * (1.0 / r**6 + k**2 / r**4)
    H_theta_sq = fac**2 * sin_theta**2 * (1.0 / r**6 - k**2 / r**4 + k**4 / r**2)

    return np.sqrt(H_r_sq + H_theta_sq)


script_dir = os.path.dirname(os.path.abspath(__file__))
output_dir = os.path.abspath(os.path.join(script_dir, "..", "images"))
os.makedirs(output_dir, exist_ok=True)


def save_h_field_plot(lim_x_m, lim_y_m, output_name, x_step, y_step, levels=None):
    x = np.linspace(-lim_x_m, lim_x_m, 1000)
    y = np.linspace(-lim_y_m, lim_y_m, 1000)
    X, Y = np.meshgrid(x, y)
    H_total = h_field_retarded(Y, X, R_m, I_A, f_Hz)

    plt.figure(figsize=(10, 10))

    # Isolinien < 1 A/m
    if levels is None:
        levels = [0.05, 0.1, 0.2]
    cp = plt.contour(X, Y, H_total, levels=levels, colors="black", linewidths=1.0)
    clabels = plt.clabel(cp, inline=True, fmt=lambda v: f"{v:g} A/m", fontsize=10, rightside_up=True)
    for label in clabels:
        label.set_bbox(dict(facecolor="white", edgecolor="none", pad=3))

    antennenfarbe = "red"
    # Leiterquerschnitt als gefüllte Form
    d_leiter_m = 0.1
    r_leiter_m = d_leiter_m / 2

    # Gefülltes Rechteck
    rectangle = plt.Rectangle(
        (-r_leiter_m, -R_m), d_leiter_m, 2 * R_m, color=antennenfarbe, fill=True
    )
    plt.gca().add_artist(rectangle)

    # Gefüllte Kreise an den Enden
    circle1 = plt.Circle((0, R_m), r_leiter_m, color=antennenfarbe, fill=True)
    circle2 = plt.Circle((0, -R_m), r_leiter_m, color=antennenfarbe, fill=True)
    plt.gca().add_artist(circle1)
    plt.gca().add_artist(circle2)

    # Raster & Achsen
    plt.xticks(np.arange(-lim_x_m, lim_x_m + 1, x_step))
    plt.yticks(np.arange(-lim_y_m, lim_y_m + 1, y_step))
    plt.grid(True, which="major", linestyle="-", color="gray", alpha=0.3)
    plt.axhline(0, color="black", lw=1.2)
    plt.axvline(0, color="black", lw=1.2)

    plt.title("Magnetic Field Strength ($H$)", fontsize=12)
    plt.xlabel("x [m]")
    plt.ylabel("y [m]")
    plt.gca().set_aspect("equal")
    plt.xlim(-lim_x_m, lim_x_m)
    plt.ylim(-lim_y_m, lim_y_m)

    # Legende
    legend_elements = [
        Line2D([0], [0], color=antennenfarbe, lw=4, label="Antenna"),
        Line2D([0], [0], marker="None", color="None", label=f"D = {D_m:.0f} m"),
        Line2D([0], [0], marker="None", color="None", label=f"I = {I_A:.1f} A"),
        Line2D([0], [0], marker="None", color="None", label=f"f = {f_Hz/1e6:.1f} MHz"),
    ]
    plt.legend(handles=legend_elements, loc="upper right", frameon=True)

    output_path = os.path.join(output_dir, output_name)
    plt.tight_layout(pad=0.2)
    plt.savefig(output_path, bbox_inches="tight", pad_inches=0.02)
    plt.close()


save_h_field_plot(lim_x_m=4, lim_y_m=3, output_name="magnetic_field_strength.svg", x_step=1.0, y_step=1.0)
save_h_field_plot(
    lim_x_m=30,
    lim_y_m=60,
    output_name="magnetic_field_strenght_big.svg",
    x_step=10.0,
    y_step=10.0,
    levels=[0.001, 0.002, 0.005, 0.05],
)


# Berechne die Feldstärke für einzelne Punkte bei I_A = 10.5A
I_calc_A = 10.5
points = {
    # X, Y, Z
    "A": (2, 0, 0),
    "B": (3, 1, 0),
    "C": (3, 0, 0),
    "D": (3, -1, 0),
    "E": (3, -2, 0),
    "F": (3, -3, 0),
    "G": (5, 1, 0),
    "H": (6, 1, 0),
    "I": (7, 1, 0),
    "K": (-11, 0, 0),
    "L": (-3, -38, 0),
    "M": (0, 0, 3),
    "N": (0, 0, -5.7),
    "O": (5.5, 0, -5.7),
}

# Nahfeldsonde Parameter
sonde_D_m = 0.104
sonde_r_m = sonde_D_m / 2.0
sonde_A = np.pi * sonde_r_m**2
sonde_leiter_r_m = 5e-4
u0 = 4 * np.pi * 1e-7
sonde_L = u0 * sonde_r_m * (np.log(8 * sonde_r_m / sonde_leiter_r_m) - 2)

omega = 2 * np.pi * f_Hz
# Korrektur Eingangsimpedanz Power Meter
sonde_XL = omega * sonde_L
power_meter_Ri_Ohm = 50.0
gain_wegen_XL = power_meter_Ri_Ohm / np.sqrt(power_meter_Ri_Ohm**2 + sonde_XL**2)


def dBm_to_H(dBm):
    P_W = 10 ** (dBm / 10) * 0.001
    V_load = np.sqrt(P_W * power_meter_Ri_Ohm)
    V_oc = V_load / gain_wegen_XL
    H = V_oc / (omega * u0 * sonde_A)
    return H


# Gemessene Werte in dBm
messwerte_dBm = {
    "A": -1.9,
    "B": -14.9,
    "C": -11.6,
    "D": -12.7,
    "E": -15.8,
    "F": -15.9,
    "G": -26.0,
    "H": -29.0,
    "I": -30.0,
    "K": -33.4,  # Bei Zaun
    "L": -41.3,  # Huegel spielpi
    "M": -23.5,  # Auf Dach
    "N": -32.6,  # Waschkueche
    "O": -35.4,  # Tuere bei Werkstatt
}

print(f"Feldstärke H bei I = {I_calc_A} A, D = {D_m} m:")
print(
    f"{'Punkt':<6} {'X [m]':>6} {'Y [m]':>6} {'Z [m]':>6} {'H_calc [A/m]':>13} {'dBm_mess':>9} {'H_mess [A/m]':>13} {'Faktor':>7}"
)
print("-" * 72)
csv_path = os.path.join(script_dir, "magnetic_field_strength.csv")
with open(csv_path, "w") as f:
    f.write("Punkt\tX [m]\tY [m]\tZ [m]\tH_calc [A/m]\tdBm_mess\tH_mess [A/m]\tFaktor\n")
    for name, (px, py, pz) in points.items():
        rho = np.sqrt(py**2 + pz**2)
        H_val = h_field_retarded(np.array([rho]), np.array([px]), R_m, I_calc_A, f_Hz)
        dBm = messwerte_dBm[name]
        H_mess = dBm_to_H(dBm)
        faktor = H_mess / H_val[0]
        print(
            f"{name:<6} {px:>6.1f} {py:>6.1f} {pz:>6.1f} {H_val[0]:>13.4f} {dBm:>8.1f} {H_mess:>13.4f} {faktor:>7.2f}"
        )
        f.write(
            f"{name}\t{px:.1f}\t{py:.1f}\t{pz:.1f}\t{H_val[0]:.4f}\t{dBm:.1f}\t{H_mess:.4f}\t{faktor:.2f}\n"
        )
