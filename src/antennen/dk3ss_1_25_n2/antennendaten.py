"""Structured data for the DK3SS 1.25m n2 loop."""

import html
from pathlib import Path

from antennenvergleich.antenna_calculations import AntennaCalculator
from antennenvergleich.constants import BANDS, DK3SS
from antennenvergleich.datatypes import Antenna, BandData, FloatText, IntText


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
    powerP_W=DK3SS.powerP_W,
    info_str=DK3SS.info_str,
    info_thanks_str=DK3SS.info_thanks_str,
    info_enviroment_str=DK3SS.info_enviroment_str,
    info_conductor_str=DK3SS.info_conductor_str,
    info_capacitor_str=DK3SS.info_capacitor_str,
    measurement_html=("../../shared/DK3SS/measurement.html",),
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


def _fmt_sig(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.3g}"


def _fmt_pf(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value * 1e12:.3g}"


def _build_summary_lines() -> list[str]:
    lines = ["#sym:ANTENNENDATEN", ""]
    lines.append(f"name: {ANTENNENDATEN.name}")
    lines.append(f"D_m: {_fmt_sig(ANTENNENDATEN.D_m.value)} m")
    lines.append(f"d_m: {_fmt_sig(ANTENNENDATEN.d_m.value)} m")
    lines.append(f"n: {_fmt_sig(ANTENNENDATEN.n.value)}")
    for band_name, band in zip(("160m", "80m", "40m"), ANTENNENDATEN.bands):
        calc = AntennaCalculator(
            D_m=ANTENNENDATEN.D_m.value,
            d_m=ANTENNENDATEN.d_m.value,
            n=ANTENNENDATEN.n.value or 1.0,
            p_m=ANTENNENDATEN.p_m.value or 0.0,
            swr_min=band.swr_min.value,
            f_Hz=band.f_Hz.value,
            bw262_Hz=band.bw262_Hz.value,
            powerP_W=ANTENNENDATEN.powerP_W.value,
        )
        lines.append(
            f"{band_name}: f={_fmt_sig(calc.f_Hz)} Hz, "
            f"L={_fmt_sig(calc.L_H)} H, C={_fmt_pf(calc.C_F)} pF"
        )
    return lines


def _write_cross_check_capacity_html() -> None:
    output_path = Path(__file__).with_name("cross_check_capacity.html")
    rows = []
    for band_name, band in zip(("160m", "80m", "40m"), ANTENNENDATEN.bands):
        calc = AntennaCalculator(
            D_m=ANTENNENDATEN.D_m.value,
            d_m=ANTENNENDATEN.d_m.value,
            n=ANTENNENDATEN.n.value or 1.0,
            p_m=ANTENNENDATEN.p_m.value or 0.0,
            swr_min=band.swr_min.value,
            f_Hz=band.f_Hz.value,
            bw262_Hz=band.bw262_Hz.value,
            powerP_W=ANTENNENDATEN.powerP_W.value,
        )
        website_c_f = {
            "160m": 500e-12 + 150e-12,
            "80m": 150e-12,
            "40m": 27e-12,
        }[band_name]
        rows.append(
            "<tr>"
            f"<td>{html.escape(band_name)}</td>"
            f"<td>{_fmt_sig(calc.f_Hz)}</td>"
            f"<td>{_fmt_sig(calc.L_H)}</td>"
            f"<td>{_fmt_pf(calc.C_F)}</td>"
            f"<td>{_fmt_pf(website_c_f)}</td>"
            "</tr>"
        )

    summary_html = "<pre>" + html.escape("\n".join(_build_summary_lines())) + "</pre>"
    website_info_html = "<pre>" + html.escape(_info_website) + "</pre>"
    html_text = f"""<!DOCTYPE html>
<html lang=\"de\">
<head>
  <meta charset=\"utf-8\">
  <title>Cross-check capacitance</title>
  <style>
    body {{ font-family: sans-serif; margin: 2rem; }}
    table {{ border-collapse: collapse; }}
    th, td {{ border: 1px solid #888; padding: 0.5rem; text-align: right; }}
    th {{ background: #f2f2f2; }}
    pre {{ background: #f7f7f7; padding: 1rem; border: 1px solid #ddd; }}
  </style>
</head>
<body>
  <h1>Cross-check capacitance</h1>
  <p>This file is automatically generated by {Path(__file__).name} when the module is imported.</p>
  <h2>Website info</h2>
  {website_info_html}
  {summary_html}
  <table>
    <thead>
      <tr>
        <th>Band</th>
        <th>f Hz</th>
        <th>Inductance L H</th>
        <th>Capacitance C calculated pF</th>
        <th>Capacitance on website C pF</th>
      </tr>
    </thead>
    <tbody>
      {"".join(rows)}
    </tbody>
  </table>
</body>
</html>
"""
    output_path.write_text(html_text, encoding="utf-8")


print("\n".join(_build_summary_lines()))
_write_cross_check_capacity_html()
