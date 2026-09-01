"""Generates compare.html — comparison table for magnetic loop antennas."""

import dataclasses
import html
import os
import pathlib
from collections.abc import Callable

from antennenvergleich.datatypes import Antenna, BandData

from . import constants, loop_directories, renderer_diagram_svg
from .antenna_calculations import (
    AntennaCalculator,
    _make_calc,
)

# ── Constants (same as calculations.py) ───────────────────────────────────────
DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent


def _band_sort_key(band_name: str) -> int:
    assert band_name.endswith("m"), band_name
    return int(band_name.removesuffix("m"))


def _band_from_frequency(f_Hz: float | None) -> str | None:
    if f_Hz is None or f_Hz <= 0:
        return None

    return min(
        constants.BANDS.f_hz_by_band_name.items(),
        key=lambda item: abs(f_Hz - item[1]),
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


_DERIVED_SOURCE_TOOLTIP = (
    "[Computed] From geometry, frequency, and bandwidth data "
    "according to the formulas in calculations.py "
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
SourceFormatter = Callable[[Antenna, BandData], str | None]


def _source_derived(_antenna: Antenna, _bd: BandData) -> str:
    return _DERIVED_SOURCE_TOOLTIP


def _source_power_load(_antenna: Antenna, _bd: BandData) -> str:
    return "[Computed] P_load = P_fwd * eta_SWR_ant"


# (column-1 label, unit, tooltip description, value formatter, source formatter)
_ROWS: list[tuple[str, str, str, RowFormatter, SourceFormatter]] = [
    (
        "Loop diameter <i>D</i>",
        "m",
        "Äquivalenter Durchmesser der Loop.",
        lambda c: f"{c.D_m:.3f}",
        lambda antenna, _bd: antenna.D_m.source,
    ),
    (
        "Conductor diameter <i>d</i>",
        "m",
        "Äquivalenter Leiterdurchmesser der Loop.",
        lambda c: f"{c.d_m:.3f}",
        lambda antenna, _bd: antenna.d_m.source,
    ),
    (
        "Loop count <i>n</i>",
        "1",
        "Anzahl der Windungen der Schleife.",
        lambda c: f"{c.n:.0f}",
        lambda antenna, _bd: antenna.n.source,
    ),
    (
        "Frequency <i>f</i>",
        "MHz",
        "Mittenfrequenz des betrachteten Bandes.",
        lambda c: f"{c.f_Hz / 1e6:.3f}",
        lambda _antenna, bd: bd.f_Hz.source,
    ),
    (
        "Bandwidth <i>B</i><sub>SWR=2.62</sub>",
        "kHz",
        "Bandbreite am Antenneneingang beim Kriterium SWR = 2.62.",
        lambda c: f"{c.bw262_Hz / 1e3:.2f}",
        lambda _antenna, bd: bd.bw262_Hz.source,
    ),
    (
        "Inductance <i>L</i>",
        "H",
        "Berechnete Induktivität der Loop.",
        lambda c: f"{c.L_H:.2e}",
        _source_derived,
    ),
    (
        "Capacitance <i>C</i>",
        "F",
        "Erforderliche Resonanzkapazität bei der Bandfrequenz.",
        lambda c: f"{c.C_F:.2e}",
        _source_derived,
    ),
    (
        "Unloaded Q<sub>0</sub>",
        "1",
        "Unbelastete Güte, aus f / Bandbreite abgeschätzt.",
        lambda c: f"{c.Q0:.0f}",
        _source_derived,
    ),
    (
        "Damping resistance <i>R</i><sub>T</sub>",
        "Ohm",
        "Gesamter Dämpfungswiderstand des Resonanzkreises.",
        lambda c: _fmt_r(c.RT_Ohm),
        _source_derived,
    ),
    (
        "Radiation resistance <i>R</i><sub>R</sub>",
        "Ohm",
        "Äquivalenter Strahlungswiderstand der Antenne.",
        lambda c: _fmt_r(c.RR_Ohm),
        _source_derived,
    ),
    (
        "Loss resistance <i>R</i><sub>Loss</sub>",
        "Ohm",
        "Verlustwiderstand: R_T - R_R.",
        lambda c: _fmt_r(c.RLoss_Ohm),
        _source_derived,
    ),
    (
        "Power to antenna <i>P</i><sub>fwd</sub>",
        "W",
        "Power towards the antenna feed point <br>(forward power after cable losses; a portion may be reflected due to SWR mismatch).",
        lambda c: f"{c.powerPfwd_W:.0f}",
        lambda antenna, _bd: antenna.powerPfwd_W.source,
    ),
    (
        "swr_min",
        "1",
        "Minimales SWR am Antenneneingang.",
        lambda c: f"{c.swr_min:.2f}",
        lambda _antenna, bd: bd.swr_min.source,
    ),
    (
        "eta<sub>SWR_ant</sub>",
        "%",
        "Anpassungswirkungsgrad aus swr_min: eta = 4*SWR/(1+SWR)^2.",
        lambda c: _fmt_percent(c.eta_SWR_ant * 100),
        _source_derived,
    ),
    (
        "Power antenna load <i>P</i><sub>load</sub>",
        "W",
        "Power in antenna load: P_load = P_fwd * eta_SWR_ant.",
        lambda c: f"{c.powerPload_W:.0f}",
        _source_power_load,
    ),
    (
        "<b>Antenna efficiency <i>η</i></b>",
        "%",
        "Gesamteffizienz: (R_R / R_T) * eta_SWR_ant.",
        lambda c: _fmt_percent(c.eta * 100),
        _source_derived,
    ),
    (
        "Loop current <i>I</i> rms",
        "A",
        "Strom im Hauptloop bei der Referenzleistung.",
        lambda c: f"{c.I_main_loop_A:.2f}",
        _source_derived,
    ),
    (
        "Loop voltage <i>U</i><sub>loop</sub> rms",
        "V",
        "Spannung über dem Loop bei Resonanz.",
        lambda c: f"{c.U_loop_V:.0f}",
        _source_derived,
    ),
    (
        "Magnetic dipole moment <i>m</i>",
        "A m²",
        "Magnetisches Dipolmoment des Loops.",
        lambda c: f"{c.m_Am2:.3f}",
        _source_derived,
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
        self.sections.append(
            f"""<img src="{renderer_diagram_svg.FILENAME_SVG_ETA_F}" id="{renderer_diagram_svg.ID_SVG_ETA_F}" alt="Antenna efficiency eta over frequency">"""
        )

        self.html_prefix = """<!-- Automatically generated file by run_2_html.py. Do not edit manually. -->

<!DOCTYPE html>
<html lang=\"de\">
<head>
    <meta charset=\"utf-8\">
    <title>Magnetic Loop Antenna Compare</title>
    <link rel="stylesheet" href="static/css/style_compare.css">
</head>
<body>
<h1>Magnetic Loop Antenna Compare</h1>
<p>This is a static page. For the page with filters and selection, go to the <a href="index.html?page=compare">compare page</a>.</p>
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
            if band_data.swr_min.value is not None:
                params.append(f"swr_min={fmt_param(band_data.swr_min.value, 4)}")

        # Extract power parameter
        if antenna.powerPfwd_W.value is not None:
            params.append(f"Pfwd_W={antenna.powerPfwd_W.value}")

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
        for band in sorted(constants.BANDS.f_hz_by_band_name, key=_band_sort_key):
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

    def render(
        self, antenna_entries: list[loop_directories.AntennaPlusDirectory]
    ) -> None:
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
            overview_pictures = self._overview_pictures_from_field(
                antenna, entry.directory
            )
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
            for band in sorted(constants.BANDS.f_hz_by_band_name, key=_band_sort_key)
            if any(
                band in band_data_by_dir[entry.directory] for entry in antenna_entries
            )
        ]

        body = ""
        for band_index, band in enumerate(available_bands):
            header_overview_links_band = (
                "<tr><th style='font-weight: normal;'>Links</th><th></th>"
            )
            for entry in antenna_entries:
                filename_html_antenna = (
                    entry.directory / "generated_antenna.html"
                ).resolve()
                filename_relative = self._get_relative_path(filename_html_antenna)
                band_data = band_data_by_dir[entry.directory].get(band)
                link_html = f"<a href='{html.escape(filename_relative, quote=True)}'>description</a>"
                if band_data is not None:
                    calculator_url = self._build_calculator_url(
                        entry.antenna, band_data
                    )
                    link_html += (
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
            for label, unit, tooltip, fmt, source_fmt in _ROWS:
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
                    source_text = source_fmt(entry.antenna, band_data) or ""
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

    def close(self, body_only: bool) -> str:
        author_footer = html.escape(constants.AUTOR_STR)
        html_suffix = f"""
    <p style='margin-top: 2rem; font-size: 0.9rem; color: #666;'>{author_footer}</p>
</body>
</html>
"""
        html_body = "".join(self.sections)
        if body_only:
            return html_body

        return f"{self.html_prefix}{html_body}{html_suffix}"


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
