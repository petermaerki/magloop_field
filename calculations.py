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
_KR_NEAR = 0.3
_KR_FAR = 1.0
# Transition tuning for the hybrid model:
# keep the elliptic (quasi-static) solution dominant for kr < 0.3,
# blend in the mid zone, and enforce pure retarded behavior for kr >= 1.0.


def _ellip_rf(x, y, z, tol=1e-12, max_iter=60):
    """Carlson symmetric integral RF(x, y, z) for non-negative x, y, z."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    z = np.asarray(z, dtype=float)
    x, y, z = np.broadcast_arrays(x, y, z)

    an = (x + y + z) / 3.0
    xn = x.copy()
    yn = y.copy()
    zn = z.copy()

    for _ in range(max_iter):
        sx = np.sqrt(xn)
        sy = np.sqrt(yn)
        sz = np.sqrt(zn)
        lam = sx * sy + sx * sz + sy * sz
        xn = 0.25 * (xn + lam)
        yn = 0.25 * (yn + lam)
        zn = 0.25 * (zn + lam)
        an = 0.25 * (an + lam)

        dx = np.abs(1.0 - xn / an)
        dy = np.abs(1.0 - yn / an)
        dz = np.abs(1.0 - zn / an)
        if np.max(np.stack([dx, dy, dz])) < tol:
            break

    xbar = 1.0 - xn / an
    ybar = 1.0 - yn / an
    zbar = 1.0 - zn / an
    e2 = xbar * ybar - zbar * zbar
    e3 = xbar * ybar * zbar
    poly = 1.0 - e2 / 10.0 + e3 / 14.0 + (e2 * e2) / 24.0 - (3.0 * e2 * e3) / 44.0
    return poly / np.sqrt(an)


def _ellip_rd(x, y, z, tol=1e-12, max_iter=60):
    """Carlson symmetric integral RD(x, y, z) for non-negative x, y, z>0."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    z = np.asarray(z, dtype=float)
    x, y, z = np.broadcast_arrays(x, y, z)

    xn = x.copy()
    yn = y.copy()
    zn = z.copy()
    sigma = np.zeros_like(xn)
    fac = np.ones_like(xn)

    for _ in range(max_iter):
        sx = np.sqrt(xn)
        sy = np.sqrt(yn)
        sz = np.sqrt(zn)
        lam = sx * (sy + sz) + sy * sz
        sigma += fac / (sz * (zn + lam))
        fac *= 0.25
        xn = 0.25 * (xn + lam)
        yn = 0.25 * (yn + lam)
        zn = 0.25 * (zn + lam)

        an = (xn + yn + 3.0 * zn) / 5.0
        dx = np.abs(1.0 - xn / an)
        dy = np.abs(1.0 - yn / an)
        dz = np.abs(1.0 - zn / an)
        if np.max(np.stack([dx, dy, dz])) < tol:
            break

    an = (xn + yn + 3.0 * zn) / 5.0
    xbar = 1.0 - xn / an
    ybar = 1.0 - yn / an
    zbar = 1.0 - zn / an

    ea = xbar * ybar
    eb = zbar * zbar
    ec = ea - eb
    ed = ea - 6.0 * eb
    ef = ed + 2.0 * ec

    s1 = ed * (-3.0 / 14.0 + (9.0 / 88.0) * ed - (9.0 / 52.0) * zbar * ef)
    s2 = zbar * ((1.0 / 6.0) * ef + zbar * (-(9.0 / 22.0) * ec + (3.0 / 26.0) * zbar * ea))
    return 3.0 * sigma + fac * (1.0 + s1 + s2) / (an * np.sqrt(an))


def _ellipk_e_from_m(m):
    """Complete elliptic integrals K(m), E(m) with parameter m in [0, 1)."""
    m = np.asarray(m, dtype=float)
    m = np.clip(m, 0.0, 1.0 - 1e-15)
    k_val = _ellip_rf(0.0, 1.0 - m, 1.0)
    e_val = k_val - (m / 3.0) * _ellip_rd(0.0, 1.0 - m, 1.0)
    return k_val, e_val


