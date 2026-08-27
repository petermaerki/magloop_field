"""Generates compare.html — comparison table for magnetic loop antennas."""

import dataclasses
import html
import math
import os
import pathlib
from collections.abc import Callable

from antennenvergleich.datatypes import Antenna, BandData
from magloop_field.calculations import AntennaCalculator as FieldAntennaCalculator

from . import constants, loop_directories
from .antenna_calculations import (
    AntennaCalculator,
    _make_calc,
)
from .antenna_data_loader import load_antenna_data, read_values_file
from .antenna_fragments import build_and_write_antenna_fragments
from .antenna_efficiency_overview import build_efficiency_overview
from .antenna_page_layout import (
    build_antenna_css_rel,
    build_antenna_image_html,
    build_compare_overview_link_html,
    build_header_title,
    build_info_block_html,
    build_legacy_antenna_document,
)
from .antenna_sections import generate_inductivity_section, load_html_fragments
from .constants import BANDS
from .constants_s1p import (
    RESULTS_SUBDIR,
)
from .output_filenames import (
    FILENAME_ANTENNA_EFFICIENCY_TABLE,
    FILENAME_ANTENNA_PAGE,
    FILENAME_SVG_ETA_F,
    ID_SVG_ETA_F,
)

# ── Constants (same as calculations.py) ───────────────────────────────────────
_C_LIGHT = 299_792_458.0  # m/s

BAND_ORDER = ["10m", "12m", "15m", "20m", "30m", "40m", "60m", "80m", "160m"]

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent

_BAND_WAVELENGTHS_M = {
    "160m": 160.0,
    "80m": 80.0,
    "60m": 60.0,
    "40m": 40.0,
    "30m": 30.0,
    "20m": 20.0,
    "15m": 15.0,
    "12m": 12.0,
    "10m": 10.0,
}


def write_antenna_html(output_subdir: pathlib.Path) -> None:
    """Generate one antenna.html page for a given antenna results directory."""
    antenna_dir = output_subdir.parent
    antenna_dir_name = output_subdir.parent.name

    antenna_data = load_antenna_data(antenna_dir_name)

    environment_html_block = ""
    measurement_html_block = ""
    if antenna_data is not None:
        measurement_html_block = load_html_fragments(
            antenna_data=antenna_data,
            attribute_name="measurement_html",
            base_dir=output_subdir.parent,
            destination_dir=antenna_dir,
            warning_label="measurement_html",
        )
        environment_html_block = load_html_fragments(
            antenna_data=antenna_data,
            attribute_name="enviroment_html",
            base_dir=output_subdir.parent,
            destination_dir=antenna_dir,
            warning_label="enviroment_html",
        )

    overview = build_efficiency_overview(
        output_subdir=output_subdir,
        antenna_dir=antenna_dir,
        antenna_data=antenna_data,
        read_values_file=read_values_file,
    )
    table_rows = overview.table_rows
    chart_table_rows = overview.chart_table_rows
    first_values_with_model = overview.first_values_with_model
    efficiency_overview_html = overview.efficiency_overview_html
    (antenna_dir / FILENAME_ANTENNA_EFFICIENCY_TABLE).write_text(
        efficiency_overview_html,
        encoding="utf-8",
    )

    inductivity_section_html = generate_inductivity_section(
        output_subdir=output_subdir,
        antenna_dir=antenna_dir,
        antenna_data=antenna_data,
        first_values_with_model=first_values_with_model,
        antenna_dir_name=antenna_dir_name,
    )
    fragments = build_and_write_antenna_fragments(
        output_subdir=output_subdir,
        antenna_dir=antenna_dir,
        antenna_data=antenna_data,
        table_rows=table_rows,
        chart_table_rows=chart_table_rows,
        environment_html_block=environment_html_block,
        measurement_html_block=measurement_html_block,
        inductivity_section_html=inductivity_section_html,
    )
    measurement_section_html = fragments["measurement_section_html"]
    environment_section_html = fragments["environment_section_html"]
    measurements_section_html = fragments["measurements_section_html"]
    diagrams_section_html = fragments["diagrams_section_html"]
    h_field_section_html = fragments["h_field_section_html"]

    antenna_image_html = build_antenna_image_html(
        output_subdir=output_subdir,
        antenna_dir=antenna_dir,
        antenna_data=antenna_data,
    )
    info_block_html = build_info_block_html(antenna_data)
    header_title = build_header_title(antenna_dir_name, antenna_data)
    compare_overview_link_html = build_compare_overview_link_html(antenna_dir)
    antenna_css_rel = build_antenna_css_rel(antenna_dir)

    doc = build_legacy_antenna_document(
        antenna_dir_name=antenna_dir_name,
        antenna_css_rel=antenna_css_rel,
        header_title=header_title,
        antenna_image_html=antenna_image_html,
        info_block_html=info_block_html,
        efficiency_overview_html=efficiency_overview_html,
        measurement_section_html=measurement_section_html,
        environment_section_html=environment_section_html,
        measurements_section_html=measurements_section_html,
        diagrams_section_html=diagrams_section_html,
        inductivity_section_html=inductivity_section_html,
        h_field_section_html=h_field_section_html,
        compare_overview_link_html=compare_overview_link_html,
    )
    (antenna_dir / FILENAME_ANTENNA_PAGE).write_text(doc)


