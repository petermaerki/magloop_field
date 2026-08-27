"""Generate experimental per-antenna ninja pages in parallel to antenna_generated.html."""

import argparse
import html
import importlib
import pathlib
import re
from collections.abc import Iterable

from . import constants, renderer_html

NINJA_FILENAME = "antenna_ninja_generated.html"
TEMPLATE_FILE = (
    constants.DIRECTORY_OF_THIS_FILE / "templates" / "antenna_ninja.html"
)
SHARED_H_FIELD_INTRO_FILE = (
    constants.DIRECTORY_REPO / "src" / "shared" / "h_field" / "h_field_intro.html"
)


def _iter_antenna_dirs() -> Iterable[pathlib.Path]:
    antennas_root = constants.DIRECTORY_REPO / "src" / "antennen"
    for antenna_data_file in sorted(antennas_root.rglob("antennendaten.py")):
        if antenna_data_file.parent.name == "__pycache__":
            continue
        yield antenna_data_file.parent


def _load_antenna_data(antenna_dir: pathlib.Path) -> object | None:
    module_name = f"antennen.{antenna_dir.name}.antennendaten"
    try:
        module = importlib.import_module(module_name)
        module = importlib.reload(module)
    except Exception as exc:  # pragma: no cover - best effort for optional data
        print(
            f"Warnung: Antennendaten konnten nicht geladen werden ({module_name}): {exc}"
        )
        return None
    return getattr(module, "ANTENNENDATEN", None)


def _safe_read_text(path: pathlib.Path) -> str:
    if not path.is_file():
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except Exception as exc:  # pragma: no cover - best effort for optional files
        print(f"Warnung: Datei konnte nicht geladen werden ({path}): {exc}")
        return ""


def _load_template() -> str:
    template = _safe_read_text(TEMPLATE_FILE)
    if not template:
        raise FileNotFoundError(f"Template nicht gefunden oder leer: {TEMPLATE_FILE}")
    return template


def _load_efficiency_overview_fragment(antenna_dir: pathlib.Path) -> str:
    fragment_file = antenna_dir / renderer_html.FILENAME_ANTENNA_EFFICIENCY_TABLE
    assert fragment_file.is_file(), (
        "Efficiency-Fragment fehlt. Bitte zuerst run_2_html ausfuehren: "
        f"{fragment_file}"
    )
    fragment = fragment_file.read_text(encoding="utf-8")
    assert fragment.strip(), f"Efficiency-Fragment ist leer: {fragment_file}"
    return fragment.rstrip()


def _load_environment_fragment(antenna_dir: pathlib.Path) -> str:
    fragment_file = antenna_dir / renderer_html.FILENAME_ENVIRONMENT_FRAGMENT
    assert fragment_file.is_file(), (
        "Enviroment-Fragment fehlt. Bitte zuerst run_2_html ausfuehren: "
        f"{fragment_file}"
    )
    return fragment_file.read_text(encoding="utf-8")


def _load_vna_measurements_fragment(antenna_dir: pathlib.Path) -> str:
    fragment_file = antenna_dir / renderer_html.FILENAME_VNA_MEASUREMENTS_FRAGMENT
    assert fragment_file.is_file(), (
        "VNA-Fragment fehlt. Bitte zuerst run_2_html ausfuehren: "
        f"{fragment_file}"
    )
    return fragment_file.read_text(encoding="utf-8")


def _load_h_field_fragment(antenna_dir: pathlib.Path) -> str:
    fragment_file = antenna_dir / renderer_html.FILENAME_H_FIELD_FRAGMENT
    assert fragment_file.is_file(), (
        "H-field-Fragment fehlt. Bitte zuerst run_2_html ausfuehren: "
        f"{fragment_file}"
    )
    return fragment_file.read_text(encoding="utf-8")


def _strip_shared_h_field_intro(h_field_html: str) -> str:
    # Keep shared intro text in template; drop duplicated per-antenna copy if present.
    pattern = (
        r"^\s*<h2>Cross-check H-field</h2>\s*"
        r"<p>The H-field can be calculated under free-space conditions\.[\s\S]*?</p>\s*"
        r"<p>The H-field is measured with a small measurement loop\.[\s\S]*?</p>\s*"
    )
    return re.sub(pattern, "", h_field_html, count=1)


def _load_shared_h_field_intro_html(antenna_dir: pathlib.Path) -> str:
    assert SHARED_H_FIELD_INTRO_FILE.is_file(), (
        "Shared H-field-Intro fehlt: "
        f"{SHARED_H_FIELD_INTRO_FILE}"
    )
    intro_html = SHARED_H_FIELD_INTRO_FILE.read_text(encoding="utf-8")
    assert intro_html.strip(), (
        "Shared H-field-Intro ist leer: "
        f"{SHARED_H_FIELD_INTRO_FILE}"
    )
    return renderer_html._rewrite_local_links_in_html_fragment(
        intro_html,
        fragment_dir=SHARED_H_FIELD_INTRO_FILE.parent,
        destination_dir=antenna_dir,
    )


