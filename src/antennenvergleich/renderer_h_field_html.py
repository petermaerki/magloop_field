import dataclasses
import html
import pathlib
import re
from collections.abc import Callable

import jinja2

_H_FIELD_MEASUREMENTS_MARKER = "__H_FIELD_MEASUREMENTS_TABLE__"


@dataclasses.dataclass(frozen=True)
class HFieldSummaryRow:
    label: str
    value: str


@dataclasses.dataclass(frozen=True)
class HFieldPointRow:
    point: str
    x_m: str
    y_m: str
    z_m: str
    expected_a_m: str
    measured_a_m: str
    factor: str


@dataclasses.dataclass(frozen=True)
class HFieldFrequencySection:
    f_mhz: str
    summary_rows: list[HFieldSummaryRow]
    point_rows: list[HFieldPointRow]


@dataclasses.dataclass(frozen=True)
class HFieldMeasurements:
    sections: list[HFieldFrequencySection]


@dataclasses.dataclass(frozen=True)
class HFieldSectionContent:
    html_before_measurements: str
    html_after_measurements: str
    measurements: HFieldMeasurements


def _parse_h_field_measurements_html(measurements_html: str) -> HFieldMeasurements:
    section_pattern = re.compile(
        r"<h4>\s*f\s*=\s*([0-9.]+)\s*MHz\s*</h4>\s*"
        r"<table\s+class=['\"]h-field-summary['\"]>(.*?)</table>\s*"
        r"<table\s+class=['\"]measure-table['\"]>.*?<tbody>(.*?)</tbody>.*?</table>",
        flags=re.DOTALL,
    )
    summary_row_pattern = re.compile(
        r"<tr>\s*<td>(.*?)</td>\s*<td>(.*?)</td>\s*</tr>",
        flags=re.DOTALL,
    )
    point_row_pattern = re.compile(
        r"<tr>\s*"
        r"<td\s+class=['\"]point-col['\"]>(.*?)</td>\s*"
        r"<td>(.*?)</td>\s*"
        r"<td>(.*?)</td>\s*"
        r"<td>(.*?)</td>\s*"
        r"<td>(.*?)</td>\s*"
        r"<td>(.*?)</td>\s*"
        r"<td\s+class=['\"]hl-factor['\"]>(.*?)</td>\s*"
        r"</tr>",
        flags=re.DOTALL,
    )

    sections: list[HFieldFrequencySection] = []
    for match in section_pattern.finditer(measurements_html):
        f_mhz = match.group(1).strip()
        summary_table_html = match.group(2)
        points_table_html = match.group(3)

        summary_rows = [
            HFieldSummaryRow(
                label=html.unescape(row.group(1).strip()),
                value=html.unescape(row.group(2).strip()),
            )
            for row in summary_row_pattern.finditer(summary_table_html)
        ]
        point_rows = [
            HFieldPointRow(
                point=html.unescape(row.group(1).strip()),
                x_m=html.unescape(row.group(2).strip()),
                y_m=html.unescape(row.group(3).strip()),
                z_m=html.unescape(row.group(4).strip()),
                expected_a_m=html.unescape(row.group(5).strip()),
                measured_a_m=html.unescape(row.group(6).strip()),
                factor=html.unescape(row.group(7).strip()),
            )
            for row in point_row_pattern.finditer(points_table_html)
        ]
        sections.append(
            HFieldFrequencySection(
                f_mhz=f_mhz,
                summary_rows=summary_rows,
                point_rows=point_rows,
            )
        )

    return HFieldMeasurements(sections=sections)


def build_h_field_section_html(
    antenna_dir: pathlib.Path,
    antenna_root_dir: pathlib.Path,
    rewrite_local_links: Callable[[str, pathlib.Path, pathlib.Path], str],
    template_vars: dict[str, str] | None = None,
) -> HFieldSectionContent:
    h_field_html = ""
    h_field_measurements = HFieldMeasurements(sections=[])
    h_field_html_file = antenna_root_dir / "h_field" / "h_field.html"
    if h_field_html_file.is_file():
        h_field_html = h_field_html_file.read_text(encoding="utf-8")
        h_field_measurements_file = (
            h_field_html_file.parent / "h_field_measurements_generated.html"
        )
        if h_field_measurements_file.is_file():
            h_field_measurements = _parse_h_field_measurements_html(
                h_field_measurements_file.read_text(encoding="utf-8")
            )

        render_context: dict[str, object] = {
            "h_field_measurements_table_marker": _H_FIELD_MEASUREMENTS_MARKER,
        }
        if template_vars:
            render_context.update(template_vars)
        h_field_html = jinja2.Template(h_field_html).render(**render_context)

        h_field_html = rewrite_local_links(
            h_field_html,
            fragment_dir=h_field_html_file.parent,
            destination_dir=antenna_dir,
        )

    before, marker, after = h_field_html.partition(_H_FIELD_MEASUREMENTS_MARKER)
    if marker:
        return HFieldSectionContent(
            html_before_measurements=before,
            html_after_measurements=after,
            measurements=h_field_measurements,
        )

    return HFieldSectionContent(
        html_before_measurements=h_field_html,
        html_after_measurements="",
        measurements=h_field_measurements,
    )
