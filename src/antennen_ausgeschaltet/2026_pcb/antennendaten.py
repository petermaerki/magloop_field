"""Structured data for the Peter Märki Tubby indoor antenna."""

from antennenvergleich import constants
from antennenvergleich.datatypes import Antenna, BandData, FloatText, VnaCalibration


ANTENNENDATEN = Antenna(
    # name="Selfmade Tubby Indoor",
    # call="HB9ISP",
    # color="#ffa52f",  # color from compare_colors.py
    dashed=False,
    selection_brand="Selfmade",
    selection_location="HB9ISP",
    selection_name="2026_pcb",
    vna_calibration=VnaCalibration.ANTENNA_FEED_POINT,
    vna_device_str=constants.VNA_PETER_INFO,
    D_m=constants.PETER_2026_PCB.D_m,
    d_m=constants.PETER_2026_PCB.d_m,
    n=constants.PETER_2026_PCB.n,
    p_m=constants.PETER_2026_PCB.p_m,
    powerPfwd_W=constants.PETER_2026_PCB.powerPfwd_W,
    info_str=constants.PETER_2026_PCB.info_str,
    overview_pictures=("images/20261002_060731061.jpg",),
    environment_html="environment.html",
    info_environment_str="todo",
    info_conductor_str=constants.PETER_2026_PCB.info_conductor_str,
    info_capacitor_str=constants.PETER_2026_PCB.info_capacitor_str,
    bands=[],
    bandwidth_source_str="S-Parameters",
)
