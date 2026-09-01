"""Structured data for the DK3SS 1.25m n2 loop."""

from antennenvergleich.constants import BANDS, DK3SS
from antennenvergleich.datatypes import Antenna, BandData, FloatText

q_160m = 305  # qrz_com_db_DK3SS.pdf
bw262_Hz_160m = BANDS.f_hz_by_band_name["30m"] / q_160m

q_80m = 277  # qrz_com_db_DK3SS.pdf
bw262_Hz_80m = BANDS.f_hz_by_band_name["80m"] / q_80m

q_40m = 213  # qrz_com_db_DK3SS.pdf
bw262_Hz_40m = BANDS.f_hz_by_band_name["40m"] / q_40m


_info_website = """
mag160-antenne_DK3SS.pdf
160m: 500 pf plus 150 pF 
80m: 150 pF 
40m 27 pf 

EMail, Induktivität "ich habe sie mit der Thomsonschen Formel 
aus der Resonanzfrequenz und der bekannten Festkapazität errechnet. 
Wobei der Loop selbst auch eine Streukapazität aufweist, 
die ihreseits etwas vom L kompensiert (reale Verhältnisse!)"
"""


ANTENNENDATEN = Antenna(
    # name="Selfmade 1.25m n2",
    # call="DK3SS",
    color="#8c3bff",  # color from compare_colors.py
    selection_brand="Selfmade",
    selection_location="DK3SS",
    selection_name="1.25m n2",
    overview_pictures=("images/overview.jpg",),
    D_m=FloatText(1.25, "qrz_com_db_DK3SS.pdf"),
    d_m=DK3SS.d_m,
    n=DK3SS.n,
    p_m=DK3SS.p_m,
    powerPfwd_W=DK3SS.powerPfwd_W,
    info_str=DK3SS.info_str,
    info_thanks_str=DK3SS.info_thanks_str,
    info_enviroment_str=DK3SS.info_enviroment_str,
    info_conductor_str=DK3SS.info_conductor_str,
    info_capacitor_str=DK3SS.info_capacitor_str,
    measurement_html="../../shared/DK3SS/measurement.html",
    enviroment_html="../../shared/DK3SS/enviroment.html",
    antenna_build_html="../../shared/DK3SS/antenna_build.html",
    final_remarks_html="../../shared/DK3SS/final_remarks.html",
    bands=[
        BandData(
            f_Hz=FloatText(
                BANDS.f_hz_by_band_name["160m"], "keine Angabe daher Bandmitte"
            ),
            bw262_Hz=FloatText(
                bw262_Hz_160m, "berechnet aus angegebenem Q qrz_com_db_DK3SS.pdf"
            ),
            swr_min=FloatText(
                1.0,
                "20260808b_email_*.md -30dB Rückflussdaempfung: also gut angepasst",
            ),
        ),
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
    ],
)
