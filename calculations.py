import dataclasses
import math
import pathlib

import matplotlib
import matplotlib.figure
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D


_MU0 = 4.0 * math.pi * 1e-7  # H/m
_C_LIGHT = 299792458.0  # m/s


@dataclasses.dataclass(frozen=True)
class AntennaCalculator:
    """Computes antenna parameters from geometry and measurement."""

    D_m: float    # loop diameter [m]
    d_m: float    # conductor diameter [m]
    f_Hz: float   # frequency [Hz]
    bw_Hz: float  # bandwidth B_SWR2.62 [Hz]
    P_W: float    # power into antenna [W]

    @property
    def L_H(self) -> float:
        """Inductance [H]"""
        return _MU0 * (self.D_m / 2) * (math.log(8 * self.D_m / self.d_m) - 2)

    @property
    def C_F(self) -> float:
        """Resonance capacitance [F]"""
        return 1.0 / ((2 * math.pi * self.f_Hz) ** 2 * self.L_H)

    @property
    def Q0(self) -> float:
        """Unloaded quality factor"""
        return self.f_Hz / self.bw_Hz

    @property
    def XL(self) -> float:
        """Inductive reactance [Ohm]"""
        return 2 * math.pi * self.f_Hz * self.L_H

    @property
    def RT_Ohm(self) -> float:
        """Damping resistance [Ohm]"""
        return self.XL / self.Q0

    @property
    def A_m2(self) -> float:
        """Loop area [m²]"""
        return math.pi * (self.D_m / 2) ** 2

    @property
    def RR_Ohm(self) -> float:
        """Radiation resistance [Ohm] — Rayleigh term with King finite-size correction."""
        rayleigh = 31171.0 * ((self.A_m2 * self.f_Hz**2) / _C_LIGHT**2) ** 2
        king_correction = 1.0 + 0.5 * ((math.pi * self.D_m * self.f_Hz) / _C_LIGHT) ** 2
        return rayleigh * king_correction

    @property
    def I_main_loop_A(self) -> float:
        """Loop current [A]"""
        return math.sqrt(self.P_W / self.RT_Ohm)

    @property
    def U_loop_V(self) -> float:
        """Loop voltage [V]"""
        return self.I_main_loop_A * self.XL

    @property
    def m_Am2(self) -> float:
        """Magnetic dipole moment [A m²]"""
        return self.I_main_loop_A * self.A_m2