def _generate_antenna_html_files() -> int:
    """Generate antenna.html files for all antennas."""
    generated = 0
    src_dir = DIRECTORY_OF_THIS_FILE.parent
    antenna_data_files = sorted(src_dir.rglob("antennendaten.py"))
    for antenna_data_file in antenna_data_files:
        antenna_dir = antenna_data_file.parent
        results_dir = antenna_dir / RESULTS_SUBDIR
        write_antenna_html(results_dir)
        generated += 1
    return generated


def _band_from_frequency(f_Hz: float | None) -> str | None:
    if f_Hz is None or f_Hz <= 0:
        return None

    wavelength_m = _C_LIGHT / f_Hz
    return min(
        _BAND_WAVELENGTHS_M.items(),
        key=lambda item: abs(wavelength_m - item[1]),
    )[0]


def _antenna_info_tooltip(antenna: Antenna) -> str:
    """Return the antenna metadata text for the column header tooltip."""
    return "\n".join(
        [
            f"info_str={antenna.info_str}",
            f"info_enviroment_str={antenna.info_enviroment_str}",
            f"info_conductor_str={antenna.info_conductor_str}",
            f"info_capacitor_str={antenna.info_capacitor_str}",
        ]
    )


def _value_source(label: str, antenna: Antenna, bd: BandData) -> str | None:
    """Return source text for the numeric cell tooltip in a given row."""
    if label.startswith("Loop diameter"):
        return antenna.D_m.source
    if label.startswith("Conductor diameter"):
        return antenna.d_m.source
    if label.startswith("Loop count"):
        return antenna.n.source
    if label.startswith("Power into antenna"):
        return antenna.powerP_W.source
    if label.startswith("Frequency"):
        return bd.f_Hz.source
    if label.startswith("Bandwidth"):
        return bd.bw262_Hz.source
    if label == "swr_min":
        return bd.swr_min.source

    # Derived quantities are computed consistently from the listed inputs.
    return (
        "[Berechnet] Aus Geometrie-, Frequenz- und Bandbreitendaten "
        "gemäss den Formeln in run_2_html.py"
    )


# ── Value formatters ───────────────────────────────────────────────────────────
def _fmt_r(v: float) -> str:
    """Format a resistance value adaptively."""
    if abs(v) < 1e-5:
        return f"{v:.2e}"
    if abs(v) < 1e-3:
        return f"{v:.6f}"
    if abs(v) < 1e-2:
        return f"{v:.5f}"
    if abs(v) < 0.1:
        return f"{v:.4f}"
    return f"{v:.3f}"


def _fmt_percent(v: float) -> str:
    """Format percentage values without exponential notation."""
    av = abs(v)
    if av >= 100:
        return f"{v:.0f}"
    if av >= 10:
        return f"{v:.1f}"
    if av >= 1:
        return f"{v:.2f}"
    return f"{v:.3f}"


RowFormatter = Callable[[AntennaCalculator], str]


