"""Reusable H-field analysis helpers for antenna scripts and compare runs."""

from __future__ import annotations

from dataclasses import dataclass

from antennenvergleich.datatypes import Antenna, BandData
from antennenvergleich.h_field_meter import h_field_from_p_dbm
from magloop_field.calculations import AntennaCalculator, Calculator


@dataclass(frozen=True)
class FeedlineSegment:
    name: str
    length_m: float
    points: tuple[tuple[float, float], tuple[float, float]]
    unit: str  # "db_per_100m" | "db_per_100ft"
    delay_ns_m: float | None = None


def interpolate_db_at_f_sqrt(
    points: tuple[tuple[float, float], tuple[float, float]],
    f_hz: float,
) -> float:
    """Interpolate attenuation between two reference points linearly in sqrt(f)."""
    (f0_hz, att0), (f1_hz, att1) = points
    sqrt_f = f_hz**0.5
    sqrt_f0 = f0_hz**0.5
    sqrt_f1 = f1_hz**0.5
    return att0 + (att1 - att0) * ((sqrt_f - sqrt_f0) / (sqrt_f1 - sqrt_f0))


def db_per_m_from_points(
    points: tuple[tuple[float, float], tuple[float, float]],
    unit: str,
    f_hz: float,
) -> float:
    att = interpolate_db_at_f_sqrt(points=points, f_hz=f_hz)
    if unit == "db_per_100m":
        return att / 100.0
    if unit == "db_per_100ft":
        return att / 30.48
    raise ValueError(f"Unsupported attenuation unit: {unit}")


def calculate_feedline_losses(
    f_hz: float,
    cables: list[FeedlineSegment],
    connectors_count: int,
    connector_loss_db: float,
) -> tuple[dict[str, float], float]:
    losses_db: dict[str, float] = {}
    total_loss_db = 0.0

    for cable in cables:
        db_per_m = db_per_m_from_points(
            points=cable.points,
            unit=cable.unit,
            f_hz=f_hz,
        )
        loss_db = db_per_m * cable.length_m
        losses_db[cable.name] = loss_db
        total_loss_db += loss_db

    losses_db["connectors"] = connectors_count * connector_loss_db
    total_loss_db += losses_db["connectors"]

    return losses_db, total_loss_db


def power_after_loss_db(tx_power_w: float, total_loss_db: float) -> float:
    return tx_power_w * 10 ** (-total_loss_db / 10.0)


def select_closest_band(antenna: Antenna, f_hz: float) -> BandData:
    if not antenna.bands:
        raise ValueError("No band data found")
    return min(antenna.bands, key=lambda b: abs(b.f_Hz.value - f_hz))


def expected_h_field_at_point(
    antenna_D_m: float,
    antenna_d_m: float,
    antenna_n: int,
    antenna_p_m: float,
    swr_min: float,
    bw262_hz: float,
    f_hz: float,
    power_into_antenna_w: float,
    x_m: float,
    y_m: float,
    z_m: float,
) -> float:
    ac = AntennaCalculator(
        D_m=antenna_D_m,
        d_m=antenna_d_m,
        n=antenna_n,
        p_m=antenna_p_m,
        swr_min=swr_min,
        f_Hz=f_hz,
        bw262_Hz=bw262_hz,
        powerPfwd_W=power_into_antenna_w,
    )

    field_calc = Calculator(
        antenna_D_m=antenna_D_m,
        R_m=antenna_D_m / 2.0,
        m_Am2=ac.m_Am2,
        f_Hz=f_hz,
    )

    return float(
        field_calc.h_field_abs_xyz(
            x_m=x_m,
            y_m=y_m,
            z_m=z_m,
            m_Am2=ac.m_Am2,
            antenna_D_m=antenna_D_m,
            f_Hz=f_hz,
        )
    )


def measured_h_field_and_factor(
    p_dbm: float,
    f_hz: float,
    expected_h_field_a_m: float,
) -> tuple[float, float]:
    measured_h_field_a_m = h_field_from_p_dbm(p_dbm=p_dbm, f_hz=f_hz)
    factor = measured_h_field_a_m / expected_h_field_a_m
    return measured_h_field_a_m, factor
