"""Build antenna efficiency overview and related measurement rows."""

from __future__ import annotations

import html
import os
import pathlib
import re
from dataclasses import dataclass
from typing import Callable

from antennenvergleich.datatypes_s1p import ValuesDataFile
from magloop_field.calculations import AntennaCalculator as FieldAntennaCalculator

from .constants import BANDS
from .constants_s1p import (
    CAP_VALUES_TAGS,
    RESULTS_SUBDIR,
    SMITH_SUFFIX,
    SVG_EXTENSION,
    SWR_SUFFIX,
    VALUES_SUFFIX,
)


@dataclass(frozen=True)
class EfficiencyOverviewResult:
    table_rows: str
    chart_table_rows: str
    first_values_with_model: ValuesDataFile | None
    efficiency_overview_html: str


def _is_cap_measurement_name(name: str) -> bool:
    name_u = name.upper()
    return any(tag in name_u for tag in CAP_VALUES_TAGS)


def build_efficiency_overview(
    output_subdir: pathlib.Path,
    antenna_dir: pathlib.Path,
    antenna_data: object | None,
    read_values_file: Callable[[pathlib.Path], ValuesDataFile],
) -> EfficiencyOverviewResult:
    """Build values table rows, chart rows, and efficiency overview HTML."""
    values_files = sorted(
        p
        for p in output_subdir.glob(f"*{VALUES_SUFFIX}.py")
        if not _is_cap_measurement_name(p.stem)
    )

    def fmt(value: object, decimals: int | None) -> str:
        if value is None:
            return "-"
        if isinstance(value, (int, float)):
            if decimals is None:
                return f"{value:.0f}"
            return f"{value:.{decimals}f}"
        return str(value)

    band_centers_mhz: list[tuple[str, float]] = sorted(
        ((name, f_hz / 1e6) for name, f_hz in BANDS.f_hz_by_band_name.items()),
        key=lambda item: item[1],
    )
    band_order = [name for name, _ in band_centers_mhz]

    def infer_band_label_from_f_hz(f_hz: float | None, fallback: str) -> str:
        if isinstance(f_hz, (int, float)) and f_hz > 0:
            f_mhz = f_hz / 1e6
            return min(band_centers_mhz, key=lambda item: abs(item[1] - f_mhz))[0]

        match = re.search(r"_(\d+(?:[\.,]\d+)?)MHz$", fallback)
        if match:
            f_mhz = float(match.group(1).replace(",", "."))
            return min(band_centers_mhz, key=lambda item: abs(item[1] - f_mhz))[0]
        return fallback

    def infer_band_label(values: ValuesDataFile, base_stem: str) -> str:
        f_hz = values.model.f0_Hz if values.model is not None else None
        return infer_band_label_from_f_hz(f_hz, base_stem)

    rows: list[str] = []
    chart_rows: list[str] = []
    band_data_rows: list[dict[str, object]] = []
    first_values_with_model: ValuesDataFile | None = None
    for values_path in values_files:
        values = read_values_file(values_path)
        if first_values_with_model is None and values.model is not None:
            first_values_with_model = values
        bswr = values.model.BSWR2_62_Hz if values.model else None
        alpha = values.model.alpha_db if values.model else None
        tau_ns = values.model.tau_s * 1e9 if values.model else None
        f0_hz = values.model.f0_Hz if values.model else None
        eta_ant = values.swr_values.eta_swr_ant
        swr_min = values.swr_values.swr_min
        base_stem = values_path.stem.removesuffix(VALUES_SUFFIX)
        band_label = infer_band_label(values, base_stem)
        smith_name = f"{base_stem}{SMITH_SUFFIX}{SVG_EXTENSION}"
        swr_name = f"{base_stem}{SWR_SUFFIX}{SVG_EXTENSION}"
        smith_rel = pathlib.Path(os.path.relpath(output_subdir / smith_name, antenna_dir)).as_posix()
        swr_rel = pathlib.Path(os.path.relpath(output_subdir / swr_name, antenna_dir)).as_posix()

        band_data_rows.append(
            {
                "band": band_label,
                "file": values_path.name,
                "f0_mhz": (f0_hz / 1e6) if isinstance(f0_hz, (int, float)) else None,
                "bswr": bswr,
                "alpha": alpha,
                "tau_ns": tau_ns,
                "swr_min": swr_min,
                "eta_ant": eta_ant,
                "source_f": values.band_data.f_Hz.source if values.model else None,
                "source_bw": values.band_data.bw262_Hz.source if values.model else None,
                "source_swr": values.band_data.swr_min.source if values.model else None,
            }
        )

        rows.append(
            "<tr>"
            f"<td>{html.escape(values_path.name)}</td>"
            f"<td>{html.escape(fmt((f0_hz / 1e6) if isinstance(f0_hz, (int, float)) else None, 3))}</td>"
            f"<td>{html.escape(fmt((bswr / 1e3) if isinstance(bswr, (int, float)) else None, 1))}</td>"
            f"<td>{html.escape(fmt(alpha, 3))}</td>"
            f"<td>{html.escape(fmt(tau_ns, 2))}</td>"
            f"<td>{html.escape(fmt(swr_min, 2))}</td>"
            f"<td>{html.escape(fmt(eta_ant, 3))}</td>"
            "</tr>"
        )

        chart_rows.append(
            "<tr>"
            f"<td><h3>{html.escape(base_stem)}</h3>"
            f'<a href="{html.escape(smith_rel)}">'
            f'<img src="{html.escape(smith_rel)}" alt="{html.escape(base_stem)} smith"></a></td>'
            f"<td><h3>{html.escape(base_stem)}</h3>"
            f'<a href="{html.escape(swr_rel)}">'
            f'<img src="{html.escape(swr_rel)}" alt="{html.escape(base_stem)} swr"></a></td>'
            "</tr>"
        )

    if not band_data_rows and antenna_data is not None:
        for idx, band in enumerate(getattr(antenna_data, "bands", ()) or (), start=1):
            f_hz = getattr(getattr(band, "f_Hz", None), "value", None)
            bw_hz = getattr(getattr(band, "bw262_Hz", None), "value", None)
            swr_min = getattr(getattr(band, "swr_min", None), "value", None)
            band_label = infer_band_label_from_f_hz(
                float(f_hz) if isinstance(f_hz, (int, float)) else None,
                f"band_{idx}",
            )
            eta_ant = None
            if isinstance(swr_min, (int, float)) and swr_min > 0:
                eta_ant = 4.0 * float(swr_min) / ((1.0 + float(swr_min)) ** 2)

            band_data_rows.append(
                {
                    "band": band_label,
                    "file": "antennendaten.py",
                    "f0_mhz": (float(f_hz) / 1e6)
                    if isinstance(f_hz, (int, float))
                    else None,
                    "bswr": float(bw_hz) if isinstance(bw_hz, (int, float)) else None,
                    "alpha": None,
                    "tau_ns": None,
                    "swr_min": float(swr_min)
                    if isinstance(swr_min, (int, float))
                    else None,
                    "eta_ant": eta_ant,
                    "source_f": str(
                        getattr(getattr(band, "f_Hz", None), "source", "") or ""
                    ),
                    "source_bw": str(
                        getattr(getattr(band, "bw262_Hz", None), "source", "") or ""
                    ),
                    "source_swr": str(
                        getattr(getattr(band, "swr_min", None), "source", "") or ""
                    ),
                }
            )

    seen: dict[str, int] = {}
    band_columns: list[str] = []
    sorted_band_items = sorted(
        band_data_rows,
        key=lambda x: (
            band_order.index(str(x["band"])) if str(x["band"]) in band_order else 999,
            float(x["f0_mhz"]) if isinstance(x["f0_mhz"], (int, float)) else 0.0,
        ),
    )
    for item in sorted_band_items:
        base = str(item["band"])
        count = seen.get(base, 0) + 1
        seen[base] = count
        band_columns.append(base if count == 1 else f"{base} #{count}")

    def _fmt_local_r(v: float) -> str:
        av = abs(v)
        if av < 1e-5:
            return f"{v:.2e}"
        if av < 1e-3:
            return f"{v:.6f}"
        if av < 1e-2:
            return f"{v:.5f}"
        if av < 0.1:
            return f"{v:.4f}"
        return f"{v:.3f}"

    def _fmt_local_percent(v: float) -> str:
        av = abs(v)
        if av >= 100:
            return f"{v:.0f}"
        if av >= 10:
            return f"{v:.1f}"
        if av >= 1:
            return f"{v:.2f}"
        return f"{v:.3f}"

    def _calc_for_item(item: dict[str, object]) -> FieldAntennaCalculator | None:
        if antenna_data is None:
            return None
        f0_mhz = item.get("f0_mhz")
        bw_hz = item.get("bswr")
        swr_min = item.get("swr_min")
        if not all(isinstance(x, (int, float)) for x in (f0_mhz, bw_hz, swr_min)):
            return None
        try:
            return FieldAntennaCalculator(
                D_m=antenna_data.D_m.value,
                d_m=antenna_data.d_m.value,
                n=antenna_data.n.value if antenna_data.n.value is not None else 1,
                p_m=antenna_data.p_m.value or 0.0,
                swr_min=float(swr_min),
                f_Hz=float(f0_mhz) * 1e6,
                bw262_Hz=float(bw_hz),
                powerP_W=antenna_data.powerP_W.value,
            )
        except Exception:
            return None

    row_specs: list[tuple[str, str, str, str]] = [
        ("Frequency <i>f</i>", "MHz", "f", "Mittenfrequenz des betrachteten Bandes."),
        (
            "Bandwidth <i>B</i><sub>SWR=2.62</sub>",
            "kHz",
            "bw",
            "Bandbreite am Antenneneingang beim Kriterium SWR = 2.62.",
        ),
        ("Loop diameter <i>D</i>", "m", "D", "Äquivalenter Durchmesser der Loop."),
        (
            "Conductor diameter <i>d</i>",
            "m",
            "d",
            "Äquivalenter Leiterdurchmesser der Loop.",
        ),
        ("Loop count <i>n</i>", "1", "n", "Anzahl der Windungen der Schleife."),
        (
            "Power into antenna <i>P</i>",
            "W",
            "P",
            "Eingespeiste Leistung in die Antenne.",
        ),
        ("Inductance <i>L</i>", "H", "L", "Berechnete Induktivität der Loop."),
        (
            "Capacitance <i>C</i>",
            "F",
            "C",
            "Erforderliche Resonanzkapazität bei der Bandfrequenz.",
        ),
        (
            "Unloaded Q<sub>0</sub>",
            "1",
            "Q0",
            "Unbelastete Güte, aus f / Bandbreite abgeschätzt.",
        ),
        (
            "Damping resistance <i>R</i><sub>T</sub>",
            "Ohm",
            "RT",
            "Gesamter Dämpfungswiderstand des Resonanzkreises.",
        ),
        (
            "Radiation resistance <i>R</i><sub>R</sub>",
            "Ohm",
            "RR",
            "Äquivalenter Strahlungswiderstand der Antenne.",
        ),
        (
            "Loss resistance <i>R</i><sub>Loss</sub>",
            "Ohm",
            "RLoss",
            "Verlustwiderstand: R_T - R_R.",
        ),
        ("swr_min", "1", "swr_min", "Minimales SWR am Antenneneingang."),
        (
            "eta<sub>SWR_ant</sub>",
            "%",
            "eta_swr",
            "Anpassungswirkungsgrad aus swr_min: eta = 4*SWR/(1+SWR)^2.",
        ),
        (
            "<b>Antenna efficiency <i>η</i></b>",
            "<b>%</b>",
            "eta",
            "Gesamteffizienz: (R_R / R_T) * eta_SWR_ant.",
        ),
        (
            "Loop current <i>I</i>",
            "A",
            "I",
            "Strom im Hauptloop bei der Referenzleistung.",
        ),
        (
            "Loop voltage <i>U</i><sub>loop</sub>",
            "V",
            "U",
            "Spannung über dem Loop bei Resonanz.",
        ),
        (
            "Magnetic dipole moment <i>m</i>",
            "A m²",
            "m",
            "Magnetisches Dipolmoment des Loops.",
        ),
    ]

    def _value_source(
        item: dict[str, object], key: str, calc: FieldAntennaCalculator | None
    ) -> str:
        file_name = str(item.get("file") or "")
        if key == "D":
            if antenna_data is None:
                return file_name
            return str(getattr(antenna_data.D_m, "source", "") or "")
        if key == "d":
            if antenna_data is None:
                return file_name
            return str(getattr(antenna_data.d_m, "source", "") or "")
        if key == "n":
            if antenna_data is None:
                return file_name
            return str(getattr(antenna_data.n, "source", "") or "")
        if key == "f":
            return str(item.get("source_f") or file_name)
        if key == "bw":
            return str(item.get("source_bw") or file_name)
        if key == "swr_min":
            return str(item.get("source_swr") or file_name)
        if key == "eta_swr":
            return f"[{file_name}] Berechnet aus swr_min: eta = 4*SWR/(1+SWR)^2."
        if key == "P":
            if antenna_data is None:
                return file_name
            return str(getattr(antenna_data.powerP_W, "source", "") or file_name)
        if key in {"L", "C", "Q0", "RT", "RR", "RLoss", "eta", "I", "U", "m"}:
            return (
                f"[{file_name}] Berechnet aus Geometrie- und Messdaten."
                if calc is not None
                else file_name
            )
        return file_name

    def _format_value(calc: FieldAntennaCalculator | None, key: str) -> str:
        if calc is None:
            return "-"
        if key == "D":
            return f"{calc.D_m:.3f}"
        if key == "d":
            return f"{calc.d_m:.3f}"
        if key == "n":
            return f"{calc.n:.0f}"
        if key == "f":
            return f"{calc.f_Hz / 1e6:.3f}"
        if key == "bw":
            return f"{calc.bw262_Hz / 1e3:.1f}"
        if key == "P":
            return f"{calc.powerP_W:.0f}"
        if key == "L":
            return f"{calc.L_H:.2e}"
        if key == "C":
            return f"{calc.C_F:.2e}"
        if key == "Q0":
            return f"{calc.Q0:.0f}"
        if key == "RT":
            return _fmt_local_r(calc.RT_Ohm)
        if key == "RR":
            return _fmt_local_r(calc.RR_Ohm)
        if key == "RLoss":
            return _fmt_local_r(calc.RLoss_Ohm)
        if key == "swr_min":
            return f"{calc.swr_min:.2f}"
        if key == "eta_swr":
            return _fmt_local_percent(calc.eta_SWR_ant * 100)
        if key == "eta":
            return _fmt_local_percent(calc.eta * 100)
        if key == "I":
            return f"{calc.I_main_loop_A:.2f}"
        if key == "U":
            return f"{calc.U_loop_V:.0f}"
        if key == "m":
            return f"{calc.m_Am2:.3f}"
        return "-"

    pivot_row_list: list[str] = []
    if band_columns:
        band_cells = "".join(f"<td class='val'>{html.escape(label)}</td>" for label in band_columns)
        pivot_row_list.append(
            f"<tr class='band-row'><td>Band</td><td class='unit'></td>{band_cells}</tr>"
        )
    else:
        pivot_row_list.append(
            f"<tr><td colspan='3'>Keine Banddaten vorhanden ({html.escape(RESULTS_SUBDIR)} fehlt oder ist leer).</td></tr>"
        )
    merged_single_value_keys = {"D", "d", "n", "L"}
    for label_html, unit_html, key, tooltip in row_specs:
        row_cells: list[str] = []
        if key in merged_single_value_keys and sorted_band_items:
            first_item = sorted_band_items[0]
            first_calc = _calc_for_item(first_item)
            merged_val = _format_value(first_calc, key)
            merged_source = html.escape(_value_source(first_item, key, first_calc), quote=True)
            row_cells.append(
                f"<td class='val merged' colspan='{len(sorted_band_items)}' title='{merged_source}'>{html.escape(merged_val)}</td>"
            )
        else:
            for item in sorted_band_items:
                calc = _calc_for_item(item)
                val = _format_value(calc, key)
                css = "val"
                if key == "RLoss" and calc is not None and calc.RLoss_Ohm < 0:
                    css += " neg"
                if key == "eta" and calc is not None and (calc.eta * 100) > 100:
                    css += " neg"
                source_attr = html.escape(_value_source(item, key, calc), quote=True)
                row_cells.append(
                    f"<td class='{css}' title='{source_attr}'>{html.escape(val)}</td>"
                )
        tooltip_attr = html.escape(tooltip, quote=True)
        row_class = " class='eff-row'" if key == "eta" else ""
        pivot_row_list.append(
            f"<tr{row_class}><td title='{tooltip_attr}'>{label_html}</td><td class='unit'>{unit_html}</td>{''.join(row_cells)}</tr>"
        )
    pivot_rows = "\n".join(pivot_row_list)
    efficiency_overview_html = (
        "<h2>Antenna Efficiency Overview</h2>\n"
        '    <table class="compact">\n'
        "        <tbody>\n"
        f"{pivot_rows}\n"
        "        </tbody>\n"
        "    </table>"
    )

    return EfficiencyOverviewResult(
        table_rows="\n".join(rows),
        chart_table_rows="\n".join(chart_rows),
        first_values_with_model=first_values_with_model,
        efficiency_overview_html=efficiency_overview_html,
    )
