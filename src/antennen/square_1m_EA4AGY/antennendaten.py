import math

from antennenvergleich.datatypes import (
    Antenna,
    BandData,
    FloatText,
    IntText,
)

rectangle_width_m = 1.0
A_m2 = rectangle_width_m * rectangle_width_m
aequivalent_D_m = 2 * math.sqrt(A_m2 / math.pi)

"""Wie genau diese Angaben stimmen ist mir unklar. Ich könnte mir gut vorstellen dass 1m Rohrstücke verwendet wurden und der Loop entsprechend etwas grösser ist."""


ANTENNENDATEN = Antenna(
    # color="#8e7900",  # color from compare_colors.py
    dashed=True,
    selection_brand="Selfmade",
    selection_location="EA4AGY",
    selection_name="square_1m",
    D_m=FloatText(
        aequivalent_D_m,
        "YouTube: square loop 4 ft x 4 ft -> equivalent D = 2*sqrt(A/pi)",
    ),
    d_m=FloatText(0.022, "youtube, OD1.9 Inch"),
    n=IntText(1, ""),
    p_m=FloatText(0.0, ""),
    powerPfwd_W=FloatText(
        100.0, "estimated reference power; not documented in the available sources"
    ),
    info_str="Rectangular loop made from 22 mm copper tubing with a butterfly air-variable capacitor.",
    overview_pictures=("images/20250905_204448_overview.jpg",),
    info_environment_str="Indoor, on wooden table, next to brick wall and window. 11th floor under the roof.",
    info_conductor_str="Copper tube 22 mm, connected with sanitary angle fittings and soft-soldered joints.",
    info_capacitor_str="Air-variable butterfly capacitor 15 pF-240 pF 2kV.",
    info_thanks_str="Many thanks to Carlos for answering all my emails and sending me screenshots of his vna.",
    environment_html="environment.html",
    antenna_build_html="antenna_build.html",
    measurement_html="measurement.html",
    final_remarks_html="final_remarks.html",
    bands=[
        BandData(
            f_Hz=FloatText(14_196000, "EA4AGY_20m_crop.jpg"),
            bw262_Hz=FloatText(285636, "EA4AGY_20m_crop.jpg"),
            swr_min=FloatText(1.25, "EA4AGY_20m_crop.jpg"),
        ),
        BandData(
            f_Hz=FloatText(7150000, "EA4AGY_20m_crop.jpg"),
            bw262_Hz=FloatText(70685, "EA4AGY_20m_crop.jpg"),
            swr_min=FloatText(1.25, "EA4AGY_20m_crop.jpg"),
        ),
    ],
    bandwidth_source_str="SWR estimate",
    bandwidth_source_tooltip_str="Rough estimate from VNA SWR and Smith chart screenshots; cable and calibration are unknown.",
)
