"""Section and metadata builders for Ninja page assembly."""

from __future__ import annotations

import html
import pathlib

from . import loader


def build_h1_title(antenna_dir: pathlib.Path, antenna_data: object | None) -> str:
    h1_title = antenna_dir.name
    if antenna_data is not None:
        parts = [
            str(getattr(antenna_data, "selection_brand", "") or "").strip(),
            str(getattr(antenna_data, "selection_name", "") or "").strip(),
            str(getattr(antenna_data, "selection_location", "") or "").strip(),
        ]
        parts = [part for part in parts if part]
        if parts:
            h1_title = " ".join(parts)
    return h1_title


def build_info_html(antenna_data: object | None) -> str:
    if antenna_data is None:
        return ""

    info_lines = [
        f"Info: {getattr(antenna_data, 'info_str', '-')}",
        f"Conductor: {getattr(antenna_data, 'info_conductor_str', '-')}",
        f"Capacitor: {getattr(antenna_data, 'info_capacitor_str', '-')}",
        f"Enviroment: {getattr(antenna_data, 'info_enviroment_str', '-')}",
    ]
    thanks = str(getattr(antenna_data, "info_thanks_str", "") or "").strip()
    if thanks:
        info_lines.append(f"Thanks: {thanks}")
    return "<p>" + "<br>".join(html.escape(line) for line in info_lines) + "</p>"


def build_first_image_html(antenna_dir: pathlib.Path, antenna_data: object | None) -> str:
    assert antenna_data is not None, (
        "run_3_ninja braucht ANTENNENDATEN fuer Bild-Rendering: "
        f"{antenna_dir}"
    )
    overview_pictures = tuple(getattr(antenna_data, "overview_pictures", ()) or ())
    assert overview_pictures, (
        "overview_pictures fehlt oder ist leer in ANTENNENDATEN: "
        f"{antenna_dir / 'antennendaten.py'}"
    )

    picture_rel = str(overview_pictures[0])
    picture_path = antenna_dir / picture_rel
    assert picture_path.is_file(), (
        "Erstes overview_pictures-Bild nicht gefunden: "
        f"{picture_path}"
    )

    src = html.escape(pathlib.Path(picture_rel).as_posix(), quote=True)
    alt = html.escape(f"Overview picture: {picture_path.name}", quote=True)
    return (
        f'<p><a href="{src}"><img class="overview-antenna-picture" src="{src}" alt="{alt}"></a></p>'
    )


def build_environment_section_html(antenna_dir: pathlib.Path) -> str:
    environment_html = loader.load_environment_fragment(antenna_dir)
    if not environment_html.strip():
        return ""
    return "<h2>Enviroment</h2>\n" + environment_html


def build_measurement_section_html(antenna_dir: pathlib.Path) -> str:
    vna_measurements_html = loader.load_vna_measurements_fragment(antenna_dir)
    if not vna_measurements_html.strip():
        return ""
    return "<h2>VNA-measurements</h2>\n" + vna_measurements_html


def build_diagrams_section_html(antenna_dir: pathlib.Path) -> str:
    diagrams_html = loader.load_diagrams_fragment(antenna_dir)
    if not diagrams_html.strip():
        return ""
    return "<h2>Diagrams</h2>\n" + diagrams_html


def build_inductance_section_html(antenna_dir: pathlib.Path) -> str:
    inductance_html = loader.load_inductance_fragment(antenna_dir)
    if not inductance_html.strip():
        return ""
    return inductance_html


def build_h_field_section_html(antenna_dir: pathlib.Path) -> str:
    h_field_html = loader.load_h_field_fragment(antenna_dir)
    if not h_field_html.strip():
        return ""
    h_field_intro_html = loader.load_shared_h_field_intro_html(antenna_dir)
    return "<h2>Cross-check H-field</h2>\n" + h_field_intro_html + "\n" + h_field_html
