#!/usr/bin/env python3
"""Generate charts for every antenna folder with s1p_measurements/."""

from __future__ import annotations

import dataclasses
import html
import math
import re
import shutil
from pathlib import Path

import matplotlib as mpl

mpl.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import least_squares

from antennenvergleich.constants import DIRECTORY_SRC
from antennenvergleich.constants_s1p import (
    C_100P_F,
    C_560P_F,
    DELAY_SUFFIX,
    DIRECTORY_S1P_RESULTS,
    MEASUREMENTS_SUBDIR,
    S1P_EXTENSION,
    SMITH_SUFFIX,
    SVG_EXTENSION,
    SWR_SUFFIX,
    VALUES_SUFFIX,
)
from antennenvergleich.datatype_inductance import Inductance
from antennenvergleich.datatypes_s1p import (
    AntennaModelFit,
    S1pValues,
    SwrValues,
)
from smith.smith_swr import (
    BACKGROUND_COLOR,
    FIGURE_SIZE_INCHES,
    draw_smith_chart,
    draw_swr_chart,
)

DIRECTORY_OF_THIS_FILE = Path(__file__).parent

CURVE_COLOR = "#e63946"
CURVE_LINEWIDTH = 2.0
filter_points_swr_limit_on = False
filter_points_swr_limit_swr = 6.0
"""For the circle fitting take only points where SWR is below 6"""

MODEL_COLOR = "#2dc653"

# Fit boundaries in physical units.
R_res_min_ohm = 1e-6
R_res_max_ohm = 200.0
Q_min = 5.0
Q_max = 500000.0
Lp_min_H = 1e-10
Lp_max_H = 1e-5
alpha_min_db = 0.0
alpha_max_db = 6.0
tau_min_s = -50e-9
tau_max_s = 100e-9


def _calc_l_from_fshift(f_off_hz: float, f_x_hz: float, c_x_f: float) -> float:
    return (1.0 / (f_x_hz**2) - 1.0 / (f_off_hz**2)) / (((2 * math.pi) ** 2) * c_x_f)


def _calc_c_from_fshift(f_low_hz: float, f_high_hz: float, l_h: float) -> float:
    return (1.0 / (f_low_hz**2) - 1.0 / (f_high_hz**2)) / (((2 * math.pi) ** 2) * l_h)


@dataclasses.dataclass(frozen=True)
class S1pCapFile:
    filename: Path
    s1p_values: S1pValues


@dataclasses.dataclass(frozen=True)
class S1pCapFiles:
    cap_off: S1pCapFile
    cap_100p: S1pCapFile
    cap_560p: S1pCapFile
    cap_nix: S1pCapFile


class S1pFiles(list[Path]):
    @property
    def cap_files(self) -> S1pCapFiles | None:
        def get_cap_file(tag: str) -> S1pCapFile | None:
            for p in self:
                if tag in p.stem.upper():
                    return S1pCapFile(
                        filename=p,
                        s1p_values=S1pValues.read_values_file(filename=p),
                    )

            return None

        files = S1pCapFiles(
            cap_off=get_cap_file("CAP_OFF"),  # type: ignore[arg-type]
            cap_100p=get_cap_file("CAP_100P"),  # type: ignore[arg-type]
            cap_560p=get_cap_file("CAP_560P"),  # type: ignore[arg-type]
            cap_nix=get_cap_file("CAP_NIX"),  # type: ignore[arg-type]
        )
        for file in (files.cap_off, files.cap_100p, files.cap_560p, files.cap_nix):
            if file is None:
                return None

        return files