# (column-1 label, unit, tooltip description, formatter taking AntennaCalculator)
_ROWS: list[tuple[str, str, str, RowFormatter]] = [
    (
        "Loop diameter <i>D</i>",
        "m",
        "Äquivalenter Durchmesser der Loop.",
        lambda c: f"{c.D_m:.3f}",
    ),
    (
        "Conductor diameter <i>d</i>",
        "m",
        "Äquivalenter Leiterdurchmesser der Loop.",
        lambda c: f"{c.d_m:.3f}",
    ),
    (
        "Loop count <i>n</i>",
        "1",
        "Anzahl der Windungen der Schleife.",
        lambda c: f"{c.n:.0f}",
    ),
    (
        "Frequency <i>f</i>",
        "MHz",
        "Mittenfrequenz des betrachteten Bandes.",
        lambda c: f"{c.f_Hz / 1e6:.3f}",
    ),
    (
        "Bandwidth <i>B</i><sub>SWR=2.62</sub>",
        "kHz",
        "Bandbreite am Antenneneingang beim Kriterium SWR = 2.62.",
        lambda c: f"{c.bw262_Hz / 1e3:.2f}",
    ),
    (
        "Power into antenna <i>P</i>",
        "W",
        "Eingespeiste Leistung in die Antenne.",
        lambda c: f"{c.powerP_W:.0f}",
    ),
    (
        "Inductance <i>L</i>",
        "H",
        "Berechnete Induktivität der Loop.",
        lambda c: f"{c.L_H:.2e}",
    ),
    (
        "Capacitance <i>C</i>",
        "F",
        "Erforderliche Resonanzkapazität bei der Bandfrequenz.",
        lambda c: f"{c.C_F:.2e}",
    ),
    (
        "Unloaded Q<sub>0</sub>",
        "1",
        "Unbelastete Güte, aus f / Bandbreite abgeschätzt.",
        lambda c: f"{c.Q0:.0f}",
    ),
    (
        "Damping resistance <i>R</i><sub>T</sub>",
        "Ohm",
        "Gesamter Dämpfungswiderstand des Resonanzkreises.",
        lambda c: _fmt_r(c.RT_Ohm),
    ),
    (
        "Radiation resistance <i>R</i><sub>R</sub>",
        "Ohm",
        "Äquivalenter Strahlungswiderstand der Antenne.",
        lambda c: _fmt_r(c.RR_Ohm),
    ),
    (
        "Loss resistance <i>R</i><sub>Loss</sub>",
        "Ohm",
        "Verlustwiderstand: R_T - R_R.",
        lambda c: _fmt_r(c.RLoss_Ohm),
    ),
    (
        "swr_min",
        "1",
        "Minimales SWR am Antenneneingang.",
        lambda c: f"{c.swr_min:.2f}",
    ),
    (
        "eta<sub>SWR_ant</sub>",
        "%",
        "Anpassungswirkungsgrad aus swr_min: eta = 4*SWR/(1+SWR)^2.",
        lambda c: _fmt_percent(c.eta_SWR_ant * 100),
    ),
    (
        "<b>Antenna efficiency <i>η</i></b>",
        "%",
        "Gesamteffizienz: (R_R / R_T) * eta_SWR_ant.",
        lambda c: _fmt_percent(c.eta * 100),
    ),
    (
        "Loop current <i>I</i>",
        "A",
        "Strom im Hauptloop bei der Referenzleistung.",
        lambda c: f"{c.I_main_loop_A:.2f}",
    ),
    (
        "Loop voltage <i>U</i><sub>loop</sub>",
        "V",
        "Spannung über dem Loop bei Resonanz.",
        lambda c: f"{c.U_loop_V:.0f}",
    ),
    (
        "Magnetic dipole moment <i>m</i>",
        "A m²",
        "Magnetisches Dipolmoment des Loops.",
        lambda c: f"{c.m_Am2:.3f}",
    ),
]


# ── HTML generation ────────────────────────────────────────────────────────────

