"""Structured data for the DK3SS 0.82m n2 loop."""

from antennenvergleich.constants import BANDS, DK3SS
from antennenvergleich.datatypes import Antenna, BandData, FloatText


q_80m = 545  # qrz_com_db_DK3SS.pdf
bw262_Hz_80m = BANDS.f_hz_by_band_name["80m"] / q_80m

q_40m = 293  # qrz_com_db_DK3SS.pdf
bw262_Hz_40m = BANDS.f_hz_by_band_name["40m"] / q_40m

q_30m = 253  # qrz_com_db_DK3SS.pdf
bw262_Hz_30m = BANDS.f_hz_by_band_name["30m"] / q_30m


ANTENNENDATEN = Antenna(
    # name="Selfmade 0.86m n2",
    # call="DK3SS",
    color="#0000dd",  # color from compare_colors.py
    selection_brand="Selfmade",
    selection_location="DK3SS",
    selection_name="0.86m n2",
    overview_pictures=("images/1893.jpeg",),
    D_m=FloatText(0.86, "qrz_com_db_DK3SS.pdf"),
    d_m=DK3SS.d_m,
    n=DK3SS.n,
    p_m=DK3SS.p_m,
    powerP_W=DK3SS.powerP_W,
    info_str=DK3SS.info_str,
    info_thanks_str=DK3SS.info_thanks_str,
    antenna_build_html="../../shared/DK3SS/antenna_build.html",
    enviroment_html="../../shared/DK3SS/enviroment.html",
    measurement_html="../../shared/DK3SS/measurement.html",
    final_remarks_html="../../shared/DK3SS/final_remarks.html",
    info_enviroment_str=DK3SS.info_enviroment_str,
    info_conductor_str=DK3SS.info_conductor_str,
    info_capacitor_str=DK3SS.info_capacitor_str,
    bands=[
        BandData(
            f_Hz=FloatText(
                BANDS.f_hz_by_band_name["80m"], "keine Angabe daher Bandmitte"
            ),
            bw262_Hz=FloatText(
                bw262_Hz_80m, "berechnet aus angegebenem Q qrz_com_db_DK3SS.pdf"
            ),
            swr_min=FloatText(
                1.0,
                "20260808b_email_*.md -30dB Rückflussdaempfung: also gut angepasst",
            ),
        ),
        BandData(
            f_Hz=FloatText(
                BANDS.f_hz_by_band_name["40m"], "keine Angabe daher Bandmitte"
            ),
            bw262_Hz=FloatText(
                bw262_Hz_40m, "berechnet aus angegebenem Q qrz_com_db_DK3SS.pdf"
            ),
            swr_min=FloatText(
                1.0,
                "20260808b_email_*.md -30dB Rückflussdaempfung: also gut angepasst",
            ),
        ),
        BandData(
            f_Hz=FloatText(
                BANDS.f_hz_by_band_name["30m"], "keine Angabe daher Bandmitte"
            ),
            bw262_Hz=FloatText(
                bw262_Hz_30m, "berechnet aus angegebenem Q qrz_com_db_DK3SS.pdf"
            ),
            swr_min=FloatText(
                1.0,
                "20260808b_email_*.md -30dB Rückflussdaempfung: also gut angepasst",
            ),
        ),
    ],
)
