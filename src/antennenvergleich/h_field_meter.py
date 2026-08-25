"""Convert powermeter dBm readings to magnetic field strength H (A/m).

Formulas are based on HBradio article 00_h-field_meter.typ.
"""

from __future__ import annotations

import math

MU0_H_PER_M = 4.0 * math.pi * 1e-7
DEFAULT_LOOP_D_M = 0.104
DEFAULT_CONDUCTOR_D_M = 0.00098
DEFAULT_METER_R_OHM = 50.0


def loop_area_m2(loop_d_m: float = DEFAULT_LOOP_D_M) -> float:
    if loop_d_m <= 0:
        raise ValueError("loop_d_m must be > 0")
    return math.pi * (loop_d_m / 2.0) ** 2


def loop_inductance_h(
    loop_d_m: float = DEFAULT_LOOP_D_M,
    conductor_d_m: float = DEFAULT_CONDUCTOR_D_M,
) -> float:
    """Approximate inductance for a single circular loop."""
    if loop_d_m <= 0:
        raise ValueError("loop_d_m must be > 0")
    if conductor_d_m <= 0:
        raise ValueError("conductor_d_m must be > 0")
    return MU0_H_PER_M * (loop_d_m / 2.0) * (math.log((8.0 * loop_d_m) / conductor_d_m) - 2.0)


def meter_voltage_rms_from_dbm(
    p_dbm: float,
    meter_r_ohm: float = DEFAULT_METER_R_OHM,
) -> float:
    """Convert powermeter reading in dBm to RMS voltage at meter input."""
    if meter_r_ohm <= 0:
        raise ValueError("meter_r_ohm must be > 0")
    return math.sqrt(meter_r_ohm * 1e-3 * 10.0 ** (p_dbm / 10.0))


def h_field_from_meter_voltage(
    u_meter_rms_v: float,
    f_hz: float,
    loop_d_m: float = DEFAULT_LOOP_D_M,
    conductor_d_m: float = DEFAULT_CONDUCTOR_D_M,
    meter_r_ohm: float = DEFAULT_METER_R_OHM,
) -> float:
    """Calculate H field in A/m from meter input RMS voltage."""
    if f_hz <= 0:
        raise ValueError("f_hz must be > 0")
    if meter_r_ohm <= 0:
        raise ValueError("meter_r_ohm must be > 0")

    area_m2 = loop_area_m2(loop_d_m)
    inductance_h = loop_inductance_h(loop_d_m=loop_d_m, conductor_d_m=conductor_d_m)

    divider_correction = math.sqrt(1.0 + ((2.0 * math.pi * f_hz * inductance_h) / meter_r_ohm) ** 2)
    return (
        u_meter_rms_v
        / (2.0 * math.pi * f_hz * MU0_H_PER_M * area_m2)
        * divider_correction
    )


def h_field_from_p_dbm(
    p_dbm: float,
    f_hz: float,
    loop_d_m: float = DEFAULT_LOOP_D_M,
    conductor_d_m: float = DEFAULT_CONDUCTOR_D_M,
    meter_r_ohm: float = DEFAULT_METER_R_OHM,
) -> float:
    """Calculate H field in A/m directly from powermeter dBm reading."""
    u_meter_rms_v = meter_voltage_rms_from_dbm(p_dbm=p_dbm, meter_r_ohm=meter_r_ohm)
    return h_field_from_meter_voltage(
        u_meter_rms_v=u_meter_rms_v,
        f_hz=f_hz,
        loop_d_m=loop_d_m,
        conductor_d_m=conductor_d_m,
        meter_r_ohm=meter_r_ohm,
    )
