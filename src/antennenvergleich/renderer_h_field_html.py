import pathlib
import re
from collections.abc import Callable


def build_h_field_section_html(
    antenna_dir: pathlib.Path,
    antenna_root_dir: pathlib.Path,
    rewrite_local_links: Callable[[str, pathlib.Path, pathlib.Path], str],
) -> str:
    h_field_section_html = ""
    h_field_html_file = antenna_root_dir / "h_field" / "h_field.html"
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
            h_field_section_html = rewrite_local_links(
                h_field_section_html,
                fragment_dir=h_field_html_file.parent,
                destination_dir=antenna_dir,
            )
        except Exception as exc:  # pragma: no cover - optional section best effort
            print(
                f"Warnung: H-field-HTML konnte nicht geladen werden ({h_field_html_file}): {exc}"
            )

    return h_field_section_html