def _render_ninja_page(antenna_dir: pathlib.Path, antenna_data: object | None) -> str:
    page_title = f"{antenna_dir.name} - antenna"
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

    info = ""
    if antenna_data is not None:
        info_lines = [
            f"Info: {getattr(antenna_data, 'info_str', '-')}",
            f"Conductor: {getattr(antenna_data, 'info_conductor_str', '-')}",
            f"Capacitor: {getattr(antenna_data, 'info_capacitor_str', '-')}",
            f"Enviroment: {getattr(antenna_data, 'info_enviroment_str', '-')}",
        ]
        thanks = str(getattr(antenna_data, "info_thanks_str", "") or "").strip()
        if thanks:
            info_lines.append(f"Thanks: {thanks}")
        info = "<p>" + "<br>".join(html.escape(line) for line in info_lines) + "</p>"

    efficiency_overview_html = _load_efficiency_overview_fragment(antenna_dir)
    vna_measurements_html = _load_vna_measurements_fragment(antenna_dir)
    environment_html = _load_environment_fragment(antenna_dir)
    h_field_html = _strip_shared_h_field_intro(_load_h_field_fragment(antenna_dir))

    environment_section_html = ""
    if environment_html.strip():
        environment_section_html = (
            "<h2>Enviroment</h2>\n"
            f"{environment_html}"
        )

    measurement_section_html = ""
    if vna_measurements_html.strip():
        measurement_section_html = (
            "<h2>VNA-measurements</h2>\n"
            f"{vna_measurements_html}"
        )

    h_field_section_html = ""
    if h_field_html.strip():
        h_field_intro_html = _load_shared_h_field_intro_html(antenna_dir)
        h_field_section_html = (
            "<h2>H-field</h2>\n"
            f"{h_field_intro_html}\n"
            f"{h_field_html}"
        )

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
    first_image_html = (
        f'<p><a href="{src}"><img class="overview-antenna-picture" src="{src}" alt="{alt}"></a></p>'
    )

    context = {
        "PAGE_TITLE": html.escape(page_title),
        "H1_TITLE": html.escape(h1_title),
        "ANTENNA_CSS_HREF": "../../../static/css/style_antenna.css",
        "INFO_HTML": info,
        "FIRST_IMAGE_HTML": first_image_html,
        "EFFICIENCY_OVERVIEW_HTML": efficiency_overview_html,
        "ENVIRONMENT_SECTION_HTML": environment_section_html,
        "MEASUREMENT_SECTION_HTML": measurement_section_html,
        "H_FIELD_SECTION_HTML": h_field_section_html,
    }

    template = _load_template()
    for key, value in context.items():
        template = template.replace(f"{{{{{key}}}}}", value)
    return template


def _generate_one(antenna_dir: pathlib.Path) -> pathlib.Path:
    antenna_data = _load_antenna_data(antenna_dir)
    html_text = _render_ninja_page(antenna_dir=antenna_dir, antenna_data=antenna_data)
    output_file = antenna_dir / NINJA_FILENAME
    output_file.write_text(html_text, encoding="utf-8")
    return output_file


def _resolve_antenna_dir(argument: str) -> pathlib.Path:
    candidate = pathlib.Path(argument)
    if candidate.is_absolute():
        antenna_dir = candidate
    else:
        antenna_dir = constants.DIRECTORY_REPO / "src" / "antennen" / argument

    antenna_dir = antenna_dir.resolve()
    if not (antenna_dir / "antennendaten.py").is_file():
        raise ValueError(
            "Ungueltiges Antennenverzeichnis: "
            f"{antenna_dir} (antennendaten.py fehlt)"
        )
    return antenna_dir


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--antenna-dir",
        help=(
            "Optional: antenna directory name under src/antennen/ or absolute path. "
            "If omitted, all antennas are generated."
        ),
    )
    args = parser.parse_args()

    if args.antenna_dir:
        antenna_dir = _resolve_antenna_dir(args.antenna_dir)
        output_file = _generate_one(antenna_dir)
        print(f"Written: {output_file}")
        print("Ninja pages generated: 1")
        return

    count = 0
    for antenna_dir in _iter_antenna_dirs():
        output_file = _generate_one(antenna_dir)
        print(f"Written: {output_file}")
        count += 1

    print(f"Ninja pages generated: {count}")


if __name__ == "__main__":
    main()
