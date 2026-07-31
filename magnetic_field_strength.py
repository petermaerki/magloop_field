import dataclasses
import pathlib

import matplotlib
import matplotlib.figure
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D


@dataclasses.dataclass(frozen=True)
class Calculator:
    D_m: float
    R_m: float
    m_Am2: float
    f_Hz: float

    @property
    def h_field(self) -> float:
        return self.m_Am2 * 2

    def h_field_retarded(self, rho, z_dist, m_Am2, f_Hz):
        """
        Retarded H-field magnitude of an oscillating magnetic dipole (small circular loop).
        Includes near-field (1/r³), intermediate (1/r²), and far-field (1/r) terms.
        Valid when R << lambda (magnetic dipole approximation).

        rho    : radial distance in loop plane [m]
        z_dist : axial distance along loop axis [m]
        m_Am2  : magnetic dipole moment [A·m²]
        f_Hz   : frequency [Hz]

        |H_r|²  = (m/4π)² · 4cos²θ · (1/r⁶ + k²/r⁴)
        |H_θ|²  = (m/4π)² · sin²θ  · (1/r⁶ − k²/r⁴ + k⁴/r²)
        Note: (1 − u + u²) > 0 for all u=(kr)², so H_theta_sq is always non-negative.
        """
        c = 299792458.0
        k = 2.0 * np.pi * f_Hz / c
        fac = m_Am2 / (4.0 * np.pi)

        rho = np.asarray(rho, dtype=float)
        z_dist = np.asarray(z_dist, dtype=float)
        r = np.sqrt(rho**2 + z_dist**2)
        r = np.maximum(r, 1e-9)  # avoid singularity at origin
        cos_theta = z_dist / r
        sin_theta = rho / r

        H_r_sq = fac**2 * 4 * cos_theta**2 * (1.0 / r**6 + k**2 / r**4)
        H_theta_sq = fac**2 * sin_theta**2 * (1.0 / r**6 - k**2 / r**4 + k**4 / r**2)

        return np.sqrt(H_r_sq + H_theta_sq)

    def figure_h_field_plot(
        self,
        lim_x_m,
        lim_y_m,
        x_step,
        y_step,
        levels=None,
    ) -> matplotlib.figure.Figure:
        self._save_h_field_plot(
            lim_x_m=lim_x_m,
            lim_y_m=lim_y_m,
            x_step=x_step,
            y_step=y_step,
            levels=levels,
        )
        return plt.gcf()

    def save_h_field_plot(
        self,
        lim_x_m,
        lim_y_m,
        x_step,
        y_step,
        filename: pathlib.Path,
        levels=None,
    ) -> None:
        assert isinstance(filename, pathlib.Path)

        self._save_h_field_plot(
            lim_x_m=lim_x_m,
            lim_y_m=lim_y_m,
            x_step=x_step,
            y_step=y_step,
            levels=levels,
        )
        plt.savefig(filename, bbox_inches="tight", pad_inches=0.02)
        plt.close()

    def _save_h_field_plot(
        self,
        lim_x_m,
        lim_y_m,
        x_step,
        y_step,
        levels,
    ) -> None:
        x = np.linspace(-lim_x_m, lim_x_m, 1000)
        y = np.linspace(-lim_y_m, lim_y_m, 1000)
        X, Y = np.meshgrid(x, y)
        H_total = self.h_field_retarded(Y, X, self.m_Am2, self.f_Hz)

        aspect_ratio = lim_x_m / lim_y_m if lim_y_m else 1.0
        fig_height = 8.0
        fig_width = fig_height * aspect_ratio
        plt.figure(figsize=(fig_width, fig_height))

        # Isolinien < 1 A/m
        if levels is None:
            levels = [0.05, 0.1, 0.2]
        cp = plt.contour(X, Y, H_total, levels=levels, colors="black", linewidths=1.0)
        clabels = plt.clabel(
            cp, inline=True, fmt=lambda v: f"{v:g} A/m", fontsize=10, rightside_up=True
        )
        for label in clabels:
            label.set_bbox(dict(facecolor="white", edgecolor="none", pad=3))

        antennenfarbe = "red"
        # Leiterquerschnitt als gefüllte Form
        d_leiter_m = 0.1
        r_leiter_m = d_leiter_m / 2

        # Gefülltes Rechteck
        rectangle = plt.Rectangle(
            (-r_leiter_m, -self.R_m),
            d_leiter_m,
            2 * self.R_m,
            color=antennenfarbe,
            fill=True,
        )
        plt.gca().add_artist(rectangle)

        # Gefüllte Kreise an den Enden
        circle1 = plt.Circle((0, self.R_m), r_leiter_m, color=antennenfarbe, fill=True)
        circle2 = plt.Circle((0, -self.R_m), r_leiter_m, color=antennenfarbe, fill=True)
        plt.gca().add_artist(circle1)
        plt.gca().add_artist(circle2)

        # Raster & Achsen
        plt.xticks(np.arange(-lim_x_m, lim_x_m + 1, x_step))
        plt.yticks(np.arange(-lim_y_m, lim_y_m + 1, y_step))
        plt.grid(True, which="major", linestyle="-", color="gray", alpha=0.3)
        plt.axhline(0, color="black", lw=1.2)
        plt.axvline(0, color="black", lw=1.2)

        plt.title("Magnetic Field Strength ($H$)", fontsize=12, pad=6, y=1.02)
        plt.xlabel("x [m]")
        plt.ylabel("y [m]")
        plt.gca().set_aspect("equal")
        plt.xlim(-lim_x_m, lim_x_m)
        plt.ylim(-lim_y_m, lim_y_m)

        # Legende
        legend_elements = [
            Line2D([0], [0], color=antennenfarbe, lw=4, label="Antenna"),
            Line2D(
                [0], [0], marker="None", color="None", label=f"m = {self.m_Am2:.2f} A m^2"
            ),
            Line2D(
                [0],
                [0],
                marker="None",
                color="None",
                label=f"f = {self.f_Hz / 1e6:.1f} MHz",
            ),
        ]
        plt.legend(handles=legend_elements, loc="upper right", frameon=True)

        # Keep figure margins minimal and deterministic for web rendering.
        plt.subplots_adjust(left=0.06, right=0.995, bottom=0.06, top=0.96)


def main() -> None:
    D_m = 1.0
    I_A = 10.5
    m_Am2 = I_A * np.pi * (D_m / 2) ** 2
    calculator = Calculator(
        D_m=D_m,
        R_m=D_m / 2,
        m_Am2=m_Am2,
        f_Hz=14.1e6,
    )

    DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent
    output_dir = DIRECTORY_OF_THIS_FILE / "generated_images"
    output_dir.mkdir(exist_ok=True, parents=True)

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

    calculator.save_h_field_plot(
        lim_x_m=4,
        lim_y_m=3,
        filename=output_dir / "magnetic_field_strength.svg",
        x_step=1.0,
        y_step=1.0,
    )
    calculator.save_h_field_plot(
        lim_x_m=30,
        lim_y_m=60,
        filename=output_dir / "magnetic_field_strenght_big.svg",
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

    omega = 2 * np.pi * calculator.f_Hz
    # Korrektur Eingangsimpedanz Power Meter
    sonde_XL = omega * sonde_L
    power_meter_Ri_Ohm = 50.0
    gain_wegen_XL = power_meter_Ri_Ohm / np.sqrt(power_meter_Ri_Ohm**2 + sonde_XL**2)


if __name__ == "__main__":
    main()
