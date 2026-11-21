from antennenvergleich.constants import FESZ
from antennenvergleich.datatypes import (
    Antenna,
    FloatText,
    VnaCalibration,
)

ANTENNENDATEN = Antenna(
    ctl_draft=True,
    # color="#9ae4ff",  # color from compare_colors.py
    selection_brand="Selfmade",
    selection_location=FESZ.selection_location,
    selection_name="fesz_0.95",
    D_m=FloatText(0.95, "EMail Fesz, 2026-11-20, about 0.95."),
    d_m=FloatText(
        0.0081,
        "Unclear, no specification in datasheet. I took the value of LMR400 here.",
    ),
    n=FESZ.n,
    p_m=FESZ.p_m,
    vna_calibration=VnaCalibration.ANTENNA_FEED_POINT,
    vna_device_str=FESZ.vna_device_str,
    vna_cable=FESZ.vna_cable,
    powerPfwd_W=FESZ.powerPfwd_W,
    info_str=FESZ.info_str,
    overview_pictures=("images/large_loop_thumbnail.jpg",),
    info_environment_str=FESZ.info_environment_str,
    info_conductor_str="RG213plus BP200 Messi & Paoloni approx 3 m, 10.3mm outer diameter, PL-259 at the ends. Center not connected.",
    info_capacitor_str=FESZ.info_capacitor_str,
    info_thanks_str=FESZ.info_thanks_str,
    environment_html="../../shared/YO2FZT/environment.html",
    antenna_build_html="../../shared/YO2FZT/antenna_build.html",
    measurement_html="../../shared/YO2FZT/measurement.html",
    # vna_remarks_html="vna_remarks.html",
    final_remarks_html="../../shared/YO2FZT/final_remarks.html",
    bands=[],
    bandwidth_source_str="S-Parameters",
)
