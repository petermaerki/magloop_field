import html
import importlib
import math
import os
import pathlib
import re
from urllib.parse import urlsplit, urlunsplit

import jinja2

from antennenvergleich import loop_directories
from antennenvergleich.datatypes import AntennaPlusDirectory, VnaCalibration
from antennenvergleich.datatypes_s1p import AntennaModelFit, SwrValues, ValuesDataFile
from magloop_field.calculations import AntennaCalculator as FieldAntennaCalculator

from . import constants
from .constants import BANDS, DIRECTORY_SRC
from .constants_s1p import (
    CAP_VALUES_TAGS,
    DIRECTORY_S1P_RESULTS,
    SMITH_SUFFIX,
    SVG_EXTENSION,
    SWR_SUFFIX,
    VALUES_SUFFIX,
)
from .renderer_antenna_efficiency_table_html import build_efficiency_table
from .renderer_vna_filelist_html import build_vna_filelist_section
from .renderer_vna_smith_html import build_vna_smith_section

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent


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


def _generate_inductivity_section(
    output_subdir: pathlib.Path,
    antenna_dir: pathlib.Path,
    antenna_data: object | None,
    first_values_with_model: ValuesDataFile | None,
    antenna_dir_name: str,
) -> str:
    """Generate the complete inductivity section HTML.

    Returns the full inductivity section including header, or empty string if no data.
    """
    inductivity_values_html = ""
    inductivity_text_html = ""
    inductivity_pictures_html = ""

    l_100p_h_value: float | None = None
    l_560p_h_value: float | None = None
    cap_nix_f_value: float | None = None
    inductance_file = output_subdir / "inductance.py"

    if not inductance_file.exists():
        return ""

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

    inductivity_text_file = (
        DIRECTORY_SRC / "shared" / "inductivity" / "inductivity.html"
    )
    if inductance_file.exists():
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
                powerP_W=100.0,
            )
            l_h_geometry_value = float(calc.L_H)
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
                "<td>derived from using L<sub>100</sub>, f<sub>OFF</sub>, and f<sub>NIX</sub><br>estimated parasitic capacitance of switches and wiring; expected value 1 ... 5 pF</td>"
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

    # Assemble the complete section
    if inductivity_values_html or inductivity_pictures_html:
        return (
            "<h2>Inductance</h2>\n"
            f"{inductivity_text_html}\n"
            f"{inductivity_pictures_html}\n"
            '<p class="section-label"> </p>\n'
            f"{inductivity_values_html}"
        )

    return ""