def write_cap_inductance_values(output_subdir: Path) -> None:
    s1p_files = S1pFiles(sorted(output_subdir.glob(f"*{VALUES_SUFFIX}.py")))
    if len(s1p_files) == 0:
        return

    cap_files = s1p_files.cap_files
    if cap_files is None:
        return

    f_off_hz = cap_files.cap_off.s1p_values.swr_values.f_swr_hz_min
    f_100p_hz = cap_files.cap_100p.s1p_values.swr_values.f_swr_hz_min
    f_560p_hz = cap_files.cap_560p.s1p_values.swr_values.f_swr_hz_min
    f_nix_hz = cap_files.cap_nix.s1p_values.swr_values.f_swr_hz_min

    l_100p_h = _calc_l_from_fshift(f_off_hz, f_100p_hz, C_100P_F)
    l_560p_h = _calc_l_from_fshift(f_off_hz, f_560p_hz, C_560P_F)
    c_nix_f = _calc_c_from_fshift(f_off_hz, f_nix_hz, l_100p_h)

    inductance = Inductance(
        cap_nix_file=cap_files.cap_nix.filename.name,
        cap_off_file=cap_files.cap_off.filename.name,
        cap_100p_file=cap_files.cap_100p.filename.name,
        cap_560p_file=cap_files.cap_560p.filename.name,
        f_nix_hz=f_nix_hz,
        f_off_hz=f_off_hz,
        f_100p_hz=f_100p_hz,
        f_560p_hz=f_560p_hz,
        l_100p_h=l_100p_h,
        l_560p_h=l_560p_h,
        c_nix_f=c_nix_f,
    )
    inductance.write_py(filename=output_subdir / "inductance.py")


def model_s11(
    f: np.ndarray,
    R_res: float,
    f0_hz: float,
    Q: float,
    L_P: float,
    alpha: float,
    tau: float,
    z0: float = 50.0,
) -> np.ndarray:
    omega = 2 * np.pi * f
    omega0 = 2 * np.pi * f0_hz
    L_res = Q * R_res / omega0
    C_res = 1.0 / (omega0**2 * L_res)
    Z_s = R_res + 1j * omega * L_res
    Y_res = 1.0 / Z_s + 1j * omega * C_res
    Z_ant = 1j * omega * L_P + 1.0 / Y_res
    g = (Z_ant - z0) / (Z_ant + z0)
    alpha_f = alpha * np.sqrt(f / f0_hz)  # coax loss scales with sqrt(f), alpha at f0
    return g * 10 ** (-alpha_f / 10) * np.exp(-1j * 2 * omega * tau)


def estimate_b_tau_s(freqs_hz: np.ndarray, gamma: np.ndarray, f_swr_hz: float) -> float:
    """Estimate one-way cable delay via SWR-weighted linear fit of group delay.

    Thins data to one point per 100 kHz, then fits a line through the group
    delay weighted by SWR (large SWR = far from resonance = more reliable).
    b_tau_s = fit value at centre frequency / 2.
    Returns (b_tau_s, thinned_freqs_hz, tau_group_s, tau_fit_s).
    """
    _nan = (float("nan"), np.empty(0), np.empty(0), np.empty(0))
    if len(freqs_hz) < 2:
        return _nan
    # Keep one point per 100 kHz window; works for non-equidistant grids
    indices = [0]
    for i in range(1, len(freqs_hz)):
        if freqs_hz[i] - freqs_hz[indices[-1]] >= 100e3:
            indices.append(i)
    idx = np.array(indices)
    f = freqs_hz[idx]
    g = gamma[idx]
    if len(f) < 2:
        return _nan
    phase = np.unwrap(np.angle(g))
    omega = 2 * np.pi * f
    tau_group = -np.gradient(phase, omega)
    # Weight by SWR: high SWR = far from resonance = reliable cable-delay point
    mag = np.clip(np.abs(g), 0.0, 1.0 - 1e-12)
    swr_w = (1.0 + mag) / (1.0 - mag)
    # Fit only points within 90 % of the median group delay (excludes resonance spike)
    tau_ref = np.median(tau_group)
    fit_mask = np.abs(tau_group - tau_ref) <= 0.9 * np.abs(tau_ref)
    if fit_mask.sum() < 2:
        fit_mask = np.ones(len(tau_group), dtype=bool)
    poly = np.polyfit(f[fit_mask], tau_group[fit_mask], 1, w=swr_w[fit_mask])
    tau_fit = np.polyval(poly, f)
    b_tau_s = float(np.polyval(poly, f_swr_hz) / 2)
    return b_tau_s, f, tau_group, tau_fit


