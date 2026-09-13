"""Find the resonator from three impedance measurements.

Methodology:
1. Use the three measured impedance points to compute SWR values and generate
   the two physically possible resonator branches (under-coupled and
   over-coupled). This step intentionally ignores phase, because a cable,
   fixture, transformer or other unknown series path can add phase that is not
   known a priori.
2. Use the Smith chart to decide which branch is consistent with the measured
   geometry: if the fitted circle through the three points encloses the 50 Ohm
   point, the resonator is over-coupled; otherwise it is under-coupled.
3. Once the correct branch has been selected, fit the final resonator model
    with an equivalent series reactance jXseries to account for the real port
    conditions, such as cable inductance, feedpoint parasitics, connector and
    fixture effects.

This separation keeps the physics clear: the SWR step determines the resonator
candidate without assuming a phase reference, while jXseries describes the
additional port-side reactance seen in the real measurement setup.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
from scipy.optimize import least_squares

Measurement = tuple[float, complex]
MeasurementSet = Sequence[Measurement]


@dataclass(frozen=True)
class ImpedanceMeasurementSet:
    name: str
    measurements: tuple[Measurement, ...]


@dataclass(frozen=True)
class ResonatorFit:
    fres_hz: float
    l_h: float
    c_f: float
    rpar_ohm: float
    bandwidth_hz: float
    jx_series_ohm: float
    rmse_ohm: float


@dataclass(frozen=True)
class SWRCandidate:
    label: str
    rpar_ohm: float
    q: float
    fres_hz: float
    bandwidth_hz: float
    l_h: float
    c_f: float


def swr_from_impedance(z: complex, z0: float = 50.0) -> float:
    """Return the standing-wave ratio for a complex impedance."""
    if z0 <= 0:
        raise ValueError("z0 must be positive")
    gamma = abs((z - z0) / (z + z0))
    if np.isclose(gamma, 1.0):
        return float("inf")
    return (1.0 + gamma) / (1.0 - gamma)


def s_q(
    rpar_ohm: float, f0_hz: float, f_free_hz: float, swr_free: float, z0: float = 50.0
) -> float:
    """Solve Q from one off-resonance SWR point and the resonant SWR minimum."""
    gamma = (swr_free - 1.0) / (swr_free + 1.0)
    delta_sq = (gamma**2 * (rpar_ohm + z0) ** 2 - (rpar_ohm - z0) ** 2) / (
        z0**2 * (1.0 - gamma**2)
    )
    x = f_free_hz / f0_hz - f0_hz / f_free_hz
    return float(np.sqrt(max(delta_sq, 0.0)) / abs(x))


def circle_from_three_points(points: Sequence[complex]) -> tuple[complex, float]:
    """Fit a circle through three complex points and return center and radius."""
    if len(points) != 3:
        raise ValueError("exactly three points are required")
    a, b, c = (complex(p) for p in points)
    d = 2.0 * (
        a.real * (b.imag - c.imag)
        + b.real * (c.imag - a.imag)
        + c.real * (a.imag - b.imag)
    )
    if np.isclose(d, 0.0):
        raise ValueError("points are collinear; no unique circle exists")
    ux = (
        (abs(a) ** 2) * (b.imag - c.imag)
        + (abs(b) ** 2) * (c.imag - a.imag)
        + (abs(c) ** 2) * (a.imag - b.imag)
    ) / d
    uy = (
        (abs(a) ** 2) * (c.real - b.real)
        + (abs(b) ** 2) * (a.real - c.real)
        + (abs(c) ** 2) * (b.real - a.real)
    ) / d
    center = complex(ux, uy)
    radius = abs(center - a)
    return center, float(radius)


def circle_contains_point(center: complex, radius: float, point: complex) -> bool:
    """Return True if the point lies inside or on the circle."""
    return abs(point - center) <= radius + 1e-12


def select_coupling_from_smith(measurements: MeasurementSet, z0: float = 50.0) -> str:
    """Return 'overcoupled' if the measured impedance circle encloses 50 Ohm."""
    points = [complex(z) / z0 for _, z in measurements]
    center, radius = circle_from_three_points(points)
    if circle_contains_point(center, radius, 1.0 + 0.0j):
        return "overcoupled"
    return "undercoupled"


def fit_swr_candidates(
    measurements: MeasurementSet, z0: float = 50.0
) -> tuple[SWRCandidate, SWRCandidate]:
    """Generate the two physically possible SWR-only resonator branches."""
    freqs_hz = np.asarray([freq_hz for freq_hz, _ in measurements], dtype=float)
    swr_values = np.asarray(
        [swr_from_impedance(z, z0=z0) for _, z in measurements], dtype=float
    )
    f0_hz = float(freqs_hz[np.argmin(swr_values)])
    swr_min = float(np.min(swr_values))
    f_free_hz = float(freqs_hz[np.argmax(np.abs(freqs_hz - f0_hz))])
    swr_free = float(swr_values[np.argmax(np.abs(freqs_hz - f0_hz))])

    candidates: list[SWRCandidate] = []
    for label, rpar in (
        ("undercoupled", z0 / swr_min),
        ("overcoupled", z0 * swr_min),
    ):
        q = s_q(rpar, f0_hz, f_free_hz, swr_free, z0=z0)
        omega_0 = 2.0 * np.pi * f0_hz
        l_h = rpar / (q * omega_0)
        c_f = q / (omega_0 * rpar)
        bandwidth_hz = f0_hz / q
        candidates.append(
            SWRCandidate(
                label=label,
                rpar_ohm=float(rpar),
                q=float(q),
                fres_hz=float(f0_hz),
                bandwidth_hz=float(bandwidth_hz),
                l_h=float(l_h),
                c_f=float(c_f),
            )
        )
    return tuple(candidates)


def choose_swr_candidate(
    measurements: MeasurementSet, z0: float = 50.0
) -> SWRCandidate:
    """Choose the correct branch with the Smith-chart test."""
    candidates = fit_swr_candidates(measurements, z0=z0)
    branch = select_coupling_from_smith(measurements, z0=z0)
    for candidate in candidates:
        if candidate.label == branch:
            return candidate
    raise ValueError(f"No candidate matched Smith-Chart branch '{branch}'")


def resonator_impedance(
    freqs_hz: np.ndarray,
    rpar_ohm: float,
    q: float,
    fres_hz: float,
    jx_series_ohm: float,
) -> np.ndarray:
    """Return the impedance of a parallel RLC resonator with series reactance."""
    omega = 2 * np.pi * freqs_hz
    omega_0 = 2 * np.pi * fres_hz
    delta = omega / omega_0 - omega_0 / omega
    return 1j * jx_series_ohm + rpar_ohm / (1 + 1j * q * delta)


def fit_parallel_resonator(measurements: MeasurementSet) -> ResonatorFit:
    freqs_hz = np.asarray([freq_hz for freq_hz, _ in measurements], dtype=float)
    measured_impedance = np.asarray(
        [impedance for _, impedance in measurements], dtype=complex
    )
    measured_real = measured_impedance.real
    measured_imag = measured_impedance.imag
    fres_guess_hz = float(np.median(freqs_hz))

    def residuals(params: np.ndarray) -> np.ndarray:
        log_rpar, log_q, log_fres, jx_series = params
        rpar_ohm, q, fres_hz = np.exp([log_rpar, log_q, log_fres])
        modeled_impedance = resonator_impedance(
            freqs_hz=freqs_hz,
            rpar_ohm=rpar_ohm,
            q=q,
            fres_hz=fres_hz,
            jx_series_ohm=jx_series,
        )
        return np.concatenate(
            [
                modeled_impedance.real - measured_real,
                modeled_impedance.imag - measured_imag,
            ]
        )

    best_solution: tuple[float, np.ndarray] | None = None
    for rpar_guess in (50.0, 100.0, 200.0, 500.0):
        for q_guess in (50.0, 100.0, 300.0, 600.0, 1000.0):
            for jx_series_guess in (50.0, 100.0, 150.0):
                start = np.array(
                    [
                        np.log(rpar_guess),
                        np.log(q_guess),
                        np.log(fres_guess_hz),
                        jx_series_guess,
                    ],
                    dtype=float,
                )
                fit = least_squares(residuals, start, max_nfev=5_000)
                modeled_impedance = resonator_impedance(
                    freqs_hz=freqs_hz,
                    rpar_ohm=float(np.exp(fit.x[0])),
                    q=float(np.exp(fit.x[1])),
                    fres_hz=float(np.exp(fit.x[2])),
                    jx_series_ohm=float(fit.x[3]),
                )
                rmse = float(
                    np.sqrt(
                        np.mean(np.abs(modeled_impedance - measured_impedance) ** 2)
                    )
                )
                if best_solution is None or rmse < best_solution[0]:
                    best_solution = (rmse, fit.x.copy())

    assert best_solution is not None
    rmse, best_params = best_solution
    rpar_ohm, q, fres_hz = np.exp(best_params[:3])
    jx_series_ohm = float(best_params[3])
    omega_0 = 2 * np.pi * fres_hz
    l_h = rpar_ohm / (q * omega_0)
    c_f = q / (omega_0 * rpar_ohm)
    bandwidth_hz = fres_hz / q
    return ResonatorFit(
        fres_hz=float(fres_hz),
        l_h=float(l_h),
        c_f=float(c_f),
        rpar_ohm=float(rpar_ohm),
        bandwidth_hz=float(bandwidth_hz),
        jx_series_ohm=jx_series_ohm,
        rmse_ohm=rmse,
    )


def format_resonator_fit(fit: ResonatorFit) -> str:
    return (
        f"fres_hz={fit.fres_hz:.0f} Hz\n"
        # f"L={fit.l_h:.6e} H\n"
        # f"C={fit.c_f:.6e} F\n"
        f"Rpar={fit.rpar_ohm:.2f} Ohm\n"
        f"jXseries={fit.jx_series_ohm:.2f} Ohm\n"
        f"RootMeanSquareError={fit.rmse_ohm:.3f} Ohm\n"
        f"bandwidth_hz={fit.bandwidth_hz:.1f} Hz\n"
    )


def print_resonator_fits(measurement_sets: Sequence[MeasurementSet]) -> None:
    for index, measurements in enumerate(measurement_sets, start=1):
        candidates = fit_swr_candidates(measurements)
        branch = select_coupling_from_smith(measurements)
        chosen = choose_swr_candidate(measurements)
        fit = fit_parallel_resonator(measurements)

        print(f"Set {index}")
        # print("SWR candidates:")
        for candidate in candidates:
            print(
                f"SWR candidate: {candidate.label}: Rpar={candidate.rpar_ohm:.2f} Ohm, "
                # f"Q={candidate.q:.1f}, fres={candidate.fres_hz / 1e6:.6f} MHz, "
                f"BW_hz={candidate.bandwidth_hz:.0f} Hz"
            )
        print(f"Smith-chart coupling decision: {branch}")
        # print(f"Selected branch: {chosen.label}")
        print(
            f"SWR-only estimate: BW_hz={chosen.bandwidth_hz:.0f} Hz "
            f"(phase-free candidate from SWR; no jXseries included)"
        )
        print(
            f"Final fitted model: BW_hz={fit.bandwidth_hz:.0f} Hz "
            f"(includes equivalent series reactance jXseries={fit.jx_series_ohm:.2f} Ohm)"
        )
        print("Final solution:")
        print(format_resonator_fit(fit))
        print()


def print_swr_candidates(measurement_sets: Sequence[MeasurementSet]) -> None:
    for index, measurements in enumerate(measurement_sets, start=1):
        candidates = fit_swr_candidates(measurements)
        print(f"Set {index} SWR candidates")
        for candidate in candidates:
            print(
                f"{candidate.label}: Rpar={candidate.rpar_ohm:.2f} Ohm, "
                f"Q={candidate.q:.1f}, fres={candidate.fres_hz / 1e6:.6f} MHz, "
                f"BW_hz={candidate.bandwidth_hz:.0f} Hz"
            )
        print(f"chosen by Smith chart: {select_coupling_from_smith(measurements)}")
        print()


def test_swr_from_impedance_matches_known_value() -> None:
    z = 50 + 0j
    assert np.isclose(swr_from_impedance(z), 1.0)

    z = 25 + 0j
    assert np.isclose(swr_from_impedance(z), 2.0)


def test_s_q_uses_expected_branch_for_overcoupled_case() -> None:
    q = s_q(32.6, 7.08e6, 7.091e6, 2.0)
    assert q > 0
    assert np.isfinite(q)


def test_fit_swr_candidates_returns_two_candidates() -> None:
    measurements = (
        (7_069_500.0, 154 + 178j),
        (7_080_000.0, 66.0 + 18.9j),
        (7_091_000.0, 14.9 + 47.4j),
    )
    candidates = fit_swr_candidates(measurements)
    assert len(candidates) == 2
    labels = {candidate.label for candidate in candidates}
    assert labels == {"undercoupled", "overcoupled"}


def test_circle_contains_point_works_for_overcoupled_case() -> None:
    center = 1.0 + 0.0j
    radius = 0.8
    point = 1.0 + 0.1j
    assert circle_contains_point(center, radius, point)
