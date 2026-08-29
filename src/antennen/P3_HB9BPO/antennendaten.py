
from antennenvergleich.datatypes import (
    Antenna,
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
    selection_name="3P",
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
    inductivity_pictures=("images/20260827_115219934_cap_switch.jpg",),
    inductivity_pictures_caption_str= "The switched capacitor is visible in the picture above.<br>" \
    " The connections were temporarily taped to the main loop with yellow tape.<br>" \
    "With two switches (only one is visible in the picture because they are exactly behind each other), the two capacitors can be switched in.",
    info_enviroment_str=f"In the garden, on a Styrofoam box on a wooden table. Center loop {_hoehe_ueber_boden_zentrum_m:0.2f} m above ground.",
    info_conductor_str="Copper tube OD 12 mm, ID 10 mm, bare surface.",
    info_capacitor_str="Air variable capacitor, self-made, CNC-milled from aluminum sheet.",
    info_thanks_str="Many thanks to Peter HB9BPO for the support, the fun conversations, and the catering.",
    enviroment_html="enviroment.html",
    antenna_build_html="antenna_build.html",
    measurement_html="measurement.html",
    final_remarks_html="final_remarks.html",
    template_vars_dict={
        "hoehe_zentrum_ueber_boden_m": f"{_hoehe_ueber_boden_zentrum_m:0.2f}",
        "h_field_tx_info": "IC-7300 MK2",
    },
    bands=[],
)
