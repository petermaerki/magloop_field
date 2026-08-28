import dataclasses
import math

import numpy as np
from antennenvergleich . constants import C_LIGHT_MS
from scipy import special

_MU0 = 4.0 * math.pi * 1e-7  # H/m
_KR_NEAR = 0.3
_KR_FAR = 1.0
# Transition tuning for the hybrid model:
# keep the elliptic (quasi-static) solution dominant for kr < 0.3,
# blend in the mid zone, and enforce pure retarded behavior for kr >= 1.0.


def icnirp_1998_h_limit_a_per_m(f_hz: float) -> float:
    """ICNIRP 1998 reference level for magnetic field strength H [A/m] (general public), RF range."""
    f_mhz = f_hz / 1e6
    if f_mhz < 10.0:
        return 0.73 / max(f_mhz, 1e-9)
    if f_mhz <= 400.0:
        return 0.073
    if f_mhz <= 2000.0:
        return 0.0037 * math.sqrt(f_mhz)
    return 0.16


def icnirp_1998_h_limit_section_text(f_hz: float) -> str:
    """Human-readable ICNIRP 1998 note focused on HF range only."""
    return (
        "Using ICNIRP 1998 general public: "
        "0.1-10 MHz: H = 0.73/f_MHz A/m; "
        "10-30 MHz: H = 0.073 A/m."
    )

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
    s2 = zbar * (
        (1.0 / 6.0) * ef + zbar * (-(9.0 / 22.0) * ec + (3.0 / 26.0) * zbar * ea)
    )
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

    D_m: float
    """
    loop diameter [m]
    """

    d_m: float
    """
    conductor diameter [m]
    """

    n: int
    """
    loop count
    """
    swr_min: float
    """
    minimum SWR at antenna input [-]
    """

    f_Hz: float
    """
    frequency [Hz]
    """

    bw262_Hz: float
    """
    bandwidth B_SWR2.62 [Hz]
    """

    powerP_W: float
    """
    power into antenna [W]
    """
    p_m: float = 0.0
    """
    winding pitch [m] for multi-turn coils
    """

    def __post_init__(self) -> None:
        assert self.n > 0, f"n must be a positive integer, got {self.n}"
        assert isinstance(self.n, int) and not isinstance(self.n, bool), (
            f"n must be an integer, got {self.n}"
        )
        assert self.d_m > 0, f"d_m must be positive, got {self.d_m}"
        assert self.p_m >= 0, f"p_m must be non-negative, got {self.p_m}"
        if self.n > 1:
            assert self.p_m > 0.0, f"p_m must be positive for n > 1, got {self.p_m}"
        assert self.D_m > 0, f"D_m must be positive, got {self.D_m}"

    @property
    def L_H(self) -> float:
        assert self.D_m > 0
        assert self.d_m > 0
        assert self.n > 0

        radius_m = self.D_m / 2.0
        conductor_radius_m = self.d_m / 2.0

        # Self-inductance of a single circular loop made from round wire.
        l_single = _MU0 * radius_m * (math.log(8 * radius_m / conductor_radius_m) - 2.0)

        if self.n == 1:
            return l_single

        # Mutual inductance of two identical coaxial circular turns.
        # The pitch is the axial distance between the centers of adjacent turns.
        total = self.n * l_single
        for separation in range(1, self.n):
            pitch_m = separation * self.p_m
            k_sq = (4 * radius_m * radius_m) / (
                4 * radius_m * radius_m + pitch_m * pitch_m
            )
            if math.isclose(k_sq, 1.0, rel_tol=0.0, abs_tol=1e-12):
                mutual = l_single
            else:
                k = math.sqrt(k_sq)
                k_elliptic = special.ellipk(k_sq)
                e_elliptic = special.ellipe(k_sq)
                mutual = (
                    _MU0
                    * radius_m
                    * (2.0 / k)
                    * ((1.0 - k_sq / 2.0) * k_elliptic - e_elliptic)
                )
            total += 2.0 * (self.n - separation) * mutual

        return total

    @property
    def C_F(self) -> float:
        """Resonance capacitance [F]"""
        return 1.0 / ((2 * math.pi * self.f_Hz) ** 2 * self.L_H)

    @property
    def Q0(self) -> float:
        """Unloaded quality factor"""
        return self.f_Hz / self.bw262_Hz

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
        rayleigh = 31171.0 * ((self.A_m2 * self.f_Hz**2) / C_LIGHT_MS**2) ** 2
        king_correction = 1.0 + 0.5 * ((math.pi * self.D_m * self.f_Hz) / C_LIGHT_MS) ** 2
        return self.n**2 * rayleigh * king_correction

    @property
    def RLoss_Ohm(self) -> float:
        return self.RT_Ohm - self.RR_Ohm

    @property
    def eta(self) -> float:
        return self.eta_antenna * self.eta_SWR_ant

    @property
    def eta_antenna(self) -> float:
        return self.RR_Ohm / self.RT_Ohm if self.RT_Ohm > 0 else 0.0

    @property
    def eta_SWR_ant(self) -> float:
        s = self.swr_min
        if s <= 0:
            return 0.0
        return 4.0 * s / (1.0 + s) ** 2

    @property
    def I_main_loop_A(self) -> float:
        """Loop current [A]"""
        return math.sqrt(self.powerP_W / self.RT_Ohm)

    @property
    def U_loop_V(self) -> float:
        """Loop voltage [V]"""
        return self.I_main_loop_A * self.XL

    @property
    def m_Am2(self) -> float:
        """Magnetic dipole moment [A m²]"""
        return self.n * self.I_main_loop_A * self.A_m2


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
        m_param = np.clip(
            4.0 * R_m * rho_m / np.maximum(beta2, 1e-30), 0.0, 1.0 - 1e-15
        )

        K_m, E_m = _ellipk_e_from_m(m_param)
        beta = np.sqrt(np.maximum(beta2, 1e-30))
        alpha2_safe = np.maximum(alpha2, 1e-30)

        # Brho, Bx from standard loop formulas (mapped to axis=x).
        pref_bx = _MU0 * I_main_loop_A / (2.0 * math.pi * beta)
        bx = pref_bx * (K_m + ((R_m**2 - rho_m**2 - x2) / alpha2_safe) * E_m)

        pref_brho = (
            _MU0
            * I_main_loop_A
            * x_m
            / (2.0 * math.pi * np.maximum(rho_m, 1e-30) * beta)
        )
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
        k = 2.0 * np.pi * f_Hz / C_LIGHT_MS
        fac = m_Am2 / (4.0 * np.pi)

        x_m = np.asarray(x_m, dtype=float)
        y_m = np.asarray(y_m, dtype=float)
        z_m = np.asarray(z_m, dtype=float)

        r = np.sqrt(x_m**2 + y_m**2 + z_m**2)
        r = np.maximum(r, 1e-9)
        rho = np.sqrt(y_m**2 + z_m**2)
        phi = np.arctan2(rho, x_m)

        h_r_sq = fac**2 * 4.0 * np.cos(phi) ** 2 * (1.0 / r**6 + k**2 / r**4)
        h_theta_sq = (
            fac**2 * np.sin(phi) ** 2 * (1.0 / r**6 - k**2 / r**4 + k**4 / r**2)
        )
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
        kr = 2.0 * np.pi * f_Hz * r / C_LIGHT_MS

        # Near: pure elliptic. Mid: smooth blend. Far: pure retarded.
        t = np.clip((kr - _KR_NEAR) / (_KR_FAR - _KR_NEAR), 0.0, 1.0)
        w_far = t * t * (3.0 - 2.0 * t)  # smoothstep
        return (1.0 - w_far) * h_ell + w_far * h_ret