def write_antenna_html(entry: AntennaPlusDirectory) -> None:
    """Generate one antenna.html page for a given antenna results directory."""
    directory_s1p_results = entry.directory / DIRECTORY_S1P_RESULTS

    directory_templates = pathlib.Path(__file__).with_suffix("")
    assert directory_templates.is_dir()

    antenna_css_path = constants.DIRECTORY_REPO / "static/css/style_antenna.css"
    antenna_css_rel = pathlib.Path(
        os.path.relpath(antenna_css_path.resolve(), entry.directory.resolve())
    ).as_posix()

    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(directory_templates),
        undefined=jinja2.StrictUndefined,
    )

    values_files = sorted(
        p
        for p in directory_s1p_results.glob(f"*{VALUES_SUFFIX}.py")
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

    vna_values_rows: list[dict[str, object]] = []
    vna_chart_rows: list[dict[str, str]] = []
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
            os.path.relpath(directory_s1p_results / smith_name, entry.directory)
        ).as_posix()
        swr_rel = pathlib.Path(
            os.path.relpath(directory_s1p_results / swr_name, entry.directory)
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

        vna_values_rows.append(
            {
                "file_name": values_path.name,
                "f0_mhz": (f0_hz / 1e6) if isinstance(f0_hz, (int, float)) else None,
                "bswr_khz": (bswr / 1e3) if isinstance(bswr, (int, float)) else None,
                "alpha_db": alpha,
                "tau_ns": tau_ns,
                "swr_min": swr_min,
                "eta_swr_ant": eta_ant,
            }
        )

        vna_chart_rows.append(
            {
                "label": base_stem,
                "smith_rel": smith_rel,
                "swr_rel": swr_rel,
            }
        )
    antenna_dir_name = directory_s1p_results.parent.name

    antenna_data = entry.antenna

    environment_html_block = ""
    measurement_html_block = ""
    if antenna_data is not None:
        measurement_html_block = _load_html_fragments(
            antenna_data=antenna_data,
            attribute_name="measurement_html",
            base_dir=directory_s1p_results.parent,
            destination_dir=entry.directory,
            warning_label="measurement_html",
        )
        environment_html_block = _load_html_fragments(
            antenna_data=antenna_data,
            attribute_name="enviroment_html",
            base_dir=directory_s1p_results.parent,
            destination_dir=entry.directory,
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

    efficency_table = build_efficiency_table(
        band_data_rows=band_data_rows,
        band_order=band_order,
        antenna_data=antenna_data,
    )

    measurement_section_html = ""
    if measurement_html_block.strip():
        measurement_section_html = (
            f"<h2>Measurement Info</h2>\n{measurement_html_block}"
        )

    inductivity_section_html = _generate_inductivity_section(
        output_subdir=directory_s1p_results,
        antenna_dir=entry.directory,
        antenna_data=antenna_data,
        first_values_with_model=first_values_with_model,
        antenna_dir_name=antenna_dir_name,
    )

    environment_section_html = ""
    if environment_html_block.strip():
        environment_section_html = f"<h2>Enviroment</h2>\n{environment_html_block}"

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
                "Used cables: 80 cm RG400 (including the choke) and 10 m LMR195.<br>"
                "The cable attenuation alpha and the cable delay tau in the following table should therefore be small."
            )
        elif calibration_value == VnaCalibration.AT_VNA:
            calibration_img = "kabel_vna.svg"
            calibration_text_html = (
                "The VNA calibration was done directly at the VNA: green line. "
                "The cable influence was measured and removed.<br>"
                "The cable attenuation alpha and the cable delay tau in the following table show the estimated cable values based on the VNA measurement."
            )

        if calibration_img and calibration_text_html:
            calibration_path = (
                DIRECTORY_SRC / "shared" / "vna_schematic" / calibration_img
            )
            if calibration_path.is_file():
                rel_to_antenna = pathlib.Path(
                    os.path.relpath(calibration_path, entry.directory)
                ).as_posix()
                src = html.escape(rel_to_antenna, quote=True)
                alt = html.escape(f"VNA calibration: {calibration_img}", quote=True)
                vna_calibration_html = (
                    f'<p><a href="{src}"><img class="vna-calibration-picture" src="{src}" alt="{alt}"></a><br>'
                    f"{calibration_text_html}</p>"
                )
            else:
                vna_calibration_html = f"<p>{calibration_text_html}</p>"

    vna_filelist_section = build_vna_filelist_section(vna_values_rows)
    vna_smith_section = build_vna_smith_section(vna_chart_rows)

    h_field_section_html = ""
    h_field_html_file = directory_s1p_results.parent / "h_field" / "h_field.html"
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
                destination_dir=entry.directory,
            )
        except Exception as exc:  # pragma: no cover - optional section best effort
            print(
                f"Warnung: H-field-HTML konnte nicht geladen werden ({h_field_html_file}): {exc}"
            )

    antenna_image_html = ""
    try:
        antenna_pictures = tuple(getattr(antenna_data, "overview_pictures", ()) or ())
        for picture_rel in antenna_pictures:
            pic_path = directory_s1p_results.parent / picture_rel
            if not pic_path.is_file():
                continue
            rel_to_antenna = pathlib.Path(
                os.path.relpath(pic_path, entry.directory)
            ).as_posix()
            src = html.escape(rel_to_antenna, quote=True)
            alt = html.escape(f"Overview picture: {pic_path.name}", quote=True)
            antenna_image_html = f'<p><a href="{src}"><img class="overview-antenna-picture" src="{src}" alt="{alt}"></a></p>'
            break
    except Exception:
        antenna_image_html = ""

    # info_str_line = "-"
    # info_conductor_line = "-"
    # info_capacitor_line = "-"
    # info_enviroment_line = "-"
    # info_thanks_line = ""
    # if antenna_data is not None:
    #     info_str_line = str(getattr(antenna_data, "info_str", "") or "-")
    #     info_conductor_line = str(
    #         getattr(antenna_data, "info_conductor_str", "") or "-"
    #     )
    #     info_capacitor_line = str(
    #         getattr(antenna_data, "info_capacitor_str", "") or "-"
    #     )
    #     info_enviroment_line = str(
    #         getattr(antenna_data, "info_enviroment_str", "") or "-"
    #     )
    #     info_thanks_line = str(
    #         getattr(antenna_data, "info_thanks_str", "") or ""
    #     ).strip()

    # info_lines = [
    #     f"Info: {html.escape(info_str_line)}",
    #     f"Conductor: {html.escape(info_conductor_line)}",
    #     f"Capacitor: {html.escape(info_capacitor_line)}",
    #     f"Enviroment: {html.escape(info_enviroment_line)}",
    # ]
    # if info_thanks_line:
    #     info_lines.append(f"Thanks: {html.escape(info_thanks_line)}")

    # info_block_html = f"<p>{'<br>'.join(info_lines)}</p>"

    header_title = antenna_dir_name
    if antenna_data is not None:
        brand = str(getattr(antenna_data, "selection_brand", "") or "").strip()
        name = str(getattr(antenna_data, "selection_name", "") or "").strip()
        location = str(getattr(antenna_data, "selection_location", "") or "").strip()
        header_parts = [part for part in (brand, name, location) if part]
        if header_parts:
            header_title = " ".join(header_parts)

    compare_overview_path = constants.DIRECTORY_REPO / "index.html"
    compare_overview_rel = pathlib.Path(
        os.path.relpath(compare_overview_path.resolve(), entry.directory.resolve())
    ).as_posix()
    compare_overview_link_html = (
        f"<p>All antennas overview: "
        f'<a href="{html.escape(compare_overview_rel, quote=True)}?page=compare">'
        f"compare page</a></p>"
    )

    template = env.get_template("antenna.jinja2")
    jinja_html = template.render(
        antenna=entry.antenna,
        antenna_css_rel=antenna_css_rel,
        efficency_table=efficency_table,
        measurement_section_html=measurement_section_html,
        vna_calibration_html=vna_calibration_html,
        vna_filelist_section=vna_filelist_section,
        vna_smith_section=vna_smith_section,
    )

    doc = f"""<!-- Automatically generated file by run_2_html.py. Do not edit manually. -->
<!doctype html>
<html lang=\"de\">
<head>
    <meta charset=\"utf-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
    <title>{html.escape(antenna_dir_name)} - antenna</title>
    <link rel="stylesheet" href="{html.escape(antenna_css_rel, quote=True)}">
</head>
<body>
    {jinja_html}
    <hr/>
    <h1>{html.escape(header_title)}</h1>
    {antenna_image_html}
    <info_block_html>
    {environment_section_html}
    {inductivity_section_html}
    {h_field_section_html}
    {compare_overview_link_html}
</body>
</html>
"""
    (entry.directory / "generated_antenna.html").write_text(doc)


def generate_antenna_html_files() -> int:
    """Generate antenna.html files for all antennas."""
    generated = 0

    for entry in loop_directories.get_antennen_daten():
        write_antenna_html(entry)
        generated += 1
    return generated
