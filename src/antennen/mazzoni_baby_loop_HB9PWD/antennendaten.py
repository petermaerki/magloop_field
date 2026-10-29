from antennenvergleich import constants
from antennenvergleich.constants import HB9SM, MAZZONI_BABY
from antennenvergleich.datatypes import Antenna, VnaCalibration, FloatText

ANTENNENDATEN = Antenna(
    # name="Mazzoni Baby Loop",
    # call="HB0SM",
    # color="#97ff00",  # color from compare_colors.py
    selection_brand="Mazzoni",
    selection_location="HB9PWD",
    selection_name="Baby",
    D_m=MAZZONI_BABY.D_m,
    d_m=MAZZONI_BABY.d_m,
    n=MAZZONI_BABY.n,
    p_m=MAZZONI_BABY.p_m,
    powerPfwd_W=FloatText(450.0, ""),
    info_str=MAZZONI_BABY.info_str,
    vna_device_str=constants.VNA_PETER_INFO,
    overview_pictures=("images/overview.jpeg",),
    # inductivity_pictures=("images/20260820_161035446_induktivitaet_baby.jpg",),
    # measurement_html="../../shared/HB0SM/measurement.html",
    # environment_html="../../shared/HB0SM/environment.html",
    environment_html="environment.html",
    # antenna_build_html="../../shared/HB0SM/antenna_build.html",
    # final_remarks_html="../../shared/HB0SM/final_remarks.html",
    final_remarks_html="final_remarks.html",
    info_environment_str="Mounted on a mast with a rotor 1.5m above the roof of a 5-storey building",
    info_conductor_str=MAZZONI_BABY.info_conductor_str,
    info_capacitor_str=MAZZONI_BABY.info_capacitor_str,
    measurement_html="measurement.html",
    info_thanks_str="Many thanks to Stephan for allowing me to measure his antenna, for the pleasant conversations, and for showing me his workshop and shack.",
    # inductivity_pictures_caption_str=HB9SM.inductivity_pictures_caption_str,
    vna_calibration=VnaCalibration.AT_VNA,
    bands=[],
    bandwidth_source_str="S-Parameters",
)
