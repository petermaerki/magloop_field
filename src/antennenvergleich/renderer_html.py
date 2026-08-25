"""Generates compare.html — comparison table for magnetic loop antennas."""

import dataclasses
import html
import importlib
import math
import os
import pathlib
import re
from collections.abc import Callable
from urllib.parse import urlsplit, urlunsplit

import matplotlib.colors
from magloop_field.calculations import AntennaCalculator as FieldAntennaCalculator

from antennenvergleich import loop_directories
from antennenvergleich.antenna_calculations import (
    AntennaCalculator,
    _make_calc,
)
from antennenvergleich.constants import BANDS
from antennenvergleich.constants_s1p import (
    CAP_VALUES_TAGS,
    RESULTS_SUBDIR,
    SMITH_SUFFIX,
    SVG_EXTENSION,
    SWR_SUFFIX,
    VALUES_SUFFIX,
)
from antennenvergleich.datatypes import Antenna, BandData, VnaCalibration
from antennenvergleich.datatypes_s1p import AntennaModelFit, SwrValues, ValuesDataFile

# ── Constants (same as calculations.py) ───────────────────────────────────────
_C_LIGHT = 299_792_458.0  # m/s

BAND_ORDER = ["10m", "12m", "15m", "20m", "30m", "40m", "60m", "80m", "160m"]

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent
DIRECTORY_SRC = DIRECTORY_OF_THIS_FILE.parent

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


def _is_cap_measurement_name(name: str) -> bool:
    name_u = name.upper()
    return any(tag in name_u for tag in CAP_VALUES_TAGS)


def _read_values_file(filename_values_py: pathlib.Path) -> ValuesDataFile:
    """Load swr_values and model from a generated *_values.py file."""
    try:
        relative_py = filename_values_py.resolve().relative_to(DIRECTORY_SRC)
    except ValueError as exc:
        raise RuntimeError(
            f"{filename_values_py} liegt nicht unter {DIRECTORY_SRC}"
        ) from exc

    module_name = ".".join(relative_py.with_suffix("").parts)
    module = importlib.import_module(module_name)
    module = importlib.reload(module)

    swr_values = getattr(module, "swr_values", None)
    model = getattr(module, "model", None)

    if not isinstance(swr_values, SwrValues):
        raise TypeError(f"{filename_values_py.name}: swr_values hat unerwarteten Typ")
    if model is not None and not isinstance(model, AntennaModelFit):
        raise TypeError(f"{filename_values_py.name}: model hat unerwarteten Typ")

    return ValuesDataFile(swr_values=swr_values, model=model)


def _rewrite_local_links_in_html_fragment(
    html_fragment: str,
    fragment_dir: pathlib.Path,
    destination_dir: pathlib.Path,
) -> str:
    """Rewrite local src/href links in HTML so they resolve from destination_dir."""

    def _replace(match: re.Match[str]) -> str:
        attr = match.group(1)
        quote = match.group(2)
        url = match.group(3)
        parsed = urlsplit(url)

        # Keep absolute and special links untouched.
        if parsed.scheme or url.startswith("#") or url.startswith("/"):
            return match.group(0)

        rel_path = parsed.path
        if not rel_path:
            return match.group(0)

        abs_path = (fragment_dir / rel_path).resolve()
        rewritten_path = pathlib.Path(
            os.path.relpath(abs_path, destination_dir)
        ).as_posix()
        rewritten_url = urlunsplit(
            ("", "", rewritten_path, parsed.query, parsed.fragment)
        )
        return f"{attr}={quote}{rewritten_url}{quote}"

    return re.sub(r"(src|href)\s*=\s*([\"'])([^\"']+)\2", _replace, html_fragment)


def _load_html_fragments(
    antenna_data: object,
    attribute_name: str,
    base_dir: pathlib.Path,
    destination_dir: pathlib.Path,
    warning_label: str,
) -> str:
    rel_paths = tuple(getattr(antenna_data, attribute_name, ()) or ())
    fragments: list[str] = []
    for rel_path in rel_paths:
        path = (base_dir / rel_path).resolve()
        if not path.is_file():
            print(f"Warnung: {warning_label} nicht gefunden ({path})")
            continue
        try:
            fragment = path.read_text(encoding="utf-8")
            fragment = _rewrite_local_links_in_html_fragment(
                fragment,
                fragment_dir=path.parent,
                destination_dir=destination_dir,
            )
            fragments.append(fragment)
        except Exception as exc:  # pragma: no cover - best effort for optional section
            print(
                f"Warnung: {warning_label} konnte nicht geladen werden ({path}): {exc}"
            )
    return "\n".join(fragments)


