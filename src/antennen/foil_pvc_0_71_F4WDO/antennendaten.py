from math import pi, sqrt

from antennenvergleich.datatypes import (
    Antenna,
    FloatText,
    IntText,
    VnaCalibration,
)

"""Achteck"""

_AREA_FREECAD_M2 = 0.41761

ANTENNENDATEN = Antenna(
    color="#9ae4ff",  # color from compare_colors.py
    selection_brand="Selfmade",
    selection_location="F4WDO",
    selection_name="foil_pvc_0_71",
    D_m=FloatText(
        2 * sqrt(_AREA_FREECAD_M2 / pi),
        f"äquiv. Diameter = 2*sqrt(A/pi) mit A = {_AREA_FREECAD_M2:0.4f} m^2 from drawing Freecad.",
    ),
    d_m=FloatText(0.0452, "Scetch: Tube Diameter 45 mm."),
    n=IntText(1, ""),
    p_m=FloatText(0.0, ""),
    vna_calibration=VnaCalibration.AT_VNA,
    vna_device_str="'original small NanoVNA'",
    powerP_W=FloatText(100.0, "Email: 80. Peter: 100 should work."),
    info_str="Mag loop made of copper foil glued to PVC pipe, with an air-variable capacitor.",
    overview_pictures=("images/loopzoom_f4wdo_loop_2a.jpg",),
    info_enviroment_str="In the attic, in a wooden structure with brick walls, 1.86 m above floor.",
    info_conductor_str="Copper foil  0.1 mm glued to a 45 mm PVC pipe. Joints were soldered with soft solder.",
    info_capacitor_str="Air-variable capacitor, 4 mm spacing, 10-175 pF, unknown type or brand.",
    info_thanks_str="Many thanks to Richard F4WDO for the measurements, drawings, and emails.",
    enviroment_html="enviroment.html",
    antenna_build_html="antenna_build.html",
    measurement_html="measurement.html",
    vna_remarks_html="vna_remarks.html",
    final_remarks_html="final_remarks.html",
    bands=[],
)
