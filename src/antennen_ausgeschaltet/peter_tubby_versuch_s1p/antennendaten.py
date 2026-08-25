"""Structured data for the Peter Märki Tubby outdoor antenna."""

from antennenvergleich.constants import PETER_TUBBY
from antennenvergleich.datatypes import Antenna, FloatText, IntText

ANTENNENDATEN = Antenna(
    name="Peter Tubby s1p",
    call="HB9ISP",
    D_m=PETER_TUBBY.D_m,
    d_m=PETER_TUBBY.d_m,
    n=PETER_TUBBY.n,
    p_m=PETER_TUBBY.p_m,
    info_str=PETER_TUBBY.info_str,
    info_enviroment_str=PETER_TUBBY.info_enviroment_str,
    info_conductor_str=PETER_TUBBY.info_conductor_str,
    info_capacitor_str=PETER_TUBBY.info_capacitor_str,
    bands=[],
)
