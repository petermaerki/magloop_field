#!/usr/bin/env python3
"""Generate charts for every antenna folder with s1p_measurements/."""

from __future__ import annotations

import html
import importlib
import math
import re
import shutil
import subprocess
from pathlib import Path

import matplotlib as mpl

mpl.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import least_squares

from antennenvergleich.constants import DIRECTORY_SRC
from antennenvergleich.constants_s1p import (
    DELAY_SUFFIX,
    MEASUREMENTS_SUBDIR,
    RESULTS_SUBDIR,
    S1P_EXTENSION,
    SMITH_SUFFIX,
    SVG_EXTENSION,
    SWR_SUFFIX,
    VALUES_SUFFIX,
)
from antennenvergleich.datatypes_s1p import (
    AntennaModelFit,
    SwrValues,
    ValuesDataFile,
)
from smith.smith_swr import (
    BACKGROUND_COLOR,
    FIGURE_SIZE_INCHES,
    draw_smith_chart,
    draw_swr_chart,
)

DIRECTORY_OF_THIS_FILE = Path(__file__).parent
RUFF_BIN = DIRECTORY_SRC.parent / ".venv" / "bin" / "ruff"

CURVE_COLOR = "#e63946"
CURVE_LINEWIDTH = 2.0
filter_points_swr_limit_on = False
filter_points_swr_limit_swr = 6.0
"""For the circle fitting take only points where SWR is below 6"""

MODEL_COLOR = "#2dc653"
C_100P_F = 100e-12
C_560P_F = 579e-12

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


def _remove_assignment(path: Path, var_name: str) -> None:
    text = path.read_text()
    pattern = rf"(?m)^{re.escape(var_name)}\s*=\s*.+\n?"
    text = re.sub(pattern, "", text)
    path.write_text(text)


def _calc_l_from_fshift(f_off_hz: float, f_x_hz: float, c_x_f: float) -> float:
    return (1.0 / (f_x_hz**2) - 1.0 / (f_off_hz**2)) / (((2 * math.pi) ** 2) * c_x_f)


def _calc_c_from_fshift(f_low_hz: float, f_high_hz: float, l_h: float) -> float:
    return (1.0 / (f_low_hz**2) - 1.0 / (f_high_hz**2)) / (((2 * math.pi) ** 2) * l_h)


def _write_inductance_file(
    output_subdir: Path,
    cap_nix_file: Path | None,
    cap_off_file: Path,
    cap_100p_file: Path,
    cap_560p_file: Path,
    f_nix_hz: float | None,
    f_off_hz: float,
    f_100p_hz: float,
    f_560p_hz: float,
    l_100p_h: float,
    l_560p_h: float,
    c_nix_f: float | None,
) -> None:
    inductance_path = output_subdir / "inductance.py"
    content = (
        '"""Induktivitaet aus CAP-Schaltmessungen (automatisch erzeugt)."""\n\n'
        f'FILE_CAP_NIX = "{cap_nix_file.name}"\n'
        if cap_nix_file is not None
        else 'FILE_CAP_NIX = ""\n'
    ) + (
        f'FILE_CAP_OFF = "{cap_off_file.name}"\n'
        f'FILE_CAP_100P = "{cap_100p_file.name}"\n'
        f'FILE_CAP_560P = "{cap_560p_file.name}"\n\n'
        f"C_100P_F = {C_100P_F:.12e}\n"
        f"C_560P_F = {C_560P_F:.12e}\n\n"
    ) + (
        f"F_NIX_HZ = {f_nix_hz:.6f}\n" if f_nix_hz is not None else "F_NIX_HZ = float('nan')\n"
    ) + (
        f"F_OFF_HZ = {f_off_hz:.6f}\n"
        f"F_100P_HZ = {f_100p_hz:.6f}\n"
        f"F_560P_HZ = {f_560p_hz:.6f}\n\n"
        f"L_100p_H = {l_100p_h:.12e}\n"
        f"L_560p_H = {l_560p_h:.12e}\n"
    ) + (
        f"CAP_NIX_F = {c_nix_f:.12e}\n"
        if c_nix_f is not None
        else "CAP_NIX_F = float('nan')\n"
    )
    inductance_path.write_text(content)

    try:
        subprocess.run(
            [str(RUFF_BIN), "format", str(inductance_path)],
            check=True,
        )
    except FileNotFoundError:
        print(f"Warnung: {RUFF_BIN} nicht gefunden, ueberspringe Formatierung.")
    except subprocess.CalledProcessError as exc:
        print(f"Warnung: ruff format fehlgeschlagen fuer {inductance_path}: {exc}")


