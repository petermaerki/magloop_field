"""Helpers for assembling legacy antenna page shell HTML blocks."""

from __future__ import annotations

import html
import os
import pathlib

from . import constants


def build_antenna_image_html(
    output_subdir: pathlib.Path,
    antenna_dir: pathlib.Path,
    antenna_data: object | None,
) -> str:
    """Return first available overview image block for the legacy page."""
    if antenna_data is None:
        return ""

    try:
        antenna_pictures = tuple(getattr(antenna_data, "overview_pictures", ()) or ())
        for picture_rel in antenna_pictures:
            pic_path = output_subdir.parent / picture_rel
            if not pic_path.is_file():
                continue
            rel_to_antenna = pathlib.Path(os.path.relpath(pic_path, antenna_dir)).as_posix()
            src = html.escape(rel_to_antenna, quote=True)
            alt = html.escape(f"Overview picture: {pic_path.name}", quote=True)
            return (
                f'<p><a href="{src}"><img class="overview-antenna-picture" '
                f'src="{src}" alt="{alt}"></a></p>'
            )
    except Exception:
        return ""

    return ""


def build_info_block_html(antenna_data: object | None) -> str:
    """Return legacy info paragraph with optional thanks line."""
    info_str_line = "-"
    info_conductor_line = "-"
    info_capacitor_line = "-"
    info_enviroment_line = "-"
    info_thanks_line = ""
    if antenna_data is not None:
        info_str_line = str(getattr(antenna_data, "info_str", "") or "-")
        info_conductor_line = str(getattr(antenna_data, "info_conductor_str", "") or "-")
        info_capacitor_line = str(getattr(antenna_data, "info_capacitor_str", "") or "-")
        info_enviroment_line = str(getattr(antenna_data, "info_enviroment_str", "") or "-")
        info_thanks_line = str(getattr(antenna_data, "info_thanks_str", "") or "").strip()

    info_lines = [
        f"Info: {html.escape(info_str_line)}",
        f"Conductor: {html.escape(info_conductor_line)}",
        f"Capacitor: {html.escape(info_capacitor_line)}",
        f"Enviroment: {html.escape(info_enviroment_line)}",
    ]
    if info_thanks_line:
        info_lines.append(f"Thanks: {html.escape(info_thanks_line)}")

    return f"<p>{'<br>'.join(info_lines)}</p>"


def build_header_title(antenna_dir_name: str, antenna_data: object | None) -> str:
    """Return title derived from selection metadata when available."""
    header_title = antenna_dir_name
    if antenna_data is not None:
        brand = str(getattr(antenna_data, "selection_brand", "") or "").strip()
        name = str(getattr(antenna_data, "selection_name", "") or "").strip()
        location = str(getattr(antenna_data, "selection_location", "") or "").strip()
        header_parts = [part for part in (brand, name, location) if part]
        if header_parts:
            header_title = " ".join(header_parts)
    return header_title


def build_compare_overview_link_html(antenna_dir: pathlib.Path) -> str:
    """Return relative link block to compare page."""
    compare_overview_path = constants.DIRECTORY_REPO / "index.html"
    compare_overview_rel = pathlib.Path(
        os.path.relpath(compare_overview_path.resolve(), antenna_dir.resolve())
    ).as_posix()
    return (
        f"<p>All antennas overview: "
        f'<a href="{html.escape(compare_overview_rel, quote=True)}?page=compare">'
        f"compare page</a></p>"
    )


def build_antenna_css_rel(antenna_dir: pathlib.Path) -> str:
    """Return relative href for legacy antenna CSS."""
    antenna_css_path = constants.DIRECTORY_REPO / "static/css/style_antenna.css"
    return pathlib.Path(
        os.path.relpath(antenna_css_path.resolve(), antenna_dir.resolve())
    ).as_posix()


def build_legacy_antenna_document(
    antenna_dir_name: str,
    antenna_css_rel: str,
    header_title: str,
    antenna_image_html: str,
    info_block_html: str,
    efficiency_overview_html: str,
    measurement_section_html: str,
    environment_section_html: str,
    measurements_section_html: str,
    diagrams_section_html: str,
    inductivity_section_html: str,
    h_field_section_html: str,
    compare_overview_link_html: str,
) -> str:
    """Compose the legacy full antenna page HTML document."""
    return f"""<!-- Automatically generated file by run_2_html.py. Do not edit manually. -->
<!doctype html>
<html lang=\"de\">
<head>
    <meta charset=\"utf-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
    <title>{html.escape(antenna_dir_name)} - antenna</title>
    <link rel=\"stylesheet\" href=\"{html.escape(antenna_css_rel, quote=True)}\">
</head>
<body>
    <h1>{html.escape(header_title)}</h1>
    {antenna_image_html}
    {info_block_html}
    {efficiency_overview_html}
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