def write_antenna_html(output_subdir: pathlib.Path) -> None:
    """Generate one antenna.html page for a given antenna results directory."""
    antenna_dir = output_subdir.parent
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
        values = _read_values_file(values_path)
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
        smith_rel = pathlib.Path(
            os.path.relpath(output_subdir / smith_name, antenna_dir)
        ).as_posix()
        swr_rel = pathlib.Path(
            os.path.relpath(output_subdir / swr_name, antenna_dir)
        ).as_posix()

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
            f"<td>{html.escape(fmt(bswr, None))}</td>"
            f"<td>{html.escape(fmt(alpha, 3))}</td>"
            f"<td>{html.escape(fmt(tau_ns, 2))}</td>"
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

    table_rows = "\n".join(rows)
    chart_table_rows = "\n".join(chart_rows)
    antenna_dir_name = output_subdir.parent.name

    antenna_data = None
    try:
        antenna_module = importlib.import_module(
            f"antennen.{antenna_dir_name}.antennendaten"
        )
        antenna_data = getattr(antenna_module, "ANTENNENDATEN", None)
    except Exception as exc:  # pragma: no cover - best effort for optional section
        print(
            f"Warnung: Antennendaten konnten nicht geladen werden ({antenna_dir_name}): {exc}"
        )

    environment_html_block = ""
    measurement_html_block = ""
    if antenna_data is not None:
        measurement_html_block = _load_html_fragments(
            antenna_data=antenna_data,
            attribute_name="measurement_html",
            base_dir=output_subdir.parent,
            destination_dir=antenna_dir,
            warning_label="measurement_html",
        )
        environment_html_block = _load_html_fragments(
            antenna_data=antenna_data,
            attribute_name="enviroment_html",
            base_dir=output_subdir.parent,
            destination_dir=antenna_dir,
            warning_label="enviroment_html",
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
                P_W=100.0,
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
        if key in {"P", "L", "C", "Q0", "RT", "RR", "RLoss", "eta", "I", "U", "m"}:
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
            return f"{calc.P_W:.0f}"
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
        band_cells = "".join(
            f"<td class='val'>{html.escape(label)}</td>" for label in band_columns
        )
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
            merged_source = html.escape(
                _value_source(first_item, key, first_calc), quote=True
            )
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

    inductivity_values_html = ""
    l_100p_h_value: float | None = None
    l_560p_h_value: float | None = None
    cap_nix_f_value: float | None = None
    inductance_file = output_subdir / "inductance.py"
    if inductance_file.exists():
        try:
            rel_py = inductance_file.resolve().relative_to(DIRECTORY_SRC)
            module_name = ".".join(rel_py.with_suffix("").parts)
            module = importlib.import_module(module_name)
            module = importlib.reload(module)

            l_100p_h = getattr(module, "L_100p_H", None)
            l_560p_h = getattr(module, "L_560p_H", None)
            cap_nix_f = getattr(module, "CAP_NIX_F", None)
            if isinstance(l_100p_h, (int, float)):
                l_100p_h_value = float(l_100p_h)
            if isinstance(l_560p_h, (int, float)):
                l_560p_h_value = float(l_560p_h)
            if isinstance(cap_nix_f, (int, float)) and not math.isnan(float(cap_nix_f)):
                cap_nix_f_value = float(cap_nix_f)
        except Exception as exc:  # pragma: no cover - best effort for optional section
            print(
                f"Warnung: Induktivitaet konnte nicht geladen werden ({inductance_file}): {exc}"
            )

    inductivity_text_html = ""
    inductivity_text_file = (
        DIRECTORY_SRC / "shared" / "inductivity" / "inductivity.html"
    )
    if inductivity_text_file.exists():
        try:
            inductivity_text_html = inductivity_text_file.read_text(encoding="utf-8")
            inductivity_text_html = _rewrite_local_links_in_html_fragment(
                inductivity_text_html,
                fragment_dir=inductivity_text_file.parent,
                destination_dir=antenna_dir,
            )
        except Exception as exc:  # pragma: no cover - best effort for optional section
            print(
                f"Warnung: Induktivitaets-Text konnte nicht geladen werden ({inductivity_text_file}): {exc}"
            )

    inductivity_pictures_html = ""
    try:
        picture_rel_paths = tuple(
            getattr(antenna_data, "inductivity_pictures", ()) or ()
        )
        if picture_rel_paths:
            image_tags: list[str] = []
            for picture_rel in picture_rel_paths:
                pic_path = output_subdir.parent / picture_rel
                if not pic_path.is_file():
                    continue
                rel_to_antenna = pathlib.Path(
                    os.path.relpath(pic_path, antenna_dir)
                ).as_posix()
                alt = html.escape(f"Inductivity picture: {pic_path.name}", quote=True)
                src = html.escape(rel_to_antenna, quote=True)
                image_tags.append(
                    f'<a href="{src}"><img class="inductivity-picture" src="{src}" alt="{alt}"></a>'
                )
            if image_tags:
                inductivity_pictures_html = (
                    '<div class="inductivity-pictures">'
                    + "".join(image_tags)
                    + "</div>"
                )
    except Exception as exc:  # pragma: no cover - best effort for optional section
        print(
            f"Warnung: Induktivitaets-Bilder konnten nicht geladen werden ({antenna_dir_name}): {exc}"
        )

    l_h_geometry_value: float | None = None
    l_h_geometry_str = "n/a"
    if antenna_data is not None and first_values_with_model is not None:
        try:
            calc = FieldAntennaCalculator(
                D_m=antenna_data.D_m.value,
                d_m=antenna_data.d_m.value,
                n=antenna_data.n.value if antenna_data.n.value is not None else 1,
                p_m=antenna_data.p_m.value or 0.0,
                swr_min=first_values_with_model.swr_values.swr_min,
                f_Hz=first_values_with_model.model.f0_Hz,
                bw262_Hz=first_values_with_model.model.BSWR2_62_Hz,
                P_W=100.0,
            )
            l_h_geometry_value = float(calc.L_H)
            l_h_geometry_str = f"{calc.L_H:.4g}"
        except Exception as exc:  # pragma: no cover - best effort for optional section
            print(
                f"Warnung: L_H aus Geometrie konnte nicht berechnet werden ({antenna_dir_name}): {exc}"
            )

    if (
        l_h_geometry_value is not None
        or l_100p_h_value is not None
        or l_560p_h_value is not None
        or cap_nix_f_value is not None
    ):

        def fmt_sig4(value: float | None) -> str:
            if isinstance(value, (int, float)):
                return f"{value:.4g}"
            return "n/a"

        def deviation_percent(measured: float | None, reference: float | None) -> str:
            if measured is None or reference is None or reference == 0:
                return "n/a"
            return f"{((measured - reference) / reference * 100.0):+.0f}%"

        def highlight_deviation_text(text: str) -> str:
            escaped = html.escape(text)
            if text in {"+4%", "+6%"}:
                return f"<span class='hl-yellow'>{escaped}</span>"
            return escaped

        def highlight_inductance_value_text(value: float | None) -> str:
            return f"<span class='hl-yellow'>{html.escape(fmt_sig4(value))}</span>"

        rows_html: list[str] = []
        if l_h_geometry_value is not None:
            rows_html.append(
                "<tr>"
                "<td>L</td>"
                "<td class='unit'>H</td>"
                f"<td class='val'>{highlight_inductance_value_text(l_h_geometry_value)}</td>"
                "<td>calculated from geometry of the main loop</td>"
                "</tr>"
            )

        if l_100p_h_value is not None:
            dev_100 = deviation_percent(l_100p_h_value, l_h_geometry_value)
            dev_100_html = highlight_deviation_text(dev_100)
            rows_html.append(
                "<tr>"
                "<td>L<sub>100</sub></td>"
                "<td class='unit'>H</td>"
                f"<td class='val'>{highlight_inductance_value_text(l_100p_h_value)}</td>"
                f"<td>derived from the resonance frequencies f<sub>OFF</sub> and f<sub>100</sub><br>deviation {dev_100_html} vs L</td>"
                "</tr>"
            )
        if l_560p_h_value is not None:
            dev_560 = deviation_percent(l_560p_h_value, l_h_geometry_value)
            dev_560_html = highlight_deviation_text(dev_560)
            rows_html.append(
                "<tr>"
                "<td>L<sub>560</sub></td>"
                "<td class='unit'>H</td>"
                f"<td class='val'>{highlight_inductance_value_text(l_560p_h_value)}</td>"
                f"<td>derived from the resonance frequencies f<sub>OFF</sub> and f<sub>560</sub><br>deviation {dev_560_html} vs L</td>"
                "</tr>"
            )

        if cap_nix_f_value is not None:
            rows_html.append(
                "<tr>"
                "<td>C<sub>NIX</sub></td>"
                "<td class='unit'>As/V</td>"
                f"<td class='val'>{html.escape(fmt_sig4(cap_nix_f_value))}</td>"
                "<td>derived from using L<sub>100</sub>, f<sub>OFF</sub>, and f<sub>NIX</sub><br>estimated parasitic capacitance of switches and wiring; expected value 1 ... 2 pF</td>"
                "</tr>"
            )

        deviations = []
        for measured in (l_100p_h_value, l_560p_h_value):
            if measured is not None and l_h_geometry_value not in (None, 0):
                deviations.append(
                    (measured - l_h_geometry_value) / l_h_geometry_value * 100.0
                )

        summary_html = ""
        if deviations:
            max_deviation = max(deviations, key=lambda value: abs(value))
            max_deviation_text = f"{max_deviation:+.0f}%"
            max_deviation_html = highlight_deviation_text(max_deviation_text)
            summary_html = (
                "<p>"
                "The maximum deviation between L and the capacitor-based L<sub>1x</sub> values "
                f"is {max_deviation_html}. "
                "This is considered a small deviation and is accepted. "
                "L is used for the calculations of the antenna efficiency."
                "</p>"
            )

        inductivity_values_html = (
            '<table class="compact">'
            "<tbody>"
            f"{''.join(rows_html)}"
            "</tbody>"
            "</table>"
            f"{summary_html}"
        )

    environment_section_html = ""
    if environment_html_block.strip():
        environment_section_html = f"<h2>Enviroment</h2>\n{environment_html_block}"

    measurement_section_html = ""
    if measurement_html_block.strip():
        measurement_section_html = (
            f"<h2>Measurement Info</h2>\n{measurement_html_block}"
        )

    vna_calibration_html = ""
    if antenna_data is not None:
        calibration_value = getattr(antenna_data, "vna_calibration", None)
        calibration_img = ""
        calibration_text_html = ""
        if calibration_value == VnaCalibration.ANTENNA_FEED_POINT:
            calibration_img = "fusspunkt_vna.svg"
            calibration_text_html = (
                "The VNA calibration was done at the antenna feed point: green line.<br>"
                "Common-mode choke at the antenna: "
                '<a href="http://www.positron.ch/rf/choke_simple">'
                "positron.ch/rf/choke_simple"
                "</a>.<br>"
                "Used cables: 80 cm RG400 (including the choke) and 10 m LMR195."
            )
        elif calibration_value == VnaCalibration.AT_VNA:
            calibration_img = "kabel_vna.svg"
            calibration_text_html = (
                "The VNA calibration was done directly at the VNA: green line. "
                "The cable influence was measured and removed."
            )

        if calibration_img and calibration_text_html:
            calibration_path = (
                DIRECTORY_SRC / "shared" / "vna_schematic" / calibration_img
            )
            if calibration_path.is_file():
                rel_to_antenna = pathlib.Path(
                    os.path.relpath(calibration_path, antenna_dir)
                ).as_posix()
                src = html.escape(rel_to_antenna, quote=True)
                alt = html.escape(f"VNA calibration: {calibration_img}", quote=True)
                vna_calibration_html = (
                    f'<p><a href="{src}"><img class="vna-calibration-picture" src="{src}" alt="{alt}"></a><br>'
                    f"{calibration_text_html}</p>"
                )
            else:
                vna_calibration_html = f"<p>{calibration_text_html}</p>"

    measurements_section_html = ""
    if table_rows:
        measurements_section_html = (
            "<h2>VNA-measurements</h2>\n"
            "The antenna S11 parameters were measured with a VNA. The following values were derived from these measurements."
            f"{vna_calibration_html}"
            '<table class="compact">\n'
            "    <thead>\n"
            "        <tr>\n"
            "            <th>File</th>\n"
            "            <th>model_f0<br>MHz</th>\n"
            "            <th>model_BSWR2_62<br>Hz</th>\n"
            "            <th>model_alpha<br>db</th>\n"
            "            <th>model_tau<br>ns</th>\n"
            "            <th>eta_SWR_ant</th>\n"
            "        </tr>\n"
            "    </thead>\n"
            "    <tbody>\n"
            f"{table_rows}\n"
            "    </tbody>\n"
            "</table>"
        )

    inductivity_section_html = ""
    if inductivity_values_html or inductivity_pictures_html:
        inductivity_section_html = (
            "<h2>Inductance</h2>\n"
            f"{inductivity_text_html}\n"
            f"{inductivity_pictures_html}\n"
            '<p class="section-label"> </p>\n'
            f"{inductivity_values_html}"
        )

    h_field_section_html = ""
    h_field_html_file = output_subdir.parent / "h_field" / "h_field.html"
    if h_field_html_file.is_file():
        try:
            h_field_section_html = h_field_html_file.read_text(encoding="utf-8")
            h_field_measurements_file = (
                h_field_html_file.parent / "h_field_measurements.html"
            )
            if h_field_measurements_file.is_file():
                h_field_measurements_html = h_field_measurements_file.read_text(
                    encoding="utf-8"
                )
                # Preferred: replace explicit placeholder tag in h_field.html.
                # Accept any existing placeholder text between start/end tag.
                placeholder_pattern = (
                    r"<h-field-measurements\b[^>]*>[\s\S]*?</h-field-measurements>"
                )
                replaced = re.sub(
                    placeholder_pattern,
                    h_field_measurements_html,
                    h_field_section_html,
                    count=1,
                    flags=re.IGNORECASE,
                )
                if replaced != h_field_section_html:
                    h_field_section_html = replaced
                else:
                    # Backward-compatible fallback: replace old iframe/script include.
                    iframe_script_pattern = (
                        r"<iframe[^>]*id=[\"']h-field-measurements[\"'][^>]*>\s*</iframe>\s*"
                        r"<script>[\s\S]*?</script>"
                    )
                    replaced = re.sub(
                        iframe_script_pattern,
                        h_field_measurements_html,
                        h_field_section_html,
                        count=1,
                    )
                    if replaced != h_field_section_html:
                        h_field_section_html = replaced
                    else:
                        h_field_section_html += "\n" + h_field_measurements_html
            h_field_section_html = _rewrite_local_links_in_html_fragment(
                h_field_section_html,
                fragment_dir=h_field_html_file.parent,
                destination_dir=antenna_dir,
            )
        except Exception as exc:  # pragma: no cover - optional section best effort
            print(
                f"Warnung: H-field-HTML konnte nicht geladen werden ({h_field_html_file}): {exc}"
            )

    diagrams_section_html = ""
    if chart_table_rows:
        diagrams_section_html = (
            "<p> </p>"
            "<p>The following diagrams: red points = measured values; green line = fitted model.</p>"
            '<table class="charts">\n'
            "    <thead>\n"
            "        <tr>\n"
            "            <th>Smith</th>\n"
            "            <th>SWR</th>\n"
            "        </tr>\n"
            "    </thead>\n"
            "    <tbody>\n"
            f"{chart_table_rows}\n"
            "    </tbody>\n"
            "</table>"
        )

    antenna_image_html = ""
    try:
        antenna_pictures = tuple(getattr(antenna_data, "overview_pictures", ()) or ())
        for picture_rel in antenna_pictures:
            pic_path = output_subdir.parent / picture_rel
            if not pic_path.is_file():
                continue
            rel_to_antenna = pathlib.Path(
                os.path.relpath(pic_path, antenna_dir)
            ).as_posix()
            src = html.escape(rel_to_antenna, quote=True)
            alt = html.escape(f"Overview picture: {pic_path.name}", quote=True)
            antenna_image_html = f'<p><a href="{src}"><img class="overview-antenna-picture" src="{src}" alt="{alt}"></a></p>'
            break
    except Exception:
        antenna_image_html = ""

    info_str_line = "-"
    info_conductor_line = "-"
    info_capacitor_line = "-"
    info_enviroment_line = "-"
    info_thanks_line = ""
    if antenna_data is not None:
        info_str_line = str(getattr(antenna_data, "info_str", "") or "-")
        info_conductor_line = str(
            getattr(antenna_data, "info_conductor_str", "") or "-"
        )
        info_capacitor_line = str(
            getattr(antenna_data, "info_capacitor_str", "") or "-"
        )
        info_enviroment_line = str(
            getattr(antenna_data, "info_enviroment_str", "") or "-"
        )
        info_thanks_line = str(
            getattr(antenna_data, "info_thanks_str", "") or ""
        ).strip()

    info_lines = [
        f"Info: {html.escape(info_str_line)}",
        f"Conductor: {html.escape(info_conductor_line)}",
        f"Capacitor: {html.escape(info_capacitor_line)}",
        f"Enviroment: {html.escape(info_enviroment_line)}",
    ]
    if info_thanks_line:
        info_lines.append(f"Thanks: {html.escape(info_thanks_line)}")

    info_block_html = f"<p>{'<br>'.join(info_lines)}</p>"

    header_title = antenna_dir_name
    if antenna_data is not None:
        brand = str(getattr(antenna_data, "selection_brand", "") or "").strip()
        name = str(getattr(antenna_data, "selection_name", "") or "").strip()
        location = str(getattr(antenna_data, "selection_location", "") or "").strip()
        header_parts = [part for part in (brand, name, location) if part]
        if header_parts:
            header_title = " ".join(header_parts)

    compare_overview_path = DIRECTORY_OF_THIS_FILE / "compare.html"
    compare_overview_rel = pathlib.Path(
        os.path.relpath(compare_overview_path, antenna_dir)
    ).as_posix()
    compare_overview_link_html = (
        f"<p>All antennas overview: "
        f'<a href="{html.escape(compare_overview_rel, quote=True)}">'
        f"compare.html</a></p>"
    )

    doc = f"""<!-- Automatically generated file by run_2_html.py. Do not edit manually. -->
<!doctype html>
<html lang=\"de\"> 
<head>
    <meta charset=\"utf-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
    <title>{html.escape(antenna_dir_name)} - antenna</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 1.5rem; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ccc; vertical-align: top; padding: 0.18rem 0.35rem; text-align: left; line-height: 1.15; }}
        th {{ background: #f4f4f4; }}
        td.unit {{ white-space: nowrap; }}
        td.val {{ text-align: right; }}
        td.merged {{ text-align: center; }}
        td.neg {{ background: #ffcccc; }}
        tr.band-row td {{ background: #fff59d; font-weight: 600; }}
        tr.eff-row td {{ background: #fff59d; }}
        tr.eff-row td.neg {{ background: #ffcccc; }}
        table.compact {{ width: auto; }}
        table.charts {{ width: auto; }}
        table.charts td {{ width: auto; vertical-align: top; }}
        table.charts img {{ width: 100%; max-width: 400px; height: auto; border: 1px solid #ddd; }}
        h2 {{ margin-top: 2rem; }}
        h3 {{ font-size: 1rem; margin: 0 0 0.5rem 0; }}
        p.section-label {{ margin: 1rem 0 0.5rem 0; font-weight: 400; }}
        pre {{ background: #f8f8f8; border: 1px solid #ddd; padding: 0.8rem; white-space: pre-wrap; }}
        div.inductivity-pictures {{ display: grid; gap: 0.8rem; }}
        img.inductivity-picture {{ width: 100%; max-width: 400px; height: auto; border: 1px solid #ddd; }}
        img.vna-calibration-picture {{ width: 100%; max-width: 200px; height: auto; border: 1px solid #ddd; }}
        img.overview-antenna-picture {{ width: auto; max-width: 300pt; height: auto; max-height: 500px; border: 1px solid #ddd; }}
        .hl-yellow {{ background: #fff59d; padding: 0 0.15rem; }}
    </style>
</head>
<body>
    <h1>{html.escape(header_title)}</h1>
    {antenna_image_html}
    {info_block_html}
    <h2>Antenna Efficiency Overview</h2>
    <table class=\"compact\">
        <tbody>
{pivot_rows}
        </tbody>
    </table>
    {measurement_section_html}
    {environment_section_html}
    {measurements_section_html}
    {diagrams_section_html}
    {inductivity_section_html}
    {h_field_section_html}
    {compare_overview_link_html}
</body>
</html>
"""
    (antenna_dir / "antenna.html").write_text(doc)


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
        lambda c: f"{c.bw262_Hz / 1e3:.1f}",
    ),
    (
        "Power into antenna <i>P</i>",
        "W",
        "Eingespeiste Leistung in die Antenne.",
        lambda c: f"{c.P_W:.0f}",
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
_CSS = """
body { font-family: Arial, sans-serif; }
table { border-collapse: collapse; }
td, th { border: 1px solid #ccc; vertical-align: top; padding-left: 6px; padding-right: 6px; text-align: left; }
td.unit { white-space: nowrap; }
td.val { text-align: right; }
td.miss { color: #999; }
td.neg { background: #ffcccc; }
img.overview-picture { width: auto; max-width: 110px; height: auto; max-height: 120px; display: block; }
div.overview-pictures { display: grid; gap: 6px; }
"""


class HtmlRenderer:
    def __init__(self) -> None:
        self.sections: list[str] = []
        self.html_prefix = f"""<!-- Automatically generated file by run_2_html.py. Do not edit manually. -->

<!DOCTYPE html>
<html lang=\"de\">
<head>
    <meta charset=\"utf-8\">
    <title>Magnetic Loop Antenna Compare</title>
    <style>{_CSS}</style>
</head>
<body>
<h2>Magnetic Loop Antenna Compare</h2>
<img src="magnetic_loops_compare_eta_f.svg" alt="Antenna efficiency eta over frequency" style="max-width: 100%; height: auto; display: block; margin-bottom: 12px;">
"""

    @staticmethod
    def _overview_pictures_from_field(item: "BandAntenna") -> list[str]:
        files: list[str] = []
        for rel in item.antenna.overview_pictures:
            rel_clean = rel.strip()
            if not rel_clean:
                continue
            candidate = (item.antenna_dir / rel_clean).resolve()
            if not candidate.is_file():
                continue
            rel_to_html = pathlib.Path(
                os.path.relpath(candidate, DIRECTORY_OF_THIS_FILE)
            ).as_posix()
            files.append(rel_to_html)
        return files

    def render(self, band: str, antennas_in_band: list["BandAntenna"]) -> None:
        if not antennas_in_band:
            return

        header_brand = "<tr><th style='font-weight: normal;'>Brand</th><th></th>"
        header_names = "<tr><th style='font-weight: normal;'>Name</th><th></th>"
        header_calls = "<tr><th style='font-weight: normal;'>Location</th><th></th>"
        header_overview_links = (
            "<tr><th style='font-weight: normal;'>Links</th><th></th>"
        )
        header_overview_pictures = (
            "<tr><th style='font-weight: normal;'>Picture</th><th></th>"
        )
        for item in antennas_in_band:
            tooltip_text = _antenna_info_tooltip(item.antenna)
            tooltip_attr = html.escape(tooltip_text, quote=True)
            brand_html = html.escape(item.antenna.selection_brand)
            name_html = html.escape(item.antenna.selection_name)
            location_html = html.escape(item.antenna.selection_location)
            header_brand += f"<th style='font-weight: normal;' title='{tooltip_attr}'>{brand_html}</th>"
            header_names += f"<th style='font-weight: normal;' title='{tooltip_attr}'>{name_html}</th>"
            header_calls += f"<th style='font-weight: normal;'>{location_html}</th>"
            overview_path = (item.antenna_dir / "antenna.html").resolve()
            if overview_path.is_file():
                rel_overview = pathlib.Path(
                    os.path.relpath(overview_path, DIRECTORY_OF_THIS_FILE)
                ).as_posix()
                link_html = (
                    f"<a href='{html.escape(rel_overview, quote=True)}'>description</a>"
                    "<br>"
                    "<a href='https://petermaerki.github.io/magloop_field/'>calculator</a>"
                )
                header_overview_links += (
                    f"<th style='font-weight: normal;'>{link_html}</th>"
                )
            else:
                header_overview_links += "<th></th>"
            overview_pictures = self._overview_pictures_from_field(item)
            if not overview_pictures:
                header_overview_pictures += "<th></th>"
            else:
                images_html = ""
                for overview_picture in overview_pictures:
                    src = html.escape(overview_picture, quote=True)
                    alt = html.escape(
                        f"Overview picture {item.antenna.selection_brand} {item.antenna.selection_name} {item.antenna.selection_location}",
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
        header_overview_links += "</tr>"
        header_overview_pictures += "</tr>"
        header = (
            f"{header_brand}{header_names}{header_calls}"
            f"{header_overview_pictures}{header_overview_links}"
        )

        body = ""
        for label, unit, tooltip, fmt in _ROWS:
            is_rloss = "Loss" in label
            is_efficiency_row = "Antenna efficiency" in label
            unit_html = f"<b>{unit}</b>" if is_efficiency_row else unit
            tooltip_attr = html.escape(tooltip, quote=True)
            row = f"<td title='{tooltip_attr}'>{label}</td><td class='unit'>{unit_html}</td>"
            for item in antennas_in_band:
                calc = _make_calc(item.antenna, item.band_data)
                val = fmt(calc)
                if is_efficiency_row:
                    val = f"<b>{val}</b>"
                highlight_neg = is_rloss and calc.RLoss_Ohm < 0
                highlight_over_100_efficiency = (
                    is_efficiency_row and (calc.eta * 100) > 100
                )
                extra = (
                    " neg" if (highlight_neg or highlight_over_100_efficiency) else ""
                )
                source_text = _value_source(label, item.antenna, item.band_data) or ""
                source_attr = html.escape(source_text, quote=True)
                row += f"<td class='val{extra}' title='{source_attr}'>{val}</td>"
            body += f"<tr>{row}</tr>\n"

        section = (
            f"<h2>{band} Band</h2>\n"
            f"<table>\n"
            f"<thead>{header}</thead>\n"
            f"<tbody>{body}</tbody>\n"
            f"</table>\n"
        )
        self.sections.append(section)

    def close(self) -> str:
        html_suffix = """
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
    _COLORS = list(matplotlib.colors.TABLEAU_COLORS.values())
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
        self.out = DIRECTORY_OF_THIS_FILE / "magnetic_loops_compare_eta_f.svg"
        self._pw = self._W - self._ML - self._MR
        self._ph = self._H - self._MT - self._MB
        self._ETA_MAX = 1.0  # overwritten in render() from data

    def _px(self, f_Hz: float) -> float:
        lf = math.log10(f_Hz)
        lmin = math.log10(self._F_MIN_HZ)
        lmax = math.log10(self._F_MAX_HZ)
        return self._ML + (lf - lmin) / (lmax - lmin) * self._pw

    def _color_for_index(self, index: int) -> str:
        return self._COLORS[index % len(self._COLORS)]

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

    def _collect_data(
        self, antennas: list[Antenna]
    ) -> list[tuple[str, list[tuple[float, float]]]]:
        result = []
        for antenna in antennas:
            if antenna.D_m.value is None or antenna.d_m.value is None:
                continue
            pts: list[tuple[float, float]] = []
            for bd in antenna.bands:
                if bd.f_Hz.value is None or bd.bw262_Hz.value is None:
                    continue
                calc = _make_calc(antenna, bd)
                if calc.eta > 0:
                    pts.append((bd.f_Hz.value, calc.eta))
            pts.sort()
            if pts:
                result.append(
                    (
                        f"{antenna.selection_brand} {antenna.selection_name} {antenna.selection_location}",
                        pts,
                    )
                )
        result.sort(key=lambda item: item[0].casefold())
        return result

    def render(self, antennas: list[Antenna]) -> None:
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
        for idx, (_name, pts) in enumerate(data):
            buf += self._draw_series(pts, self._color_for_index(idx))
        buf += self._draw_legend(
            [(name, self._color_for_index(i)) for i, (name, _) in enumerate(data)]
        )
        buf.append("</svg>")
        self.out.write_text("\n".join(buf), encoding="utf-8")
        print(f"Written: {self.out}")

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
    _COLORS = list(matplotlib.colors.TABLEAU_COLORS.values())

    _W = 860
    _H = 520
    _ML = 85
    _MR = 230
    _MT = 40
    _MB = 65

    _ETA_MIN = 1.0e-5

    def __init__(self) -> None:
        self.out = DIRECTORY_OF_THIS_FILE / "magnetic_loops_compare_eta_DL.svg"
        self._pw = self._W - self._ML - self._MR
        self._ph = self._H - self._MT - self._MB
        self._ETA_MAX = 1.0
        self._X_MIN = 0.0
        self._X_MAX = 1.0

    def _px(self, x_value: float) -> float:
        return (
            self._ML + (x_value - self._X_MIN) / (self._X_MAX - self._X_MIN) * self._pw
        )

    def _color_for_index(self, index: int) -> str:
        return self._COLORS[index % len(self._COLORS)]

    def _py(self, eta: float) -> float:
        if eta <= 0:
            return self._MT + self._ph
        le = math.log10(eta)
        lmin = math.log10(self._ETA_MIN)
        lmax = math.log10(self._ETA_MAX)
        return self._MT + (1.0 - (le - lmin) / (lmax - lmin)) * self._ph

    def _collect_data(
        self, antennas: list[Antenna]
    ) -> list[tuple[str, list[tuple[float, float]]]]:
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
                result.append(
                    (
                        f"{antenna.selection_brand} {antenna.selection_name} {antenna.selection_location}",
                        pts,
                    )
                )
        result.sort(key=lambda item: item[0].casefold())
        return result

    def render(self, antennas: list[Antenna]) -> None:
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
        for idx, (_name, pts) in enumerate(data):
            buf += self._draw_series(pts, self._color_for_index(idx))
        buf += self._draw_legend(
            [(name, self._color_for_index(i)) for i, (name, _) in enumerate(data)]
        )
        buf.append("</svg>")
        self.out.write_text("\n".join(buf), encoding="utf-8")
        print(f"Written: {self.out}")

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
