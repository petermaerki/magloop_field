"""Loaders and path helpers for the Ninja page assembly pipeline."""

from __future__ import annotations

import importlib
import pathlib
from collections.abc import Iterable

from .. import constants
from ..html_fragments import rewrite_local_links_in_html_fragment
from ..output_filenames import (
    FILENAME_ANTENNA_EFFICIENCY_TABLE,
    FILENAME_DIAGRAMS_FRAGMENT,
    FILENAME_ENVIRONMENT_FRAGMENT,
    FILENAME_H_FIELD_FRAGMENT,
    FILENAME_INDUCTANCE_FRAGMENT,
    FILENAME_VNA_MEASUREMENTS_FRAGMENT,
)

NINJA_FILENAME = "antenna_ninja_generated.html"
TEMPLATE_FILE = constants.DIRECTORY_OF_THIS_FILE / "templates" / "antenna_ninja.html"
SHARED_H_FIELD_INTRO_FILE = (
    constants.DIRECTORY_REPO / "src" / "shared" / "h_field" / "h_field_intro.html"
)


def iter_antenna_dirs() -> Iterable[pathlib.Path]:
    antennas_root = constants.DIRECTORY_REPO / "src" / "antennen"
    for antenna_data_file in sorted(antennas_root.rglob("antennendaten.py")):
        if antenna_data_file.parent.name == "__pycache__":
            continue
        yield antenna_data_file.parent


def resolve_antenna_dir(argument: str) -> pathlib.Path:
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


def load_antenna_data(antenna_dir: pathlib.Path) -> object | None:
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


def load_template() -> str:
    template = _safe_read_text(TEMPLATE_FILE)
    if not template:
        raise FileNotFoundError(f"Template nicht gefunden oder leer: {TEMPLATE_FILE}")
    return template


def load_efficiency_overview_fragment(antenna_dir: pathlib.Path) -> str:
    fragment_file = antenna_dir / FILENAME_ANTENNA_EFFICIENCY_TABLE
    assert fragment_file.is_file(), (
        "Efficiency-Fragment fehlt. Bitte zuerst run_2_html ausfuehren: "
        f"{fragment_file}"
    )
    fragment = fragment_file.read_text(encoding="utf-8")
    assert fragment.strip(), f"Efficiency-Fragment ist leer: {fragment_file}"
    return fragment.rstrip()


def load_environment_fragment(antenna_dir: pathlib.Path) -> str:
    fragment_file = antenna_dir / FILENAME_ENVIRONMENT_FRAGMENT
    assert fragment_file.is_file(), (
        "Enviroment-Fragment fehlt. Bitte zuerst run_2_html ausfuehren: "
        f"{fragment_file}"
    )
    return fragment_file.read_text(encoding="utf-8")


def load_vna_measurements_fragment(antenna_dir: pathlib.Path) -> str:
    fragment_file = antenna_dir / FILENAME_VNA_MEASUREMENTS_FRAGMENT
    assert fragment_file.is_file(), (
        "VNA-Fragment fehlt. Bitte zuerst run_2_html ausfuehren: "
        f"{fragment_file}"
    )
    return fragment_file.read_text(encoding="utf-8")


def load_h_field_fragment(antenna_dir: pathlib.Path) -> str:
    fragment_file = antenna_dir / FILENAME_H_FIELD_FRAGMENT
    assert fragment_file.is_file(), (
        "H-field-Fragment fehlt. Bitte zuerst run_2_html ausfuehren: "
        f"{fragment_file}"
    )
    return fragment_file.read_text(encoding="utf-8")


def load_diagrams_fragment(antenna_dir: pathlib.Path) -> str:
    fragment_file = antenna_dir / FILENAME_DIAGRAMS_FRAGMENT
    assert fragment_file.is_file(), (
        "Diagramm-Fragment fehlt. Bitte zuerst run_2_html ausfuehren: "
        f"{fragment_file}"
    )
    return fragment_file.read_text(encoding="utf-8")


def load_inductance_fragment(antenna_dir: pathlib.Path) -> str:
    fragment_file = antenna_dir / FILENAME_INDUCTANCE_FRAGMENT
    assert fragment_file.is_file(), (
        "Inductance-Fragment fehlt. Bitte zuerst run_2_html ausfuehren: "
        f"{fragment_file}"
    )
    return fragment_file.read_text(encoding="utf-8")


def load_shared_h_field_intro_html(antenna_dir: pathlib.Path) -> str:
    assert SHARED_H_FIELD_INTRO_FILE.is_file(), (
        "Shared H-field-Intro fehlt: "
        f"{SHARED_H_FIELD_INTRO_FILE}"
    )
    intro_html = SHARED_H_FIELD_INTRO_FILE.read_text(encoding="utf-8")
    assert intro_html.strip(), (
        "Shared H-field-Intro ist leer: "
        f"{SHARED_H_FIELD_INTRO_FILE}"
    )
    return rewrite_local_links_in_html_fragment(
        intro_html,
        fragment_dir=SHARED_H_FIELD_INTRO_FILE.parent,
        destination_dir=antenna_dir,
    )