class HtmlRenderer:
    def __init__(
        self,
        html_root_directory=constants.DIRECTORY_REPO,
    ) -> None:
        self.html_root_directory = html_root_directory
        self.sections: list[str] = []
        self.html_prefix = f"""<!-- Automatically generated file by run_2_html.py. Do not edit manually. -->

<!DOCTYPE html>
<html lang=\"de\">
<head>
    <meta charset=\"utf-8\">
    <title>Magnetic Loop Antenna Compare</title>
    <link rel="stylesheet" href="static/css/style_compare.css">
</head>
<body>
<img src="{FILENAME_SVG_ETA_F}" id="{ID_SVG_ETA_F}" alt="Antenna efficiency eta over frequency">
"""

    def _build_calculator_url(
        self, antenna: Antenna, band_data: BandData | None = None
    ) -> str:
        """Build calculator URL with parameters from antenna and optional band data."""

        def fmt_param(value: float | int, decimals: int) -> str:
            if isinstance(value, int):
                return str(value)
            text = f"{value:.{decimals}f}".rstrip("0").rstrip(".")
            return text or "0"

        # Use relative path so it works both locally and on GitHub Pages
        base_url = "index.html"
        params = []

        # Extract geometry parameters from antenna
        if antenna.D_m.value is not None:
            params.append(f"D_m={fmt_param(antenna.D_m.value, 4)}")
        if antenna.d_m.value is not None:
            params.append(f"d_m={fmt_param(antenna.d_m.value, 4)}")
        if antenna.n.value is not None:
            params.append(f"n={antenna.n.value}")
        if antenna.p_m.value is not None:
            params.append(f"p_m={antenna.p_m.value}")

        # Extract band-specific parameters
        if band_data is not None:
            if band_data.f_Hz.value is not None:
                params.append(f"f_Hz={band_data.f_Hz.value}")
            if band_data.bw262_Hz.value is not None:
                params.append(f"bw_Hz={fmt_param(band_data.bw262_Hz.value, 0)}")

        # Extract power parameter
        if antenna.powerP_W.value is not None:
            params.append(f"P_W={antenna.powerP_W.value}")

        if params:
            return f"{base_url}?{'&'.join(params)}"
        return base_url

    def _overview_pictures_from_field(
        self, antenna: Antenna, antenna_dir: pathlib.Path
    ) -> list[str]:
        files: list[str] = []
        for filename_relative in antenna.overview_pictures:
            rel_clean = filename_relative.strip()
            assert rel_clean == filename_relative, (
                f"Path has leading/ending spaces: '{filename_relative}'!"
            )
            filename = (antenna_dir / filename_relative).resolve()
            rel_to_html = self._get_relative_path(filename=filename)
            files.append(rel_to_html)
        return files

    @staticmethod
    def _preferred_band_data(antenna: Antenna) -> BandData | None:
        by_band: dict[str, BandData] = {}
        for bd in antenna.bands:
            band = _band_from_frequency(bd.f_Hz.value)
            if band is not None and band not in by_band:
                by_band[band] = bd
        for band in BAND_ORDER:
            if band in by_band:
                return by_band[band]
        return antenna.bands[0] if antenna.bands else None

    def _get_relative_path(self, filename: pathlib.Path) -> str:
        if constants.IS_PYODIDE:
            # The following line will fail if the resulting path starts with '../'
            # which never should happen on the web...
            rel = str(filename.relative_to(self.html_root_directory))
            # print("rel:", rel)
            return rel.replace("site-packages/", "src/")

        assert filename.is_file(), f"Path does not exist: '{filename}'!"
        return os.path.relpath(filename, self.html_root_directory)

    def render(self, antenna_entries: list[loop_directories.AntennaPlusDirectory]) -> None:
        if not antenna_entries:
            return

        header_brand = "<tr><th style='font-weight: normal;'>Brand</th><th></th>"
        header_names = "<tr><th style='font-weight: normal;'>Name</th><th></th>"
        header_calls = "<tr><th style='font-weight: normal;'>Location</th><th></th>"
        header_overview_colors = (
            "<tr><th style='font-weight: normal;'>Color</th><th></th>"
        )
        header_overview_pictures = (
            "<tr><th style='font-weight: normal;'>Picture</th><th></th>"
        )
        for entry in antenna_entries:
            antenna = entry.antenna
            tooltip_text = _antenna_info_tooltip(antenna)
            tooltip_attr = html.escape(tooltip_text, quote=True)
            brand_html = html.escape(antenna.selection_brand)
            name_html = html.escape(antenna.selection_name)
            location_html = html.escape(antenna.selection_location)
            header_brand += f"<th style='font-weight: normal;' title='{tooltip_attr}'>{brand_html}</th>"
            header_names += f"<th style='font-weight: normal;' title='{tooltip_attr}'>{name_html}</th>"
            header_calls += f"<th style='font-weight: normal;'>{location_html}</th>"
            color = html.escape(antenna.color, quote=True)
            header_overview_colors += (
                "<th class='color-cell'>"
                f"<div class='color-swatch' style='background:{color};'></div>"
                "</th>"
            )
            overview_pictures = self._overview_pictures_from_field(antenna, entry.directory)
            if not overview_pictures:
                header_overview_pictures += "<th></th>"
            else:
                images_html = ""
                for overview_picture in overview_pictures:
                    src = html.escape(overview_picture, quote=True)
                    alt = html.escape(
                        f"Overview picture {antenna.selection_brand} {antenna.selection_name} {antenna.selection_location}",
                        quote=True,
                    )
                    images_html += (
                        f"<img class='overview-picture' src='{src}' alt='{alt}'>"
                    )
                header_overview_pictures += (
                    f"<th><div class='overview-pictures'>{images_html}</div></th>"
                )
        header_brand += "</tr>"
        header_names += "</tr>"
        header_calls += "</tr>"
        header_overview_colors += "</tr>"
        header_overview_pictures += "</tr>"
        header_block_prefix = (
            f"{header_brand}{header_names}{header_calls}"
            f"{header_overview_colors}{header_overview_pictures}"
        )

        band_data_by_dir: dict[pathlib.Path, dict[str, BandData]] = {}
        for entry in antenna_entries:
            by_band: dict[str, BandData] = {}
            for bd in entry.antenna.bands:
                band = _band_from_frequency(bd.f_Hz.value)
                if band is not None and band not in by_band:
                    by_band[band] = bd
            band_data_by_dir[entry.directory] = by_band

        available_bands = [
            band
            for band in BAND_ORDER
            if any(band in band_data_by_dir[entry.directory] for entry in antenna_entries)
        ]

        body = ""
        for band_index, band in enumerate(available_bands):
            header_overview_links_band = (
                "<tr><th style='font-weight: normal;'>Links</th><th></th>"
            )
            for entry in antenna_entries:
                filename_html_antenna = (
                    entry.directory / FILENAME_ANTENNA_PAGE
                ).resolve()
                filename_relative = self._get_relative_path(filename_html_antenna)
                band_data = band_data_by_dir[entry.directory].get(band)
                calculator_url = self._build_calculator_url(entry.antenna, band_data)
                link_html = (
                    f"<a href='{html.escape(filename_relative, quote=True)}'>description</a>"
                    "<br>"
                    f"<a href='{html.escape(calculator_url, quote=True)}' style='text-decoration: underline;'>calculator</a>"
                )
                header_overview_links_band += (
                    f"<th style='font-weight: normal;'>{link_html}</th>"
                )
            header_overview_links_band += "</tr>"

            band_row_class = "band-row" if band_index == 0 else "band-row band-row-sep"
            body += (
                f"<tr class='{band_row_class}'>"
                f"<td class='band-label' colspan='{len(antenna_entries) + 2}'>{band} Band</td>"
                "</tr>\n"
            )
            body += header_block_prefix + header_overview_links_band
            for label, unit, tooltip, fmt in _ROWS:
                is_rloss = "Loss" in label
                is_efficiency_row = "Antenna efficiency" in label
                unit_html = f"<b>{unit}</b>" if is_efficiency_row else unit
                tooltip_attr = html.escape(tooltip, quote=True)
                row_class = " class='efficiency-row'" if is_efficiency_row else ""
                row = f"<tr{row_class}><td title='{tooltip_attr}'>{label}</td><td class='unit'>{unit_html}</td>"
                for entry in antenna_entries:
                    band_data = band_data_by_dir[entry.directory].get(band)
                    if band_data is None:
                        row += "<td class='val miss'></td>"
                        continue
                    calc = _make_calc(entry.antenna, band_data)
                    val = fmt(calc)
                    if is_efficiency_row:
                        val = f"<b>{val}</b>"
                    highlight_neg = is_rloss and calc.RLoss_Ohm < 0
                    highlight_over_100_efficiency = (
                        is_efficiency_row and (calc.eta * 100) > 100
                    )
                    extra = (
                        " neg"
                        if (highlight_neg or highlight_over_100_efficiency)
                        else ""
                    )
                    source_text = _value_source(label, entry.antenna, band_data) or ""
                    source_attr = html.escape(source_text, quote=True)
                    row += f"<td class='val{extra}' title='{source_attr}'>{val}</td>"
                row += "</tr>\n"
                body += row

        section = (
            "<div class='compare-scroll-dual'>\n"
            "<div class='compare-table-scroll-top' aria-hidden='true'><div class='compare-table-scroll-top-inner'></div></div>\n"
            "<div class='compare-table-wrap'>\n"
            f"<table>\n<tbody>{body}</tbody>\n</table>\n"
            "</div>\n"
            "</div>\n"
        )
        self.sections.append(section)

    def close(self) -> str:
        html_suffix = """
<p style='margin-top: 2rem; font-size: 0.9rem; color: #666;'>No guarantee for correctness! Feedback is welcome.</p>
</body>
</html>
"""
        html = f"{self.html_prefix}{''.join(self.sections)}{html_suffix}"
        return html


