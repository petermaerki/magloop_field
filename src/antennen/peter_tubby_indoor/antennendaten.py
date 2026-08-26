"""Structured data for the Peter Märki Tubby indoor antenna."""

from antennenvergleich.constants import PETER_TUBBY
from antennenvergleich.datatypes import Antenna, BandData, FloatText, IntText

ANTENNENDATEN = Antenna(
    # name="Selfmade Tubby Indoor",
    # call="HB9ISP",
    color="#ffa52f",  # color from compare_colors.py
    selection_brand="Selfmade",
    selection_location="HB9ISP",
    selection_name="Tubby indoor",
    D_m=PETER_TUBBY.D_m,
    d_m=PETER_TUBBY.d_m,
    n=PETER_TUBBY.n,
    p_m=PETER_TUBBY.p_m,
    powerP_W=PETER_TUBBY.powerP_W,
    info_str=PETER_TUBBY.info_str,
    overview_pictures=("images/tubby_indoor.png",),
    enviroment_html=("enviroment.html",),
    info_enviroment_str=PETER_TUBBY.info_enviroment_str,
    info_conductor_str=PETER_TUBBY.info_conductor_str,
    info_capacitor_str=PETER_TUBBY.info_capacitor_str,
    bands=[
        BandData(
            f_Hz=FloatText(1_840_000, "[MaerkiTabelle] Spalte f"),
            bw262_Hz=FloatText(
                3_700, "[MaerkiTabelle] indoor BW @ SWR 2.62 @ Antenneneingang"
            ),
            swr_min=FloatText(1.0, "[Annahme] Tubby: auf SWR 1.0 abgeglichen"),
        ),
        BandData(
            f_Hz=FloatText(3_573_000, "[MaerkiTabelle] Spalte f"),
            bw262_Hz=FloatText(
                5_200, "[MaerkiTabelle] indoor BW @ SWR 2.62 @ Antenneneingang"
            ),
            swr_min=FloatText(1.0, "[Annahme] Tubby: auf SWR 1.0 abgeglichen"),
        ),
        BandData(
            f_Hz=FloatText(5_357_000, "[MaerkiTabelle] Spalte f"),
            bw262_Hz=FloatText(
                10_900, "[MaerkiTabelle] indoor BW @ SWR 2.62 @ Antenneneingang"
            ),
            swr_min=FloatText(1.0, "[Annahme] Tubby: auf SWR 1.0 abgeglichen"),
        ),
        BandData(
            f_Hz=FloatText(7_074_000, "[MaerkiTabelle] Spalte f"),
            bw262_Hz=FloatText(
                15_000, "[MaerkiTabelle] indoor BW @ SWR 2.62 @ Antenneneingang"
            ),
            swr_min=FloatText(1.0, "[Annahme] Tubby: auf SWR 1.0 abgeglichen"),
        ),
        BandData(
            f_Hz=FloatText(10_136_000, "[MaerkiTabelle] Spalte f"),
            bw262_Hz=FloatText(
                34_000, "[MaerkiTabelle] indoor BW @ SWR 2.62 @ Antenneneingang"
            ),
            swr_min=FloatText(1.0, "[Annahme] Tubby: auf SWR 1.0 abgeglichen"),
        ),
        BandData(
            f_Hz=FloatText(14_074_000, "[MaerkiTabelle] Spalte f"),
            bw262_Hz=FloatText(
                72_000, "[MaerkiTabelle] indoor BW @ SWR 2.62 @ Antenneneingang"
            ),
            swr_min=FloatText(1.0, "[Annahme] Tubby: auf SWR 1.0 abgeglichen"),
        ),
        BandData(
            f_Hz=FloatText(21_074_000, "[MaerkiTabelle] Spalte f"),
            bw262_Hz=FloatText(
                175_000, "[MaerkiTabelle] indoor BW @ SWR 2.62 @ Antenneneingang"
            ),
            swr_min=FloatText(1.0, "[Annahme] Tubby: auf SWR 1.0 abgeglichen"),
        ),
        BandData(
            f_Hz=FloatText(24_915_000, "[MaerkiTabelle] Spalte f"),
            bw262_Hz=FloatText(
                272_000, "[MaerkiTabelle] indoor BW @ SWR 2.62 @ Antenneneingang"
            ),
            swr_min=FloatText(1.0, "[Annahme] Tubby: auf SWR 1.0 abgeglichen"),
        ),
        BandData(
            f_Hz=FloatText(28_074_000, "[MaerkiTabelle] Spalte f"),
            bw262_Hz=FloatText(
                452_000, "[MaerkiTabelle] indoor BW @ SWR 2.62 @ Antenneneingang"
            ),
            swr_min=FloatText(1.0, "[Annahme] Tubby: auf SWR 1.0 abgeglichen"),
        ),
    ],
)
