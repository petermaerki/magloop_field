"""Structured data for the Ciro Mazzoni MIDI Loop."""

from antennenvergleich.constants import MAZZONI_MIDI
from antennenvergleich.datatypes import Antenna, BandData, FloatText

SOURCES = ["BABY+MIDI-flyer.pdf"]

NOTES = [
    "Die Datenblätter definieren nicht, wie die Bandbreite gemessen wurde (kein Hinweis auf SWR-Schwelle oder -3-dB-Kriterium).",
    "Anfrage zur Messmethode wurde am 2026-08-03 an Mazzoni gestellt.",
]

FOOTNOTES = {
    "1": "Diverse, unsichere Quellen im Internet; nicht im offiziellen Datenblatt angegeben.",
}

ANTENNENDATEN = Antenna(
    # name="Mazzoni Midi Loop",
    # call="Datasheet",
    color="#ff7ed1",  # color from compare_colors.py
    selection_brand="Mazzoni",
    selection_location="Datasheet",
    selection_name="Midi",
    overview_pictures=("images/flyer_overview.jpg",),
    D_m=MAZZONI_MIDI.D_m,
    d_m=MAZZONI_MIDI.d_m,
    n=MAZZONI_MIDI.n,
    p_m=MAZZONI_MIDI.p_m,
    powerP_W=MAZZONI_MIDI.powerP_W,
    info_str=MAZZONI_MIDI.info_str,
    info_enviroment_str=MAZZONI_MIDI.info_enviroment_str,
    info_conductor_str=MAZZONI_MIDI.info_conductor_str,
    info_capacitor_str=MAZZONI_MIDI.info_capacitor_str,
    bands=[
        BandData(
            f_Hz=FloatText(3_500_000, "[MaerkiMD] Frequenz 3.5 MHz"),
            bw262_Hz=FloatText(
                4_000,
                "[MazzFlyer] Flyer, Bandbreite 80m; Messkriterium unbekannt (kein SWR-Hinweis)",
            ),
            swr_min=FloatText(1.18, "[Annahme] Mazzoni: nicht perfekt anpassbar"),
        ),
        BandData(
            f_Hz=FloatText(7_000_000, "[MaerkiMD] Frequenz 7 MHz"),
            bw262_Hz=FloatText(
                6_000,
                "[MazzFlyer] Flyer, Bandbreite 40m; Messkriterium unbekannt (kein SWR-Hinweis)",
            ),
            swr_min=FloatText(1.18, "[Annahme] Mazzoni: nicht perfekt anpassbar"),
        ),
        BandData(
            f_Hz=FloatText(14_000_000, "[MaerkiMD] Frequenz 14 MHz"),
            bw262_Hz=FloatText(
                10_000,
                "[MazzFlyer] Flyer, Bandbreite 20m; Messkriterium unbekannt (kein SWR-Hinweis)",
            ),
            swr_min=FloatText(1.18, "[Annahme] Mazzoni: nicht perfekt anpassbar"),
        ),
    ],
)
