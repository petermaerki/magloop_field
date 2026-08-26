"""Structured data for the Ciro Mazzoni Stealth Loop."""

from antennenvergleich.constants import MAZZONI_STEALTH
from antennenvergleich.datatypes import Antenna, BandData, FloatText, IntText


SOURCES = []

NOTES = []

FOOTNOTES = {}

ANTENNENDATEN = Antenna(
    selection_brand="Mazzoni",
    selection_location="HE9DJB",
    selection_name="Stealth",
    D_m=MAZZONI_STEALTH.D_m,
    d_m=MAZZONI_STEALTH.d_m,
    n=MAZZONI_STEALTH.n,
    p_m=MAZZONI_STEALTH.p_m,
    powerP_W=MAZZONI_STEALTH.powerP_W,
    info_str=MAZZONI_STEALTH.info_str,
    overview_pictures=("images/stealth_antenne_2021_02.jpg",),
    info_enviroment_str="In the garden on the ground on patio slabs.",
    info_conductor_str=MAZZONI_STEALTH.info_conductor_str,
    info_capacitor_str=MAZZONI_STEALTH.info_capacitor_str,
    bands=[],
)