def fit_antenna_model(
    freqs_hz: np.ndarray,
    gamma_meas: np.ndarray,
    f0_hz: float,
    b_tau_s_hint: float = 0.0,
    z0: float = 50.0,
) -> AntennaModelFit | None:
    """Least-squares fit of the antenna model."""
    _mag = np.clip(np.abs(gamma_meas), 0.0, 1.0 - 1e-12)
    _w = (1.0 - _mag) / (1.0 + _mag)  # = 1/SWR: down-weights far-from-resonance points

    def residual(p):
        logR, logQ, logLp, alpha, tau_ns = p

        R = np.exp(logR)
        Q = np.exp(logQ)
        Lp = np.exp(logLp)
        tau = tau_ns * 1e-9

        g = model_s11(
            freqs_hz,
            R,
            f0_hz,
            Q,
            Lp,
            alpha,
            tau,
            z0,
        )

        return np.concatenate(
            (
                _w * (g.real - gamma_meas.real),
                _w * (g.imag - gamma_meas.imag),
            )
        )

    best = None

    for R0 in (0.05, 0.2, 1.0):
        for Q0 in (50, 150, 500, 1500):
            for Lp0 in (10e-9, 50e-9, 200e-9):
                res = least_squares(
                    residual,
                    x0=[
                        np.log(R0),
                        np.log(Q0),
                        np.log(Lp0),
                        0.2,  # alpha dB one-way
                        b_tau_s_hint * 1e9,  # tau ns
                    ],
                    bounds=(
                        [
                            np.log(R_res_min_ohm),
                            np.log(Q_min),
                            np.log(Lp_min_H),
                            alpha_min_db,
                            b_tau_s_hint * 1e9 - 122.0,
                        ],
                        [
                            np.log(R_res_max_ohm),
                            np.log(Q_max),
                            np.log(Lp_max_H),
                            alpha_max_db,
                            b_tau_s_hint * 1e9 + 12.0,
                        ],
                    ),
                    ftol=1e-13,
                    xtol=1e-13,
                    gtol=1e-13,
                    max_nfev=5000,
                )

                if best is None or res.cost < best.cost:
                    best = res

    if best is None or not best.success:
        return None

    logR, logQ, logLp, alpha, tau_ns = best.x

    R = np.exp(logR)
    Q = np.exp(logQ)
    Lp = np.exp(logLp)
    tau = tau_ns * 1e-9

    omega0 = 2 * np.pi * f0_hz

    L_res = Q * R / omega0
    C_res = 1.0 / (omega0**2 * L_res)

    return AntennaModelFit(
        R_res_ohm=float(R),
        L_res_H=float(L_res),
        C_res_F=float(C_res),
        L_P_H=float(Lp),
        f0_Hz=float(f0_hz),
        Q=float(Q),
        BSWR2_62_Hz=float(f0_hz / Q),
        alpha_db=float(alpha),
        tau_s=float(tau),
        fit_residual=float(best.cost),
        fit_success=bool(best.success),
        fit_message=str(best.message),
        fit_iterations=int(best.nfev),
    )


def load_s1p(path: Path) -> tuple[np.ndarray, np.ndarray]:
    """Return (frequencies_hz, gamma) arrays parsed from an S1P file.

    Only the RI (real-imaginary) format is handled.
    """
    freqs, gammas = [], []
    with path.open() as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("!"):
                continue
            if line.startswith("#"):
                parts = line.upper().split()
                if "RI" not in parts:
                    raise ValueError(
                        f"{path.name}: only RI format is supported, got: {line}"
                    )
                continue
            cols = line.split()
            freq, re, im = float(cols[0]), float(cols[1]), float(cols[2])
            freqs.append(freq)
            gammas.append(complex(re, im))
    return np.asarray(freqs), np.asarray(gammas)


