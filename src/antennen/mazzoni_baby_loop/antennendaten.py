"""Structured data for the Ciro Mazzoni Baby Loop."""

from antennenvergleich.constants import MAZZONI_BABY
from antennenvergleich.datatypes import Antenna, BandData, FloatText

SOURCES = [
    "MAZZONI_Baby-Loop_Datenblatt.pdf",
    "BABY+MIDI-flyer.pdf",
]

NOTES = [
    "Die Datenblätter definieren nicht, wie die Bandbreite gemessen wurde (kein Hinweis auf SWR-Schwelle oder -3-dB-Kriterium).",
    "Anfrage zur Messmethode wurde am 2026-08-03 an Mazzoni gestellt.",
]

ANTENNENDATEN = Antenna(
    #name="Mazzoni Baby Loop",
    #call="Datasheet",
    selection_brand="Mazzoni",
    selection_location="Datasheet",
    selection_name="Baby",
    overview_pictures=("images/flyer_overview.jpg",),
    D_m=MAZZONI_BABY.D_m,
    d_m=MAZZONI_BABY.d_m,
    n=MAZZONI_BABY.n,
    p_m=MAZZONI_BABY.p_m,
    info_str=MAZZONI_BABY.info_str,
    info_enviroment_str=MAZZONI_BABY.info_enviroment_str,
    info_conductor_str=MAZZONI_BABY.info_conductor_str,
    info_capacitor_str=MAZZONI_BABY.info_capacitor_str,
    bands=[
        BandData(f_Hz=FloatText(7_000_000, ""), bw262_Hz=FloatText(4_000, "[MazzBaby] Datenblatt, Bandbreite 40m; Messkriterium unbekannt (kein SWR-Hinweis)"), swr_min=FloatText(1.18, "[Annahme] Mazzoni: nicht perfekt anpassbar")),
        BandData(f_Hz=FloatText(14_000_000, ""), bw262_Hz=FloatText(6_000, "[MazzBaby] Datenblatt, Bandbreite 20m; Messkriterium unbekannt (kein SWR-Hinweis)"), swr_min=FloatText(1.18, "[Annahme] Mazzoni: nicht perfekt anpassbar")),
        BandData(f_Hz=FloatText(21_000_000, ""), bw262_Hz=FloatText(12_000, "[MazzBaby] Datenblatt, Bandbreite 15m; Messkriterium unbekannt (kein SWR-Hinweis)"), swr_min=FloatText(1.18, "[Annahme] Mazzoni: nicht perfekt anpassbar")),
        BandData(f_Hz=FloatText(28_000_000, ""), bw262_Hz=FloatText(20_000, "[MazzBaby] Datenblatt, Bandbreite 10m; Messkriterium unbekannt (kein SWR-Hinweis)"), swr_min=FloatText(1.18, "[Annahme] Mazzoni: nicht perfekt anpassbar")),
    ],
)
