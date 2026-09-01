from antennenvergleich import constants
from antennenvergleich.constants import HB9SM, MAZZONI_MIDI
from antennenvergleich.datatypes import Antenna

ANTENNENDATEN = Antenna(
    # name="Mazzoni Midi Loop",
    # call="HB0SM",
    color="#6b004f",  # color from compare_colors.py
    selection_brand="Mazzoni",
    selection_location="HB0SM",
    selection_name="Midi",
    D_m=MAZZONI_MIDI.D_m,
    d_m=MAZZONI_MIDI.d_m,
    n=MAZZONI_MIDI.n,
    p_m=MAZZONI_MIDI.p_m,
    powerPfwd_W=MAZZONI_MIDI.powerPfwd_W,
    info_str=MAZZONI_MIDI.info_str,
    vna_device_str=constants.VNA_PETER_INFO,
    overview_pictures=("images/overview_midi.jpg",),
    inductivity_pictures=("images/20260820_164701101_2_induktivitaet_midi.jpg",),
    measurement_html="../../shared/HB0SM/measurement.html",
    enviroment_html="../../shared/HB0SM/enviroment.html",
    antenna_build_html="../../shared/HB0SM/antenna_build.html",
    final_remarks_html="../../shared/HB0SM/final_remarks.html",
    info_enviroment_str=HB9SM.info_enviroment_str,
    info_conductor_str=MAZZONI_MIDI.info_conductor_str,
    info_capacitor_str=MAZZONI_MIDI.info_capacitor_str,
    info_thanks_str=HB9SM.info_thanks_str,
    inductivity_pictures_caption_str=HB9SM.inductivity_pictures_caption_str,
    vna_calibration=HB9SM.vna_calibration,
    bands=[],
)
