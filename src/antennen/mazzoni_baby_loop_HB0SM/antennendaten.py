from antennenvergleich.constants import MAZZONI_BABY, HB9SM
from antennenvergleich.datatypes import Antenna, FloatText, IntText

ANTENNENDATEN = Antenna(
    # name="Mazzoni Baby Loop",
    # call="HB0SM",
    selection_brand="Mazzoni",
    selection_location="HB0SM",
    selection_name="Baby",
    D_m=MAZZONI_BABY.D_m,
    d_m=MAZZONI_BABY.d_m,
    n=MAZZONI_BABY.n,
    p_m=MAZZONI_BABY.p_m,
    powerP_W=MAZZONI_BABY.powerP_W,
    info_str=MAZZONI_BABY.info_str,
    overview_pictures=("images/overview_baby.jpg",),
    inductivity_pictures=("images/20260820_161035446_induktivitaet_baby.jpg",),
    enviroment_html=("../../shared/HB0SM/enviroment.html",),
    info_enviroment_str=HB9SM.info_enviroment_str,
    info_conductor_str=MAZZONI_BABY.info_conductor_str,
    info_capacitor_str=MAZZONI_BABY.info_capacitor_str,
    info_thanks_str=HB9SM.info_thanks_str,
    vna_calibration=HB9SM.vna_calibration,
    bands=[],
)