def decimation_datapoints(
    freqs_hz: np.ndarray,
    gamma: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    spacing_fraction = 0.01  # min spacing = this fraction of |f - f_res|
    if len(freqs_hz) < 2:
        return freqs_hz, gamma
    f_res = freqs_hz[int(np.argmin(np.abs(gamma)))]
    # floor 100 Hz avoids zero spacing at f_res itself
    indices = [0]
    for i in range(1, len(freqs_hz)):
        min_spacing = max(100.0, spacing_fraction * abs(freqs_hz[i] - f_res))
        if freqs_hz[i] - freqs_hz[indices[-1]] >= min_spacing:
            indices.append(i)
    idx = np.array(indices)
    return freqs_hz[idx], gamma[idx]


def make_chart(s1p_path: Path, filename_svg: Path) -> S1pValues:
    freqs, gamma = load_s1p(s1p_path)
    freqs, gamma = decimation_datapoints(freqs, gamma)

    fig, ax = plt.subplots(figsize=FIGURE_SIZE_INCHES)
    fig.patch.set_facecolor(BACKGROUND_COLOR)
    _mag = np.clip(np.abs(gamma), 0.0, 1.0 - 1e-12)  # guard against |S11|>=1 noise
    swr = (1.0 + _mag) / (1.0 - _mag)
    mask = (
        (swr < filter_points_swr_limit_swr)
        if filter_points_swr_limit_on
        else np.ones(len(swr), dtype=bool)
    )

    idx = int(np.argmin(swr))
    swr_min = float(swr[idx])
    f_hz_min = float(freqs[idx])
    z_min = 50.0 * (1 + gamma[idx]) / (1 - gamma[idx])

    b_tau_s, b_tau_freqs_hz, b_tau_group_s, b_tau_fit_s = estimate_b_tau_s(
        freqs, gamma, f_hz_min
    )
    _tau_hint = 0.0 if math.isnan(b_tau_s) else b_tau_s

    model = (
        fit_antenna_model(freqs[mask], gamma[mask], f_hz_min, b_tau_s_hint=_tau_hint)
        if mask.sum() >= 3
        else None
    )
    g_model = None
    if model:
        g_model = model_s11(
            freqs,
            model.R_res_ohm,
            model.f0_Hz,
            model.Q,
            model.L_P_H,
            model.alpha_db,
            model.tau_s,
        )

    draw_smith_chart(ax)

    # Modell zuerst (im Hintergrund)
    if g_model is not None:
        ax.plot(
            g_model.real,
            g_model.imag,
            color=MODEL_COLOR,
            linewidth=8,
            zorder=1,
        )

    # Messpunkte ausserhalb des SWR-Limits
    ax.scatter(
        gamma.real[~mask],
        gamma.imag[~mask],
        s=8,
        color="grey",
        linewidths=0,
        zorder=2,
    )

    # Messpunkte innerhalb des SWR-Limits
    ax.scatter(
        gamma.real[mask],
        gamma.imag[mask],
        s=30,
        color=CURVE_COLOR,
        linewidths=0,
        zorder=3,
    )

    filename_svg.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(filename_svg, format="svg", bbox_inches="tight")

    plt.close(fig)

    swr_path = filename_svg.with_name(
        filename_svg.stem.replace(SMITH_SUFFIX, SWR_SUFFIX) + SVG_EXTENSION
    )
    fig, ax = plt.subplots(figsize=FIGURE_SIZE_INCHES)
    fig.patch.set_facecolor(BACKGROUND_COLOR)
    draw_swr_chart(ax, freqs, gamma, g_model)

    ax.legend(loc="best")
    fig.savefig(swr_path, format="svg", bbox_inches="tight")
    plt.close(fig)

    print(f"  {s1p_path.name}  →  {filename_svg.name}, {swr_path.name}")

    r_vna = (swr_min - 1.0) / (swr_min + 1.0)
    eta_swr = 1.0 - r_vna**2
    eta_swr_ant = None
    if model:
        r_ant = r_vna * 10 ** (model.alpha_db / 10.0)
        eta_swr_ant = 1.0 - r_ant**2

    # --- group delay diagram ---
    delay_path = filename_svg.with_name(
        filename_svg.stem.replace(SMITH_SUFFIX, DELAY_SUFFIX) + SVG_EXTENSION
    )
    fig_d, ax_d = plt.subplots(figsize=FIGURE_SIZE_INCHES)
    fig_d.patch.set_facecolor(BACKGROUND_COLOR)
    ax_d.set_facecolor(BACKGROUND_COLOR)
    # Remove 5 % outliers from scatter (top 5 % and bottom 5 %)
    lo, hi = np.percentile(b_tau_group_s, [5, 95]) if len(b_tau_group_s) else (0, 0)
    plot_mask = (b_tau_group_s >= lo) & (b_tau_group_s <= hi)
    ax_d.scatter(
        b_tau_freqs_hz[plot_mask] / 1e6,
        b_tau_group_s[plot_mask] * 1e9,
        s=20,
        color=CURVE_COLOR,
        linewidths=0,
        zorder=2,
        label="Gruppenl. (gemessen)",
    )
    ax_d.plot(
        b_tau_freqs_hz / 1e6,
        b_tau_fit_s * 1e9,
        color="#2dc653",
        linewidth=2,
        zorder=3,
        label=f"Linearfit  b_tau_s={b_tau_s * 1e9:.1f} ns",
    )
    # Resonance marker: exactly at f_hz_min on the fit line (y = b_tau_s * 2)
    if not math.isnan(b_tau_s):
        ax_d.scatter(
            [f_hz_min / 1e6],
            [b_tau_s * 2 * 1e9],
            s=120,
            color="#00ff44",
            edgecolors="white",
            linewidths=1,
            zorder=5,
            label=f"Resonanz {f_hz_min / 1e6:.3f} MHz",
        )
    ax_d.set_xlabel("Frequenz (MHz)")
    ax_d.set_ylabel("Gruppenlaufzeit (ns)")
    ax_d.set_title(s1p_path.stem)
    ax_d.legend(loc="best")
    fig_d.savefig(delay_path, format="svg", bbox_inches="tight")
    plt.close(fig_d)

    swr_values = SwrValues(
        swr_min=swr_min,
        eta_swr=eta_swr,
        eta_swr_ant=eta_swr_ant,
        f_swr_hz_min=f_hz_min,
        z_swr_min=z_min,
    )

    filename_values_py = filename_svg.with_name(
        filename_svg.stem.replace(SMITH_SUFFIX, VALUES_SUFFIX) + ".py"
    )
    # Ensure generated values files are importable as a package.
    (filename_values_py.parent / "__init__.py").touch(exist_ok=True)

    s1p_values = S1pValues(
        filename=s1p_path.name,
        swr_values=swr_values,
        model=model,
        b_tau_s=b_tau_s,
    )
    s1p_values.write_py(filename=filename_values_py)

    return s1p_values


def main() -> None:
    measurement_dirs = sorted(
        p for p in DIRECTORY_SRC.rglob(MEASUREMENTS_SUBDIR) if p.is_dir()
    )
    if not measurement_dirs:
        print(f"Keine Unterordner namens '{MEASUREMENTS_SUBDIR}' unter {DIRECTORY_SRC}")

    processed_any = False
    for s1p_dir in measurement_dirs:
        s1p_files = sorted(s1p_dir.rglob(f"*{S1P_EXTENSION}"))
        if not s1p_files:
            continue

        results_dir = s1p_dir.parent / DIRECTORY_S1P_RESULTS
        if results_dir.exists():
            shutil.rmtree(results_dir)
        results_dir.mkdir(parents=True, exist_ok=True)
        print(
            f"Verarbeite {s1p_dir.relative_to(DIRECTORY_SRC)}: {len(s1p_files)} Datei(en)"
        )

        for s1p_path in s1p_files:
            rel_parent = s1p_path.relative_to(s1p_dir).parent
            output_path = (
                results_dir
                / rel_parent
                / (s1p_path.stem + SMITH_SUFFIX + SVG_EXTENSION)
            )
            make_chart(s1p_path, output_path)

        write_cap_inductance_values(results_dir)

        processed_any = True

    if not processed_any:
        print(
            f"Keine {S1P_EXTENSION}-Dateien in Unterordnern namens '{MEASUREMENTS_SUBDIR}' unter {DIRECTORY_SRC}"
        )

    print("Fertig.")


if __name__ == "__main__":
    main()