def write_cap_inductance_values(output_subdir: Path) -> None:
    values_files = sorted(output_subdir.glob(f"*{VALUES_SUFFIX}.py"))
    if not values_files:
        return

    cap_off_files = [p for p in values_files if "CAP_OFF" in p.stem.upper()]
    cap_100p_files = [p for p in values_files if "CAP_100P" in p.stem.upper()]
    cap_560p_files = [p for p in values_files if "CAP_560P" in p.stem.upper()]
    cap_nix_files = [p for p in values_files if "CAP_NIX" in p.stem.upper()]

    if len(cap_off_files) != 1 or len(cap_100p_files) != 1 or len(cap_560p_files) != 1:
        return

    cap_off_file = cap_off_files[0]
    cap_100p_file = cap_100p_files[0]
    cap_560p_file = cap_560p_files[0]

    f_off_hz = read_values_file(cap_off_file).swr_values.f_swr_hz_min
    f_100p_hz = read_values_file(cap_100p_file).swr_values.f_swr_hz_min
    f_560p_hz = read_values_file(cap_560p_file).swr_values.f_swr_hz_min
    f_nix_hz = (
        read_values_file(cap_nix_files[0]).swr_values.f_swr_hz_min
        if len(cap_nix_files) == 1
        else None
    )

    l_100p_h = _calc_l_from_fshift(f_off_hz, f_100p_hz, C_100P_F)
    l_560p_h = _calc_l_from_fshift(f_off_hz, f_560p_hz, C_560P_F)
    c_nix_f = None
    if f_nix_hz is not None:
        # CAP_NIX estimate: extra capacitance from NIX -> OFF using L from 100 pF branch.
        c_nix_f = _calc_c_from_fshift(f_off_hz, f_nix_hz, l_100p_h)

    _write_inductance_file(
        output_subdir=output_subdir,
        cap_nix_file=cap_nix_files[0] if len(cap_nix_files) == 1 else None,
        cap_off_file=cap_off_file,
        cap_100p_file=cap_100p_file,
        cap_560p_file=cap_560p_file,
        f_nix_hz=f_nix_hz,
        f_off_hz=f_off_hz,
        f_100p_hz=f_100p_hz,
        f_560p_hz=f_560p_hz,
        l_100p_h=l_100p_h,
        l_560p_h=l_560p_h,
        c_nix_f=c_nix_f,
    )

    _remove_assignment(cap_100p_file, "C_100P_F")
    _remove_assignment(cap_100p_file, "L_100p_H")
    _remove_assignment(cap_100p_file, "L_560p_H")
    _remove_assignment(cap_560p_file, "C_560P_F")
    _remove_assignment(cap_560p_file, "L_560p_H")
    _remove_assignment(cap_560p_file, "L_100p_H")


def read_values_file(filename_values_py: Path) -> ValuesDataFile:
    """Load swr_values and model from a generated *_values.py file."""
    try:
        relative_py = filename_values_py.resolve().relative_to(DIRECTORY_SRC)
    except ValueError as exc:
        raise RuntimeError(
            f"{filename_values_py} liegt nicht unter {DIRECTORY_SRC}"
        ) from exc

    module_name = ".".join(relative_py.with_suffix("").parts)
    module = importlib.import_module(module_name)
    module = importlib.reload(module)

    swr_values = getattr(module, "swr_values", None)
    model = getattr(module, "model", None)

    if not isinstance(swr_values, SwrValues):
        raise TypeError(f"{filename_values_py.name}: swr_values hat unerwarteten Typ")
    if model is not None and not isinstance(model, AntennaModelFit):
        raise TypeError(f"{filename_values_py.name}: model hat unerwarteten Typ")

    return ValuesDataFile(swr_values=swr_values, model=model)