@dataclasses.dataclass(frozen=True)
class AntennaCalculator:
    """Computes antenna parameters from geometry and measurement."""

    antenna_D_m: float    # loop diameter [m]
    d_m: float    # conductor diameter [m]
    f_Hz: float   # frequency [Hz]
    bw_Hz: float  # bandwidth B_SWR2.62 [Hz]
    P_W: float    # power into antenna [W]

    @property
    def L_H(self) -> float:
        """Inductance [H]"""
        return _MU0 * (self.antenna_D_m / 2) * (math.log(8 * self.antenna_D_m / self.d_m) - 2)

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
        return math.pi * (self.antenna_D_m / 2) ** 2

    @property
    def RR_Ohm(self) -> float:
        """Radiation resistance [Ohm] — Rayleigh term with King finite-size correction."""
        rayleigh = 31171.0 * ((self.A_m2 * self.f_Hz**2) / _C_LIGHT**2) ** 2
        king_correction = 1.0 + 0.5 * ((math.pi * self.antenna_D_m * self.f_Hz) / _C_LIGHT) ** 2
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
    antenna_D_m: float
    R_m: float
    m_Am2: float
    f_Hz: float

    @property
    def h_field(self) -> float:
        return self.m_Am2 * 2

    def h_field_elliptic_abs_xyz(self, x_m, y_m, z_m, m_Am2, antenna_D_m):
        """Exact |H| of a circular loop via elliptic integrals (magnetostatic closed form).

        Geometry used in this project:
        - Loop lies in the y-z plane
        - Loop axis is the x-axis
        - Loop radius R = D/2
        """
        x_m = np.asarray(x_m, dtype=float)
        y_m = np.asarray(y_m, dtype=float)
        z_m = np.asarray(z_m, dtype=float)

        R_m = 0.5 * float(antenna_D_m)
        I_main_loop_A = float(m_Am2) / (math.pi * R_m**2)

        # Cylindrical coordinates around x-axis (loop axis)
        rho_m = np.sqrt(y_m**2 + z_m**2)
        x2 = x_m**2
        alpha2 = (R_m - rho_m) ** 2 + x2
        beta2 = (R_m + rho_m) ** 2 + x2
        m_param = np.clip(4.0 * R_m * rho_m / np.maximum(beta2, 1e-30), 0.0, 1.0 - 1e-15)

        K_m, E_m = _ellipk_e_from_m(m_param)
        beta = np.sqrt(np.maximum(beta2, 1e-30))
        alpha2_safe = np.maximum(alpha2, 1e-30)

        # Brho, Bx from standard loop formulas (mapped to axis=x).
        pref_bx = _MU0 * I_main_loop_A / (2.0 * math.pi * beta)
        bx = pref_bx * (K_m + ((R_m**2 - rho_m**2 - x2) / alpha2_safe) * E_m)

        pref_brho = _MU0 * I_main_loop_A * x_m / (2.0 * math.pi * np.maximum(rho_m, 1e-30) * beta)
        brho = pref_brho * (-K_m + ((R_m**2 + rho_m**2 + x2) / alpha2_safe) * E_m)

        # On-axis limit (rho -> 0): Brho=0, exact finite Bx expression.
        axis_mask = rho_m < 1e-12
        if np.any(axis_mask):
            bx_axis = _MU0 * I_main_loop_A * R_m**2 / (2.0 * (R_m**2 + x2) ** 1.5)
            bx = np.where(axis_mask, bx_axis, bx)
            brho = np.where(axis_mask, 0.0, brho)

        b_abs = np.sqrt(bx**2 + brho**2)
        return b_abs / _MU0

    def h_field_retarded_dipole_abs_xyz(self, x_m, y_m, z_m, m_Am2, f_Hz):
        """Retarded magnetic dipole |H| at Cartesian point (x, y, z)."""
        k = 2.0 * np.pi * f_Hz / _C_LIGHT
        fac = m_Am2 / (4.0 * np.pi)

        x_m = np.asarray(x_m, dtype=float)
        y_m = np.asarray(y_m, dtype=float)
        z_m = np.asarray(z_m, dtype=float)

        r = np.sqrt(x_m**2 + y_m**2 + z_m**2)
        r = np.maximum(r, 1e-9)
        rho = np.sqrt(y_m**2 + z_m**2)
        phi = np.arctan2(rho, x_m)

        h_r_sq = fac**2 * 4.0 * np.cos(phi) ** 2 * (1.0 / r**6 + k**2 / r**4)
        h_theta_sq = fac**2 * np.sin(phi) ** 2 * (1.0 / r**6 - k**2 / r**4 + k**4 / r**2)
        return np.sqrt(h_r_sq + h_theta_sq)

    def h_field_abs_xyz(self, x_m, y_m, z_m, m_Am2, antenna_D_m, f_Hz):
        """Hybrid |H| model: exact elliptic near field, retarded dipole far field.

        Transition uses kr = 2*pi*r/lambda with smooth blending in the mid range.
        In the far zone (kr >= kr_far), the result is exactly the retarded model.
        """
        x_m = np.asarray(x_m, dtype=float)
        y_m = np.asarray(y_m, dtype=float)
        z_m = np.asarray(z_m, dtype=float)

        h_ell = self.h_field_elliptic_abs_xyz(x_m, y_m, z_m, m_Am2, antenna_D_m)
        h_ret = self.h_field_retarded_dipole_abs_xyz(x_m, y_m, z_m, m_Am2, f_Hz)

        r = np.sqrt(x_m**2 + y_m**2 + z_m**2)
        kr = 2.0 * np.pi * f_Hz * r / _C_LIGHT

        # Near: pure elliptic. Mid: smooth blend. Far: pure retarded.
        t = np.clip((kr - _KR_NEAR) / (_KR_FAR - _KR_NEAR), 0.0, 1.0)
        w_far = t * t * (3.0 - 2.0 * t)  # smoothstep
        return (1.0 - w_far) * h_ell + w_far * h_ret

    def figure_h_field_plot(
        self,
        lim_x_m,
        lim_y_m,
        x_step,
        y_step,
        levels=None,
        icnirp_limit_a_per_m=None,
        show_icnirp_blue=False,
        d_min_abstand_m=0.01,
    ) -> matplotlib.figure.Figure:
        self._save_h_field_plot(
            lim_x_m=lim_x_m,
            lim_y_m=lim_y_m,
            x_step=x_step,
            y_step=y_step,
            levels=levels,
            icnirp_limit_a_per_m=icnirp_limit_a_per_m,
            show_icnirp_blue=show_icnirp_blue,
            d_min_abstand_m=d_min_abstand_m,
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
        d_min_abstand_m=0.01,
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
            d_min_abstand_m=d_min_abstand_m,
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
        d_min_abstand_m=0.01,
    ) -> None:
        x = np.linspace(-lim_x_m, lim_x_m, 1000)
        y = np.linspace(-lim_y_m, lim_y_m, 1000)
        X, Y = np.meshgrid(x, y)
        H_total = self.h_field_abs_xyz(
            X,
            Y,
            0.0,
            self.m_Am2,
            self.antenna_D_m,
            self.f_Hz,
        )

        # Split contours into far/near region by distance to the conductor axis.
        # Loop axis is x, loop lies in y-z plane, and this plot slice uses z=0.
        rho_m = np.sqrt(Y**2)
        d_abstand_zu_wire = np.sqrt((rho_m - self.R_m) ** 2 + X**2)
        near_region = d_abstand_zu_wire < float(d_min_abstand_m)
        H_total_far = np.ma.masked_where(near_region, H_total)

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
            H_total_far,
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
            h_min = float(np.ma.min(H_total_far))
            h_max = float(np.ma.max(H_total_far))
            if h_min <= float(icnirp_limit_a_per_m) <= h_max:
                cp_limit = plt.contour(
                    X,
                    Y,
                    H_total_far,
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

        antennenfarbe = "red"
        # Draw conductor with end caps using centerline diameter convention.
        # D refers to the centerline (cap centers at y=±R), so outer length is D + d_leiter.
        d_leiter_m = 0.1
        r_leiter_m = d_leiter_m / 2
        rectangle = plt.Rectangle(
            (-r_leiter_m, -self.R_m),
            d_leiter_m,
            2 * self.R_m,
            color=antennenfarbe,
            fill=True,
            zorder=3.0,
        )
        plt.gca().add_artist(rectangle)

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

        # Contour lines are shown only outside the near-conductor exclusion zone.

        # Legende
        legend_elements = [
            Line2D([0], [0], color=antennenfarbe, lw=4, label="Antenna"),
            Line2D(
                [0],
                [0],
                marker="None",
                color="None",
                label=f"D = {self.antenna_D_m:.3g} m",
            ),
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
        plt.legend(handles=legend_elements, loc="upper right", frameon=True)

        # Keep figure margins minimal and deterministic for web rendering.
        plt.subplots_adjust(left=0.06, right=0.995, bottom=0.06, top=0.96)


def main() -> None:
    antenna_D_m = 1.0
    I_A = 10.5
    m_Am2 = I_A * np.pi * (antenna_D_m / 2) ** 2
    calculator = Calculator(
        antenna_D_m=antenna_D_m,
        R_m=antenna_D_m / 2,
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
