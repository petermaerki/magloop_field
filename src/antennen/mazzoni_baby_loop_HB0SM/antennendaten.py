from antennenvergleich import constants
from antennenvergleich.constants import HB9SM, MAZZONI_BABY
from antennenvergleich.datatypes import Antenna

ANTENNENDATEN = Antenna(
    # name="Mazzoni Baby Loop",
    # call="HB0SM",
    color="#97ff00",  # color from compare_colors.py
    selection_brand="Mazzoni",
    selection_location="HB0SM",
    selection_name="Baby",
    D_m=MAZZONI_BABY.D_m,
    d_m=MAZZONI_BABY.d_m,
    n=MAZZONI_BABY.n,
    p_m=MAZZONI_BABY.p_m,
    powerPfwd_W=MAZZONI_BABY.powerP_W,
    info_str=MAZZONI_BABY.info_str,
    overview_pictures=("images/overview_baby.jpg",),
    inductivity_pictures=("images/20260820_161035446_induktivitaet_baby.jpg",),
    measurement_html="../../shared/HB0SM/measurement.html",
    enviroment_html="../../shared/HB0SM/enviroment.html",
    antenna_build_html="../../shared/HB0SM/antenna_build.html",
    final_remarks_html="../../shared/HB0SM/final_remarks.html",
    info_enviroment_str=HB9SM.info_enviroment_str,
    info_conductor_str=MAZZONI_BABY.info_conductor_str,
    info_capacitor_str=MAZZONI_BABY.info_capacitor_str,
    info_thanks_str=HB9SM.info_thanks_str,
    inductivity_pictures_caption_str=HB9SM.inductivity_pictures_caption_str,
    vna_calibration=HB9SM.vna_calibration,
    bands=[],
)
