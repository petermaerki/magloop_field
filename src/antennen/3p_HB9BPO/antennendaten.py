import math

from antennenvergleich.datatypes import (
    Antenna,
    BandData,
    FloatText,
    IntText,
    VnaCalibration,
)

# 3 mal gemessen, Mittelwert
_D1_m = 0.775
_D2_m = 0.77
_D3_m = 0.74
_D_m = (_D1_m + _D2_m + _D3_m) / 3.0

_hoehe_ueber_boden_tisch_m = 0.74
_hoehe_ueber_boden_kiste_m = 0.25
_hoehe_ueber_boden_acrylplatte_m = 0.03
_hoehe_ueber_boden_zentrum_m = (
    _hoehe_ueber_boden_tisch_m
    + _hoehe_ueber_boden_kiste_m
    + _hoehe_ueber_boden_acrylplatte_m
    + _D_m / 2.0
)

ANTENNENDATEN = Antenna(
    color="#5900a3",  # color from compare_colors.py
    selection_brand="Selfmade",
    selection_location="HB9BPO",
    selection_name="3p",
    D_m=FloatText(
        _D_m,
        "Peter: Measurement Doppelmeter",
    ),
    d_m=FloatText(0.012, "Peter_Measurement with caliper."),
    n=IntText(1, ""),
    p_m=FloatText(0.0, ""),
    vna_calibration=VnaCalibration.ANTENNA_FEED_POINT,
    powerP_W=FloatText(10.0, "HB9BPO: at higher power, the capacitor breaks down."),
    info_str="Mag loop made of copper tubing with an air variable capacitor.",
    overview_pictures=("images/20260827_113113142_overview.jpg",),
    info_enviroment_str=f"In the garden, on a Styrofoam box on a wooden table. Center loop {_hoehe_ueber_boden_zentrum_m:0.2f} m above ground.",
    info_conductor_str="Copper tube OD 12 mm, ID 10 mm, bare surface.",
    info_capacitor_str="Air variable capacitor, self-made, CNC-milled from aluminum sheet.",
    info_thanks_str="Many thanks to HB9BPO for the support, the fun conversations, and the catering.",
    measurement_html=("measurement.html",),
    bands=[],
)


print(ANTENNENDATEN)
