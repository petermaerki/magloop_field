import importlib
import os
import pathlib
import re
from urllib.parse import urlsplit, urlunsplit

import jinja2

from antennenvergleich import loop_directories
from antennenvergleich.datatypes import AntennaPlusDirectory, VnaCalibration
from antennenvergleich.datatypes_s1p import AntennaModelFit, SwrValues, ValuesDataFile

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
from .renderer_h_field_html import HFieldMeasurements, build_h_field_section_html
from .renderer_inductance_html import build_inductance_section_html
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
    template_vars: dict[str, str] | None = None,
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
            if template_vars:
                for key, value in template_vars.items():
                    fragment = fragment.replace(f"{{{{{key}}}}}", value)
            fragments.append(fragment)
        except Exception as exc:  # pragma: no cover - best effort for optional section
            print(
                f"Warnung: {warning_label} konnte nicht geladen werden ({path}): {exc}"
            )
    return "\n".join(fragments)


def _generate_inductance_section(
    output_subdir: pathlib.Path,
    antenna_dir: pathlib.Path,
    antenna_data: object | None,
    first_values_with_model: ValuesDataFile | None,
    antenna_dir_name: str,
) -> str:
    return build_inductance_section_html(
        output_subdir=output_subdir,
        antenna_dir=antenna_dir,
        antenna_data=antenna_data,
        first_values_with_model=first_values_with_model,
        antenna_dir_name=antenna_dir_name,
        rewrite_local_links=_rewrite_local_links_in_html_fragment,
    )


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
    build_html_block = ""
    template_vars_dict: dict[str, str] = {"vna_info": constants.VNA_INFO}
    if antenna_data is not None:
        raw_template_vars_dict = (
            getattr(antenna_data, "template_vars_dict", {}) or {}
        )
        template_vars_dict.update(
            {str(key): str(value) for key, value in raw_template_vars_dict.items()}
        )
        measurement_html_block = _load_html_fragments(
            antenna_data=antenna_data,
            attribute_name="measurement_html",
            base_dir=directory_s1p_results.parent,
            destination_dir=entry.directory,
            warning_label="measurement_html",
            template_vars=template_vars_dict,
        )
        environment_html_block = _load_html_fragments(
            antenna_data=antenna_data,
            attribute_name="enviroment_html",
            base_dir=directory_s1p_results.parent,
            destination_dir=entry.directory,
            warning_label="enviroment_html",
            template_vars=template_vars_dict,
        )
        build_html_block = _load_html_fragments(
            antenna_data=antenna_data,
            attribute_name="build_html",
            base_dir=directory_s1p_results.parent,
            destination_dir=entry.directory,
            warning_label="build_html",
            template_vars=template_vars_dict,
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

    efficiency_table = build_efficiency_table(
        band_data_rows=band_data_rows,
        band_order=band_order,
        antenna_data=antenna_data,
    )

    measurement_section_html = ""
    if measurement_html_block.strip():
        measurement_section_html = (
            f"<h2>Measurement Info</h2>\n{measurement_html_block}"
        )

    build_details_section_html = ""
    if build_html_block.strip():
        build_details_section_html = f"<h2>Build Details</h2>\n{build_html_block}"

    inductance_section_html = _generate_inductance_section(
        output_subdir=directory_s1p_results,
        antenna_dir=entry.directory,
        antenna_data=antenna_data,
        first_values_with_model=first_values_with_model,
        antenna_dir_name=antenna_dir_name,
    )

    environment_section_html = ""
    if environment_html_block.strip():
        environment_section_html = f"<h2>Enviroment</h2>\n{environment_html_block}"

    vna_calibration_mode = ""
    vna_calibration_href = ""
    if antenna_data is not None:
        calibration_value = getattr(antenna_data, "vna_calibration", None)
        calibration_img = ""
        if calibration_value == VnaCalibration.ANTENNA_FEED_POINT:
            vna_calibration_mode = VnaCalibration.ANTENNA_FEED_POINT.value
            calibration_img = "fusspunkt_vna.svg"
        elif calibration_value == VnaCalibration.AT_VNA:
            vna_calibration_mode = VnaCalibration.AT_VNA.value
            calibration_img = "kabel_vna.svg"

        if calibration_img:
            calibration_path = DIRECTORY_SRC / "shared" / "vna_schematic" / calibration_img
            if calibration_path.is_file():
                vna_calibration_href = pathlib.Path(
                    os.path.relpath(calibration_path, entry.directory)
                ).as_posix()

    vna_filelist_section = build_vna_filelist_section(vna_values_rows)
    vna_smith_section = build_vna_smith_section(vna_chart_rows)

    h_field_section = build_h_field_section_html(
        antenna_dir=entry.directory,
        antenna_root_dir=directory_s1p_results.parent,
        rewrite_local_links=_rewrite_local_links_in_html_fragment,
        template_vars=template_vars_dict,
    )
    h_field_section_before_html = h_field_section.html_before_measurements
    h_field_section_after_html = h_field_section.html_after_measurements
    h_field_measurements: HFieldMeasurements = h_field_section.measurements

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

    compare_overview_path = constants.DIRECTORY_REPO / "index.html"
    compare_overview_rel = pathlib.Path(
        os.path.relpath(compare_overview_path.resolve(), entry.directory.resolve())
    ).as_posix()
    compare_overview_href = f"{compare_overview_rel}?page=compare"

    template = env.get_template("antenna.jinja2")
    jinja_html = template.render(
        antenna=entry.antenna,
        antenna_css_rel=antenna_css_rel,
        efficiency_table=efficiency_table,
        build_details_section_html=build_details_section_html,
        measurement_section_html=measurement_section_html,
        environment_section_html=environment_section_html,
        vna_calibration_mode=vna_calibration_mode,
        vna_calibration_href=vna_calibration_href,
        vna_filelist_section=vna_filelist_section,
        vna_smith_section=vna_smith_section,
        inductance_section_html=inductance_section_html,
        h_field_section_before_html=h_field_section_before_html,
        h_field_section_after_html=h_field_section_after_html,
        h_field_measurements=h_field_measurements,
        vna_info=constants.VNA_INFO,
        compare_overview_href=compare_overview_href,
    )
    (entry.directory / "generated_antenna.html").write_text(
        jinja_html,
        encoding="utf-8",
    )


def generate_antenna_html_files() -> int:
    """Generate antenna.html files for all antennas."""
    generated = 0

    for entry in loop_directories.get_antennen_daten():
        write_antenna_html(entry)
        generated += 1
    return generated