@dataclasses.dataclass(frozen=True)
class Calculator:
    D_m: float
    R_m: float
    m_Am2: float
    f_Hz: float

    @property
    def h_field(self) -> float:
        return self.m_Am2 * 2

    def h_field_retarded_xyz(self, x_m, y_m, z_m, m_Am2, f_Hz):
        """Retarded dipole |H| at Cartesian point (x, y, z)."""
        c = 299792458.0
        k = 2.0 * np.pi * f_Hz / c
        fac = m_Am2 / (4.0 * np.pi)

        x_m = np.asarray(x_m, dtype=float)
        y_m = np.asarray(y_m, dtype=float)
        z_m = np.asarray(z_m, dtype=float)

        r = np.sqrt(x_m**2 + y_m**2 + z_m**2)
        r = np.maximum(r, 1e-9)
        rho = np.sqrt(y_m**2 + z_m**2)
        phi = np.arctan2(rho, x_m)

        H_r_sq = fac**2 * 4 * np.cos(phi) ** 2 * (1.0 / r**6 + k**2 / r**4)
        H_theta_sq = fac**2 * np.sin(phi) ** 2 * (1.0 / r**6 - k**2 / r**4 + k**4 / r**2)
        return np.sqrt(H_r_sq + H_theta_sq)

    def figure_h_field_plot(
        self,
        lim_x_m,
        lim_y_m,
        x_step,
        y_step,
        levels=None,
        icnirp_limit_a_per_m=None,
        show_icnirp_blue=False,
    ) -> matplotlib.figure.Figure:
        self._save_h_field_plot(
            lim_x_m=lim_x_m,
            lim_y_m=lim_y_m,
            x_step=x_step,
            y_step=y_step,
            levels=levels,
            icnirp_limit_a_per_m=icnirp_limit_a_per_m,
            show_icnirp_blue=show_icnirp_blue,
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
        icnirp_limit_a_per_m=None,
        show_icnirp_blue=False,
    ) -> None:
        assert isinstance(filename, pathlib.Path)

        self._save_h_field_plot(
            lim_x_m=lim_x_m,
            lim_y_m=lim_y_m,
            x_step=x_step,
            y_step=y_step,
            levels=levels,
            icnirp_limit_a_per_m=icnirp_limit_a_per_m,
            show_icnirp_blue=show_icnirp_blue,
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
        icnirp_limit_a_per_m=None,
        show_icnirp_blue=False,
    ) -> None:
        x = np.linspace(-lim_x_m, lim_x_m, 1000)
        y = np.linspace(-lim_y_m, lim_y_m, 1000)
        X, Y = np.meshgrid(x, y)
        H_total = self.h_field_retarded_xyz(X, Y, 0.0, self.m_Am2, self.f_Hz)

        # Do not draw contour lines in the near-field area where the model is unreliable.
        # Use the full 3D radius definition r = sqrt(x^2 + y^2 + z^2) with z=0 in this plot slice.
        z_plane_m = 0.0
        r_3d = np.sqrt(X**2 + Y**2 + z_plane_m**2)
        H_total_masked = np.ma.masked_where(r_3d <= 1.5 * self.D_m, H_total)

        aspect_ratio = lim_x_m / lim_y_m if lim_y_m else 1.0
        fig_height = 8.0
        fig_width = fig_height * aspect_ratio
        plt.figure(figsize=(fig_width, fig_height))

        # Isolinien < 1 A/m
        if levels is None:
            levels = [0.05, 0.1, 0.2]
        else:
            levels = np.unique(np.asarray(levels, dtype=float))
            if levels.size == 0:
                levels = np.array([0.05, 0.1, 0.2], dtype=float)
        cp = plt.contour(
            X,
            Y,
            H_total_masked,
            levels=levels,
            colors="black",
            linewidths=1.0,
            corner_mask=False,
        )
        clabels = plt.clabel(
            cp, inline=True, fmt=lambda v: f"{v:g} A/m", fontsize=10, rightside_up=True
        )
        for label in clabels:
            label.set_bbox({"facecolor": "white", "edgecolor": "none", "pad": 3})

        show_blue_limit_line = False
        if show_icnirp_blue and icnirp_limit_a_per_m is not None and np.isfinite(icnirp_limit_a_per_m):
            h_min = float(np.ma.min(H_total_masked))
            h_max = float(np.ma.max(H_total_masked))
            if h_min <= float(icnirp_limit_a_per_m) <= h_max:
                cp_limit = plt.contour(
                    X,
                    Y,
                    H_total_masked,
                    levels=[float(icnirp_limit_a_per_m)],
                    colors="blue",
                    linewidths=1.6,
                    corner_mask=False,
                )
                limit_labels = plt.clabel(
                    cp_limit,
                    inline=True,
                    fmt=lambda v: f"ICNIRP {v:g} A/m",
                    fontsize=10,
                    colors="blue",
                    rightside_up=True,
                )
                for label in limit_labels:
                    label.set_bbox({"facecolor": "white", "edgecolor": "none", "pad": 3})
                show_blue_limit_line = True

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
            zorder=3.0,
        )
        plt.gca().add_artist(rectangle)

        # Gefüllte Kreise an den Enden
        circle1 = plt.Circle((0, self.R_m), r_leiter_m, color=antennenfarbe, fill=True, zorder=3.0)
        circle2 = plt.Circle((0, -self.R_m), r_leiter_m, color=antennenfarbe, fill=True, zorder=3.0)
        plt.gca().add_artist(circle1)
        plt.gca().add_artist(circle2)

        # Raster & Achsen
        plt.xticks(np.arange(-lim_x_m, lim_x_m + 1, x_step))
        plt.yticks(np.arange(-lim_y_m, lim_y_m + 1, y_step))
        plt.grid(True, which="major", linestyle="-", color="gray", alpha=0.3)
        plt.axhline(0, color="black", lw=1.2)
        plt.axvline(0, color="black", lw=1.2)

        plt.title("Magnetic Field Strength $|H|$", fontsize=12, pad=6, y=1.02)
        plt.xlabel("x [m]")
        plt.ylabel("y [m]")
        plt.gca().set_aspect("equal")
        plt.xlim(-lim_x_m, lim_x_m)
        plt.ylim(-lim_y_m, lim_y_m)

        # Contour lines are already masked for r <= 1.5D via H_total_masked.

        # Legende
        legend_elements = [
            Line2D([0], [0], color=antennenfarbe, lw=4, label="Antenna"),
            Line2D(
                [0], [0], marker="None", color="None", label=f"m = {self.m_Am2:.2f} A m²"
            ),
            Line2D(
                [0],
                [0],
                marker="None",
                color="None",
                label=f"f = {self.f_Hz / 1e6:.1f} MHz",
            ),
        ]
        if show_blue_limit_line:
            legend_elements.append(
                Line2D(
                    [0],
                    [0],
                    color="blue",
                    lw=1.6,
                    label=f"ICNIRP 1998 = {float(icnirp_limit_a_per_m):g} A/m",
                )
            )
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

    calculator.save_h_field_plot(
        lim_x_m=4,
        lim_y_m=3,
        filename=output_dir / "calculations.svg",
        x_step=1.0,
        y_step=1.0,
    )
    calculator.save_h_field_plot(
        lim_x_m=30,
        lim_y_m=60,
        filename=output_dir / "calculations_big.svg",
        x_step=10.0,
        y_step=10.0,
        levels=[0.001, 0.002, 0.005, 0.05],
    )


if __name__ == "__main__":
    main()
