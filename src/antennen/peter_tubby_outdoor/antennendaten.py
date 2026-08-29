"""Structured data for the Peter Märki Tubby outdoor antenna."""

from antennenvergleich.constants import PETER_TUBBY
from antennenvergleich.datatypes import Antenna, BandData, FloatText, IntText

ANTENNENDATEN = Antenna(
    # name="Selfmade Tubby Outdoor",
    # call="HB9ISP",
    color="#d60000",  # color from compare_colors.py
    selection_brand="Selfmade",
    selection_location="HB9ISP",
    selection_name="Tubby outdoor",
    D_m=PETER_TUBBY.D_m,
    d_m=PETER_TUBBY.d_m,
    n=PETER_TUBBY.n,
    p_m=PETER_TUBBY.p_m,
    powerP_W=PETER_TUBBY.powerP_W,
    info_str=PETER_TUBBY.info_str,
    overview_pictures=("images/tubby_outdoor.png",),
    enviroment_html="enviroment.html",
    info_enviroment_str="Suspended 5 m above ground next to the house.",
    info_conductor_str=PETER_TUBBY.info_conductor_str,
    info_capacitor_str=PETER_TUBBY.info_capacitor_str,
    bands=[
        BandData(
            f_Hz=FloatText(3_573_000, "[MaerkiTabelle] Spalte f"),
            bw262_Hz=FloatText(
                2_200, "[MaerkiTabelle] outdoor BW @ SWR 2.62 @ Antenneneingang"
            ),
            swr_min=FloatText(1.0, "[Annahme] Tubby: auf SWR 1.0 abgeglichen"),
        ),
        BandData(
            f_Hz=FloatText(5_357_000, "[MaerkiTabelle] Spalte f"),
            bw262_Hz=FloatText(
                5_200, "[MaerkiTabelle] outdoor BW @ SWR 2.62 @ Antenneneingang"
            ),
            swr_min=FloatText(1.0, "[Annahme] Tubby: auf SWR 1.0 abgeglichen"),
        ),
        BandData(
            f_Hz=FloatText(7_074_000, "[MaerkiTabelle] Spalte f"),
            bw262_Hz=FloatText(
                6_300, "[MaerkiTabelle] outdoor BW @ SWR 2.62 @ Antenneneingang"
            ),
            swr_min=FloatText(1.0, "[Annahme] Tubby: auf SWR 1.0 abgeglichen"),
        ),
        BandData(
            f_Hz=FloatText(10_136_000, "[MaerkiTabelle] Spalte f"),
            bw262_Hz=FloatText(
                8_700, "[MaerkiTabelle] outdoor BW @ SWR 2.62 @ Antenneneingang"
            ),
            swr_min=FloatText(1.0, "[Annahme] Tubby: auf SWR 1.0 abgeglichen"),
        ),
        BandData(
            f_Hz=FloatText(14_074_000, "[MaerkiTabelle] Spalte f"),
            bw262_Hz=FloatText(
                11_100, "[MaerkiTabelle] outdoor BW @ SWR 2.62 @ Antenneneingang"
            ),
            swr_min=FloatText(1.0, "[Annahme] Tubby: auf SWR 1.0 abgeglichen"),
        ),
        BandData(
            f_Hz=FloatText(21_074_000, "[MaerkiTabelle] Spalte f"),
            bw262_Hz=FloatText(
                59_000, "[MaerkiTabelle] outdoor BW @ SWR 2.62 @ Antenneneingang"
            ),
            swr_min=FloatText(1.0, "[Annahme] Tubby: auf SWR 1.0 abgeglichen"),
        ),
        BandData(
            f_Hz=FloatText(24_915_000, "[MaerkiTabelle] Spalte f"),
            bw262_Hz=FloatText(
                179_000, "[MaerkiTabelle] outdoor BW @ SWR 2.62 @ Antenneneingang"
            ),
            swr_min=FloatText(1.0, "[Annahme] Tubby: auf SWR 1.0 abgeglichen"),
        ),
        BandData(
            f_Hz=FloatText(28_074_000, "[MaerkiTabelle] Spalte f"),
            bw262_Hz=FloatText(
                310_000, "[MaerkiTabelle] outdoor BW @ SWR 2.62 @ Antenneneingang"
            ),
            swr_min=FloatText(1.0, "[Annahme] Tubby: auf SWR 1.0 abgeglichen"),
        ),
    ],
)
