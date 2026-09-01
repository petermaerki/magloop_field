"""Structured data for the Ciro Mazzoni Stealth Loop."""

from antennenvergleich.constants import MAZZONI_STEALTH
from antennenvergleich.datatypes import Antenna, BandData, FloatText

SOURCES = ["mzz-stealth-a_ed.pdf"]

NOTES = [
    "Die Datenblätter definieren nicht, wie die Bandbreite gemessen wurde (kein Hinweis auf SWR-Schwelle oder -3-dB-Kriterium).",
    "Anfrage zur Messmethode wurde am 2026-08-03 an Mazzoni gestellt.",
]

FOOTNOTES = {
    "1": "Peter Märki, FreeCAD-Messung der eingeschlossenen Leiterfläche aus der Geometrie der Stealth Loop.",
}

ANTENNENDATEN = Antenna(
    # name="Mazzoni Stealth Loop",
    # call="Datasheet",
    color="#005659",  # color from compare_colors.py
    selection_brand="Mazzoni",
    selection_location="Datasheet",
    selection_name="Stealth",
    D_m=MAZZONI_STEALTH.D_m,
    d_m=MAZZONI_STEALTH.d_m,
    n=MAZZONI_STEALTH.n,
    p_m=MAZZONI_STEALTH.p_m,
    powerPfwd_W=MAZZONI_STEALTH.powerP_W,
    info_str=MAZZONI_STEALTH.info_str,
    overview_pictures=("images/overview_stealth.jpg",),
    measurement_html="../../shared/mazzoni/measurement.html",
    final_remarks_html="../../shared/mazzoni/final_remarks.html",
    info_enviroment_str=MAZZONI_STEALTH.info_enviroment_str,
    info_conductor_str=MAZZONI_STEALTH.info_conductor_str,
    info_capacitor_str=MAZZONI_STEALTH.info_capacitor_str,
    bands=[
        BandData(
            f_Hz=FloatText(7_000_000, ""),
            bw262_Hz=FloatText(5_000, ""),
            swr_min=FloatText(1.18, ""),
        ),
        BandData(
            f_Hz=FloatText(14_000_000, ""),
            bw262_Hz=FloatText(8_000, ""),
            swr_min=FloatText(1.18, ""),
        ),
        BandData(
            f_Hz=FloatText(21_000_000, ""),
            bw262_Hz=FloatText(15_000, ""),
            swr_min=FloatText(1.18, ""),
        ),
        BandData(
            f_Hz=FloatText(28_000_000, ""),
            bw262_Hz=FloatText(25_000, ""),
            swr_min=FloatText(1.18, ""),
        ),
    ],
)
