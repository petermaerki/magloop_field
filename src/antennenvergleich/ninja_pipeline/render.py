"""Render Ninja pages from generated fragments and template placeholders."""

from __future__ import annotations

import html
import pathlib

from . import loader, sections


def render_ninja_page(antenna_dir: pathlib.Path, antenna_data: object | None) -> str:
    context = {
        "PAGE_TITLE": html.escape(f"{antenna_dir.name} - antenna"),
        "H1_TITLE": html.escape(sections.build_h1_title(antenna_dir, antenna_data)),
        "ANTENNA_CSS_HREF": "../../../static/css/style_antenna.css",
        "INFO_HTML": sections.build_info_html(antenna_data),
        "FIRST_IMAGE_HTML": sections.build_first_image_html(antenna_dir, antenna_data),
        "EFFICIENCY_OVERVIEW_HTML": loader.load_efficiency_overview_fragment(antenna_dir),
        "ENVIRONMENT_SECTION_HTML": sections.build_environment_section_html(antenna_dir),
        "MEASUREMENT_SECTION_HTML": sections.build_measurement_section_html(antenna_dir),
        "DIAGRAMS_SECTION_HTML": sections.build_diagrams_section_html(antenna_dir),
        "INDUCTANCE_SECTION_HTML": sections.build_inductance_section_html(antenna_dir),
        "H_FIELD_SECTION_HTML": sections.build_h_field_section_html(antenna_dir),
    }

    template = loader.load_template()
    for key, value in context.items():
        template = template.replace(f"{{{{{key}}}}}", value)
    return template


def generate_one(antenna_dir: pathlib.Path) -> pathlib.Path:
    antenna_data = loader.load_antenna_data(antenna_dir)
    html_text = render_ninja_page(antenna_dir=antenna_dir, antenna_data=antenna_data)
    output_file = antenna_dir / loader.NINJA_FILENAME
    output_file.write_text(html_text, encoding="utf-8")
    return output_file