@dataclasses.dataclass(frozen=True)
class BandAntenna:
    antenna: Antenna
    band_data: BandData
    antenna_dir: pathlib.Path


def get_antennas_in_band(
    antenna_entries: list[loop_directories.AntennaPlusDirectory],
    band: str,
) -> list[BandAntenna]:
    """Return all antennas with their selected band data for the requested band."""
    result: list[BandAntenna] = []
    for entry in antenna_entries:
        antenna = entry.antenna
        selected_band = next(
            (bd for bd in antenna.bands if _band_from_frequency(bd.f_Hz.value) == band),
            None,
        )
        if selected_band is not None:
            result.append(
                BandAntenna(
                    antenna=antenna,
                    band_data=selected_band,
                    antenna_dir=entry.directory,
                )
            )
    return result


class Diagramm_eta_f_svg:
    _BAND_CENTERS_MHZ = [
        1.85,
        3.65,
        5.35,
        7.1,
        10.1,
        14.2,
        21.2,
        28.5,
    ]  # ITU amateur band centers

    _W = 860
    _H = 520
    _ML = 85  # margin left
    _MR = 230  # margin right (legend)
    _MT = 40  # margin top
    _MB = 65  # margin bottom

    _F_MIN_HZ = 1.5e6
    _F_MAX_HZ = 35.0e6
    _ETA_MIN = 1.0e-5  # 0.001 %

    def __init__(self) -> None:
        self._pw = self._W - self._ML - self._MR
        self._ph = self._H - self._MT - self._MB
        self._ETA_MAX = 1.0  # overwritten in render() from data

    def _px(self, f_Hz: float) -> float:
        lf = math.log10(f_Hz)
        lmin = math.log10(self._F_MIN_HZ)
        lmax = math.log10(self._F_MAX_HZ)
        return self._ML + (lf - lmin) / (lmax - lmin) * self._pw

    def _visible_band_centers_mhz(self) -> list[float]:
        return [
            f_mhz
            for f_mhz in self._BAND_CENTERS_MHZ
            if self._F_MIN_HZ <= f_mhz * 1e6 <= self._F_MAX_HZ
        ]

    def _py(self, eta: float) -> float:
        if eta <= 0:
            return self._MT + self._ph
        le = math.log10(eta)
        lmin = math.log10(self._ETA_MIN)
        lmax = math.log10(self._ETA_MAX)
        return self._MT + (1.0 - (le - lmin) / (lmax - lmin)) * self._ph

    @staticmethod
    def _eta_points_for_antenna(antenna: Antenna) -> list[tuple[float, float]]:
        pts: list[tuple[float, float]] = []
        for bd in antenna.bands:
            if bd.f_Hz.value is None or bd.bw262_Hz.value is None:
                continue
            calc = _make_calc(antenna, bd)
            if calc.eta > 0:
                pts.append((bd.f_Hz.value, calc.eta))
        pts.sort()
        return pts

    def _collect_data(
        self, antennas: list[Antenna]
    ) -> list[tuple[Antenna, list[tuple[float, float]]]]:
        result = []
        for antenna in antennas:
            if antenna.D_m.value is None or antenna.d_m.value is None:
                continue
            pts = self._eta_points_for_antenna(antenna)
            if pts:
                result.append((antenna, pts))
        result.sort(key=lambda item: item[0].antenna_label.casefold())
        return result

    def render(
        self,
        antennas: list[Antenna],
    ) -> str:
        data = self._collect_data(antennas)
        all_etas = [e for _, pts in data for _, e in pts]
        if all_etas:
            self._ETA_MAX = 10.0 ** math.ceil(math.log10(max(all_etas)))
        buf: list[str] = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self._W}" height="{self._H}" viewBox="0 0 {self._W} {self._H}">',
            f'  <rect width="{self._W}" height="{self._H}" fill="white"/>',
            f'  <clipPath id="plotarea"><rect x="{self._ML}" y="{self._MT}" width="{self._pw}" height="{self._ph}"/></clipPath>',
        ]
        buf += self._draw_grid()
        buf += self._draw_frame()
        buf += self._draw_x_ticks()
        buf += self._draw_y_ticks()
        buf += self._draw_axis_labels()
        for antenna, pts in data:
            buf += self._draw_series(pts, antenna.color)
        buf += self._draw_legend(
            [(antenna.antenna_label, antenna.color) for antenna, _ in data]
        )
        buf.append("</svg>")
        return "\n".join(buf)

    def _draw_grid(self) -> list[str]:
        lines = []
        x0, x1 = self._ML, self._ML + self._pw
        y0, y1 = self._MT, self._MT + self._ph
        for f_mhz in self._visible_band_centers_mhz():
            x = self._px(f_mhz * 1e6)
            lines.append(
                f'  <line x1="{x:.1f}" y1="{y0}" x2="{x:.1f}" y2="{y1}" stroke="#e0e0e0" stroke-width="1"/>'
            )
        exp_max = round(math.log10(self._ETA_MAX))
        for exp in range(-5, exp_max + 1):
            y = self._py(10.0**exp)
            lines.append(
                f'  <line x1="{x0}" y1="{y:.1f}" x2="{x1}" y2="{y:.1f}" stroke="#e0e0e0" stroke-width="1"/>'
            )
        return lines

    def _draw_frame(self) -> list[str]:
        return [
            f'  <rect x="{self._ML}" y="{self._MT}" width="{self._pw}" height="{self._ph}" fill="none" stroke="#888" stroke-width="1.5"/>',
        ]

    def _draw_x_ticks(self) -> list[str]:
        lines = []
        y_base = self._MT + self._ph
        for f_mhz in self._visible_band_centers_mhz():
            x = self._px(f_mhz * 1e6)
            lines.append(
                f'  <line x1="{x:.1f}" y1="{y_base}" x2="{x:.1f}" y2="{y_base + 5}" stroke="#888" stroke-width="1.5"/>'
            )
            lines.append(
                f'  <text x="{x:.1f}" y="{y_base + 18}" text-anchor="middle" font-size="11" font-family="Arial,sans-serif" fill="#333">{f_mhz:.1f}</text>'
            )
        return lines

    def _draw_y_ticks(self) -> list[str]:
        lines = []
        all_tick_labels = {
            -5: "0.001%",
            -4: "0.01%",
            -3: "0.1%",
            -2: "1%",
            -1: "10%",
            0: "100%",
        }
        exp_max = round(math.log10(self._ETA_MAX))
        tick_labels = {k: v for k, v in all_tick_labels.items() if k <= exp_max}
        for exp, label in tick_labels.items():
            y = self._py(10.0**exp)
            lines.append(
                f'  <line x1="{self._ML - 5}" y1="{y:.1f}" x2="{self._ML}" y2="{y:.1f}" stroke="#888" stroke-width="1.5"/>'
            )
            lines.append(
                f'  <text x="{self._ML - 8}" y="{y + 4:.1f}" text-anchor="end" font-size="11" font-family="Arial,sans-serif" fill="#333">{label}</text>'
            )
        return lines

    def _draw_axis_labels(self) -> list[str]:
        cx = self._ML + self._pw / 2
        cy = self._MT + self._ph / 2
        return [
            f'  <text x="{cx:.1f}" y="{self._MT + self._ph + 50}" text-anchor="middle" font-size="13" font-family="Arial,sans-serif" fill="#222">f (MHz)</text>',
            f'  <text transform="rotate(-90 25 {cy:.1f})" x="25" y="{cy:.1f}" text-anchor="middle" font-size="13" font-family="Arial,sans-serif" fill="#222">η (Wirkungsgrad)</text>',
        ]

    def _draw_series(self, pts: list[tuple[float, float]], color: str) -> list[str]:
        lines = []
        coords = " ".join(f"{self._px(f):.2f},{self._py(e):.2f}" for f, e in pts)
        lines.append(
            f'  <polyline points="{coords}" fill="none" stroke="{color}" stroke-width="1.8" clip-path="url(#plotarea)"/>'
        )
        for f, e in pts:
            x, y = self._px(f), self._py(e)
            lines.append(
                f'  <circle cx="{x:.2f}" cy="{y:.2f}" r="4" fill="{color}" stroke="white" stroke-width="1" clip-path="url(#plotarea)"/>'
            )
        return lines

    def _draw_legend(self, entries: list[tuple[str, str]]) -> list[str]:
        lines = []
        lx = self._ML + self._pw + 18
        ly = self._MT + 10
        for i, (name, color) in enumerate(entries):
            y = ly + i * 22
            lines.append(
                f'  <line x1="{lx}" y1="{y + 7}" x2="{lx + 25}" y2="{y + 7}" stroke="{color}" stroke-width="2"/>'
            )
            lines.append(
                f'  <circle cx="{lx + 12}" cy="{y + 7}" r="4" fill="{color}" stroke="white" stroke-width="1"/>'
            )
            lines.append(
                f'  <text x="{lx + 32}" y="{y + 11}" font-size="11" font-family="Arial,sans-serif" fill="#333">{html.escape(name)}</text>'
            )
        return lines


