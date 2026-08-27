"""Build and write per-antenna HTML section fragments for page generation."""

from __future__ import annotations

import html
import os
import pathlib

from antennenvergleich.datatypes import VnaCalibration

from .html_fragments import rewrite_local_links_in_html_fragment
from .output_filenames import (
    FILENAME_DIAGRAMS_FRAGMENT,
    FILENAME_ENVIRONMENT_FRAGMENT,
    FILENAME_H_FIELD_FRAGMENT,
    FILENAME_INDUCTANCE_FRAGMENT,
    FILENAME_VNA_MEASUREMENTS_FRAGMENT,
)

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent
DIRECTORY_SRC = DIRECTORY_OF_THIS_FILE.parent


def build_and_write_antenna_fragments(
    output_subdir: pathlib.Path,
    antenna_dir: pathlib.Path,
    antenna_data: object | None,
    table_rows: str,
    chart_table_rows: str,
    environment_html_block: str,
    measurement_html_block: str,
    inductivity_section_html: str,
) -> dict[str, str]:
    """Build legacy section HTML and write generated fragments used by Ninja pages."""

    environment_section_html = ""
    if environment_html_block.strip():
        environment_section_html = f"<h2>Enviroment</h2>\n{environment_html_block}"
    (antenna_dir / FILENAME_ENVIRONMENT_FRAGMENT).write_text(
        environment_html_block,
        encoding="utf-8",
    )

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
            calibration_path = DIRECTORY_SRC / "shared" / "vna_schematic" / calibration_img
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

    vna_measurements_body_html = ""
    if table_rows:
        vna_intro_html = ""
        vna_intro_file = (
            DIRECTORY_SRC / "shared" / "vna_schematic" / "vna_measurements_intro.html"
        )
        if vna_intro_file.is_file():
            vna_intro_html = vna_intro_file.read_text(encoding="utf-8")
            vna_intro_html = rewrite_local_links_in_html_fragment(
                vna_intro_html,
                fragment_dir=vna_intro_file.parent,
                destination_dir=antenna_dir,
            )

        vna_measurements_body_html = (
            f"{vna_intro_html}"
            f"{vna_calibration_html}"
            '<table class="compact">\n'
            "    <thead>\n"
            "        <tr>\n"
            "            <th>File</th>\n"
            "            <th>model_f0<br>MHz</th>\n"
            "            <th>model_BSWR2_62<br>kHz</th>\n"
            "            <th>model_alpha<br>db</th>\n"
            "            <th>model_tau<br>ns</th>\n"
            "            <th>SWR_min</th>\n"
            "            <th>eta_SWR_ant</th>\n"
            "        </tr>\n"
            "    </thead>\n"
            "    <tbody>\n"
            f"{table_rows}\n"
            "    </tbody>\n"
            "</table>"
        )
    measurements_section_html = ""
    if vna_measurements_body_html:
        measurements_section_html = (
            "<h2>VNA-measurements</h2>\n" + vna_measurements_body_html
        )
    (antenna_dir / FILENAME_VNA_MEASUREMENTS_FRAGMENT).write_text(
        vna_measurements_body_html,
        encoding="utf-8",
    )

    h_field_section_html = ""
    h_field_dir = output_subdir.parent / "h_field"
    h_field_body_file = h_field_dir / "h_field_body.html"
    h_field_measurements_file = h_field_dir / "h_field_measurements.html"
    shared_h_field_conclusion_file = (
        DIRECTORY_SRC / "shared" / "h_field" / "h_field_conclusion.html"
    )
    try:
        h_field_body_html = ""
        if h_field_body_file.is_file():
            h_field_body_html = h_field_body_file.read_text(encoding="utf-8")
            h_field_body_html = rewrite_local_links_in_html_fragment(
                h_field_body_html,
                fragment_dir=h_field_body_file.parent,
                destination_dir=antenna_dir,
            )

        h_field_measurements_html = ""
        if h_field_measurements_file.is_file():
            h_field_measurements_html = h_field_measurements_file.read_text(
                encoding="utf-8"
            )

        shared_h_field_conclusion_html = ""
        if shared_h_field_conclusion_file.is_file():
            shared_h_field_conclusion_html = shared_h_field_conclusion_file.read_text(
                encoding="utf-8"
            )
            shared_h_field_conclusion_html = rewrite_local_links_in_html_fragment(
                shared_h_field_conclusion_html,
                fragment_dir=shared_h_field_conclusion_file.parent,
                destination_dir=antenna_dir,
            )

        h_field_parts = [
            part
            for part in (
                h_field_body_html,
                h_field_measurements_html,
                shared_h_field_conclusion_html,
            )
            if part.strip()
        ]
        h_field_section_html = "\n".join(h_field_parts)
    except Exception as exc:  # pragma: no cover - optional section best effort
        print(
            "Warnung: H-field-Fragmente konnten nicht geladen werden "
            f"({h_field_dir}): {exc}"
        )
    (antenna_dir / FILENAME_H_FIELD_FRAGMENT).write_text(
        h_field_section_html,
        encoding="utf-8",
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
    (antenna_dir / FILENAME_DIAGRAMS_FRAGMENT).write_text(
        diagrams_section_html,
        encoding="utf-8",
    )

    (antenna_dir / FILENAME_INDUCTANCE_FRAGMENT).write_text(
        inductivity_section_html,
        encoding="utf-8",
    )

    return {
        "measurement_section_html": measurement_section_html,
        "environment_section_html": environment_section_html,
        "measurements_section_html": measurements_section_html,
        "diagrams_section_html": diagrams_section_html,
        "h_field_section_html": h_field_section_html,
    }