def write_measurement_html_files(output_subdir: Path) -> None:
    """Write one HTML report per *_values.py in the result directory."""
    values_files = sorted(output_subdir.glob(f"*{VALUES_SUFFIX}.py"))
    if not values_files:
        return

    antenna_dir_name = output_subdir.parent.name

    def fmt(value: object, decimals: int | None = None) -> str:
        if isinstance(value, (int, float)):
            if decimals is None:
                return f"{value:.0f}"
            return f"{value:.{decimals}f}"
        return str(value)

    for values_path in values_files:
        values = read_values_file(values_path)
        base_stem = values_path.stem.removesuffix(VALUES_SUFFIX)
        smith_name = f"{base_stem}{SMITH_SUFFIX}{SVG_EXTENSION}"
        swr_name = f"{base_stem}{SWR_SUFFIX}{SVG_EXTENSION}"
        delay_name = f"{base_stem}{DELAY_SUFFIX}{SVG_EXTENSION}"

        f0_hz = values.model.f0_Hz if values.model else None
        bswr = values.model.BSWR2_62_Hz if values.model else None
        alpha = values.model.alpha_db if values.model else None
        tau_ns = values.model.tau_s * 1e9 if values.model else None
        eta_ant = values.swr_values.eta_swr_ant
        swr_min = values.swr_values.swr_min

        doc = f"""<!doctype html>
<html lang=\"de\">
<head>
    <meta charset=\"utf-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
    <title>{html.escape(base_stem)} - report</title>
    <style>
        body {{ font-family: sans-serif; margin: 1.5rem; }}
        table {{ border-collapse: collapse; width: 100%; max-width: 760px; }}
        th, td {{ border: 1px solid #ccc; padding: 0.4rem 0.6rem; text-align: left; }}
        th {{ background: #f4f4f4; width: 40%; }}
        h2 {{ margin-top: 2rem; }}
        .plot img {{ width: 100%; height: auto; border: 1px solid #ddd; }}
    </style>
</head>
<body>
    <h1>{html.escape(antenna_dir_name)}: {html.escape(base_stem)}</h1>
    <table>
        <tbody>
            <tr><th>File</th><td>{html.escape(values_path.name)}</td></tr>
            <tr><th>model_f0_Hz</th><td>{html.escape(fmt(f0_hz, 0))}</td></tr>
            <tr><th>model_BSWR2_62_Hz</th><td>{html.escape(fmt(bswr, 0))}</td></tr>
            <tr><th>model_alpha_db</th><td>{html.escape(fmt(alpha, 3))}</td></tr>
            <tr><th>model_tau_ns</th><td>{html.escape(fmt(tau_ns, 2))}</td></tr>
            <tr><th>eta_SWR_ant</th><td>{html.escape(fmt(eta_ant, 3))}</td></tr>
            <tr><th>swr_min</th><td>{html.escape(fmt(swr_min, 3))}</td></tr>
        </tbody>
    </table>

    <h2>Diagramme</h2>
    <div class=\"plot\">
        <h3>Smith</h3>
        <a href=\"{html.escape(smith_name)}\"><img src=\"{html.escape(smith_name)}\" alt=\"{html.escape(base_stem)} smith\"></a>
    </div>
    <div class=\"plot\">
        <h3>SWR</h3>
        <a href=\"{html.escape(swr_name)}\"><img src=\"{html.escape(swr_name)}\" alt=\"{html.escape(base_stem)} swr\"></a>
    </div>
    <div class=\"plot\">
        <h3>Delay</h3>
        <a href=\"{html.escape(delay_name)}\"><img src=\"{html.escape(delay_name)}\" alt=\"{html.escape(base_stem)} delay\"></a>
    </div>
</body>
</html>
"""

        report_path = output_subdir / f"{base_stem}.html"
        report_path.write_text(doc)


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


def make_chart(s1p_path: Path, filename_svg: Path) -> None:
    freqs, gamma = load_s1p(s1p_path)
    freqs, gamma = decimation_datapoints(freqs, gamma)

    fig, ax = plt.subplots(figsize=FIGURE_SIZE_INCHES)
    fig.patch.set_facecolor(BACKGROUND_COLOR)
    _mag = np.clip(np.abs(gamma), 0.0, 1.0 - 1e-12)  # guard against |S11|>=1 noise
    swr = (1.0 + _mag) / (1.0 - _mag)
    mask = (swr < filter_points_swr_limit_swr) if filter_points_swr_limit_on else np.ones(len(swr), dtype=bool)

    idx = int(np.argmin(swr))
    swr_min = float(swr[idx])
    f_hz_min = float(freqs[idx])
    z_min = 50.0 * (1 + gamma[idx]) / (1 - gamma[idx])

    b_tau_s, b_tau_freqs_hz, b_tau_group_s, b_tau_fit_s = estimate_b_tau_s(freqs, gamma, f_hz_min)
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
        label=f"Linearfit  b_tau_s={b_tau_s*1e9:.1f} ns",
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
            label=f"Resonanz {f_hz_min/1e6:.3f} MHz",
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

    with filename_values_py.open("w") as fw:
        fw.write("import numpy as np\n")
        fw.write(
            "from antennenvergleich.datatypes_s1p import AntennaModelFit, SwrValues\n"
        )
        fw.write(f"swr_values = {swr_values!r}\n")
        fw.write(f"model = {model!r}\n")
        b_tau_s_lit = "float('nan')" if math.isnan(b_tau_s) else repr(b_tau_s)
        fw.write(f"b_tau_s = {b_tau_s_lit}\n")

    try:
        subprocess.run(
            [str(RUFF_BIN), "format", str(filename_values_py)],
            check=True,
        )
    except FileNotFoundError:
        print(f"Warnung: {RUFF_BIN} nicht gefunden, ueberspringe Formatierung.")
    except subprocess.CalledProcessError as exc:
        print(f"Warnung: ruff format fehlgeschlagen fuer {filename_values_py}: {exc}")


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

        results_dir = s1p_dir.parent / RESULTS_SUBDIR
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
        write_measurement_html_files(results_dir)

        processed_any = True

    if not processed_any:
        print(
            f"Keine {S1P_EXTENSION}-Dateien in Unterordnern namens '{MEASUREMENTS_SUBDIR}' unter {DIRECTORY_SRC}"
        )

    print("Fertig.")


if __name__ == "__main__":
    main()
