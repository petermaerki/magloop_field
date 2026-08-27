import math

from antennenvergleich.datatypes import Antenna, BandData, FloatText, IntText


ANTENNENDATEN = Antenna(
    color="#5900a3",  # color from compare_colors.py
    selection_brand="Selfmade",
    selection_location="HB9BPO-draft",
    selection_name="Butterfly",
    D_m=FloatText(
        1.0,
        "todo korrekt",
    ),
    d_m=FloatText(0.01, "todo korrekt"),
    n=IntText(1, ""),
    p_m=FloatText(0.0, ""),
    powerP_W=FloatText(
        10.0, "todo korrekt"
    ),
    info_str="todo.",
    overview_pictures=(),
    info_enviroment_str="Todo.",
    info_conductor_str="Todo.",
    info_capacitor_str="Todo.",
    info_thanks_str="Many thanks to HB9BPO for the support.",
    measurement_html=(),
    bands=[],
)