class Diagramm_eta_D_lambda_svg:
    _W = 860
    _H = 520
    _ML = 85
    _MR = 230
    _MT = 40
    _MB = 65

    _ETA_MIN = 1.0e-5

    def __init__(self) -> None:
        self._pw = self._W - self._ML - self._MR
        self._ph = self._H - self._MT - self._MB
        self._ETA_MAX = 1.0
        self._X_MIN = 0.0
        self._X_MAX = 1.0

    def _px(self, x_value: float) -> float:
        return (
            self._ML + (x_value - self._X_MIN) / (self._X_MAX - self._X_MIN) * self._pw
        )

    def _py(self, eta: float) -> float:
        if eta <= 0:
            return self._MT + self._ph
        le = math.log10(eta)
        lmin = math.log10(self._ETA_MIN)
        lmax = math.log10(self._ETA_MAX)
        return self._MT + (1.0 - (le - lmin) / (lmax - lmin)) * self._ph

    def _collect_data(
        self, antennas: list[Antenna]
    ) -> list[tuple[Antenna, list[tuple[float, float]]]]:
        result = []
        for antenna in antennas:
            if antenna.D_m.value is None:
                continue
            pts: list[tuple[float, float]] = []
            for bd in antenna.bands:
                if bd.f_Hz.value is None or bd.bw262_Hz.value is None:
                    continue
                calc = _make_calc(antenna, bd)
                if calc.eta > 0:
                    wavelength_m = _C_LIGHT / bd.f_Hz.value
                    x_value = antenna.D_m.value / wavelength_m
                    pts.append((x_value, calc.eta))
            pts.sort()
            if pts:
                result.append((antenna, pts))
            result.sort(key=lambda item: item[0].antenna_label.casefold())
        return result

    def render(
        self,
        antennas: list[Antenna],
    ) -> str:
        data = self._collect_data(antennas)
        all_etas = [e for _, pts in data for _, e in pts]
        xs = [x for _, pts in data for x, _ in pts]
        if all_etas:
            self._ETA_MAX = 10.0 ** math.ceil(math.log10(max(all_etas)))
        if xs:
            self._X_MIN = min(xs) * 0.95 if min(xs) > 0 else 0.0
            self._X_MAX = max(xs) * 1.05 if max(xs) > self._X_MIN else self._X_MIN + 1.0
        buf: list[str] = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self._W}" height="{self._H}" viewBox="0 0 {self._W} {self._H}">',
            f'  <rect width="{self._W}" height="{self._H}" fill="white"/>',
            f'  <clipPath id="plotarea"><rect x="{self._ML}" y="{self._MT}" width="{self._pw}" height="{self._ph}"/></clipPath>',
        ]
        buf += self._draw_grid(xs)
        buf += self._draw_frame()
        buf += self._draw_x_ticks(xs)
        buf += self._draw_y_ticks()
        buf += self._draw_axis_labels()
        for antenna, pts in data:
            buf += self._draw_series(pts, antenna.color)
        buf += self._draw_legend(
            [(antenna.antenna_label, antenna.color) for antenna, _ in data]
        )
        buf.append("</svg>")
        return "\n".join(buf)

    def _draw_grid(self, xs: list[float]) -> list[str]:
        lines = []
        x0, x1 = self._ML, self._ML + self._pw
        y0, y1 = self._MT, self._MT + self._ph
        if xs:
            for tick in range(6):
                x_value = self._X_MIN + (self._X_MAX - self._X_MIN) * tick / 5.0
                x = self._px(x_value)
                lines.append(
                    f'  <line x1="{x:.1f}" y1="{y0}" x2="{x:.1f}" y2="{y1}" stroke="#e0e0e0" stroke-width="1"/>'
                )
        exp_max = round(math.log10(self._ETA_MAX))
        for exp in range(-5, exp_max + 1):
            y = self._py(10.0**exp)
            lines.append(
                f'  <line x1="{x0}" y1="{y:.1f}" x2="{x1}" y2="{y:.1f}" stroke="#e0e0e0" stroke-width="1"/>'
            )
        return lines

    def _draw_frame(self) -> list[str]:
        return [
            f'  <rect x="{self._ML}" y="{self._MT}" width="{self._pw}" height="{self._ph}" fill="none" stroke="#888" stroke-width="1.5"/>'
        ]

    def _draw_x_ticks(self, xs: list[float]) -> list[str]:
        lines = []
        y_base = self._MT + self._ph
        if xs:
            for tick in range(6):
                x_value = self._X_MIN + (self._X_MAX - self._X_MIN) * tick / 5.0
                x = self._px(x_value)
                lines.append(
                    f'  <line x1="{x:.1f}" y1="{y_base}" x2="{x:.1f}" y2="{y_base + 5}" stroke="#888" stroke-width="1.5"/>'
                )
                label = (
                    f"{x_value:.2f}".rstrip("0").rstrip(".") if x_value != 0 else "0"
                )
                lines.append(
                    f'  <text x="{x:.1f}" y="{y_base + 18}" text-anchor="middle" font-size="11" font-family="Arial,sans-serif" fill="#333">{label}</text>'
                )
        return lines

    def _draw_y_ticks(self) -> list[str]:
        lines = []
        all_tick_labels = {
            -5: "0.001%",
            -4: "0.01%",
            -3: "0.1%",
            -2: "1%",
            -1: "10%",
            0: "100%",
        }
        exp_max = round(math.log10(self._ETA_MAX))
        tick_labels = {k: v for k, v in all_tick_labels.items() if k <= exp_max}
        for exp, label in tick_labels.items():
            y = self._py(10.0**exp)
            lines.append(
                f'  <line x1="{self._ML - 5}" y1="{y:.1f}" x2="{self._ML}" y2="{y:.1f}" stroke="#888" stroke-width="1.5"/>'
            )
            lines.append(
                f'  <text x="{self._ML - 8}" y="{y + 4:.1f}" text-anchor="end" font-size="11" font-family="Arial,sans-serif" fill="#333">{label}</text>'
            )
        return lines

    def _draw_axis_labels(self) -> list[str]:
        cx = self._ML + self._pw / 2
        cy = self._MT + self._ph / 2
        return [
            f'  <text x="{cx:.1f}" y="{self._MT + self._ph + 50}" text-anchor="middle" font-size="13" font-family="Arial,sans-serif" fill="#222">D / λ</text>',
            f'  <text transform="rotate(-90 25 {cy:.1f})" x="25" y="{cy:.1f}" text-anchor="middle" font-size="13" font-family="Arial,sans-serif" fill="#222">η (Wirkungsgrad)</text>',
        ]

    def _draw_series(self, pts: list[tuple[float, float]], color: str) -> list[str]:
        lines = []
        coords = " ".join(f"{self._px(x):.2f},{self._py(e):.2f}" for x, e in pts)
        lines.append(
            f'  <polyline points="{coords}" fill="none" stroke="{color}" stroke-width="1.8" clip-path="url(#plotarea)"/>'
        )
        for x, e in pts:
            x_pos, y_pos = self._px(x), self._py(e)
            lines.append(
                f'  <circle cx="{x_pos:.2f}" cy="{y_pos:.2f}" r="4" fill="{color}" stroke="white" stroke-width="1" clip-path="url(#plotarea)"/>'
            )
        return lines

    def _draw_legend(self, entries: list[tuple[str, str]]) -> list[str]:
        lines = []
        lx = self._ML + self._pw + 18
        ly = self._MT + 10
        for i, (name, color) in enumerate(entries):
            y = ly + i * 22
            lines.append(
                f'  <line x1="{lx}" y1="{y + 7}" x2="{lx + 25}" y2="{y + 7}" stroke="{color}" stroke-width="2"/>'
            )
            lines.append(
                f'  <circle cx="{lx + 12}" cy="{y + 7}" r="4" fill="{color}" stroke="white" stroke-width="1"/>'
            )
            lines.append(
                f'  <text x="{lx + 32}" y="{y + 11}" font-size="11" font-family="Arial,sans-serif" fill="#333">{html.escape(name)}</text>'
            )
        return lines
