"""Load antenna metadata and generated values modules."""

from __future__ import annotations

import importlib
import pathlib

from antennenvergleich.datatypes_s1p import AntennaModelFit, SwrValues, ValuesDataFile

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent
DIRECTORY_SRC = DIRECTORY_OF_THIS_FILE.parent


def read_values_file(filename_values_py: pathlib.Path) -> ValuesDataFile:
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


def load_antenna_data(antenna_dir_name: str) -> object | None:
    """Load ANTENNENDATEN for an antenna directory if available."""
    try:
        antenna_module = importlib.import_module(
            f"antennen.{antenna_dir_name}.antennendaten"
        )
        return getattr(antenna_module, "ANTENNENDATEN", None)
    except Exception as exc:  # pragma: no cover - best effort for optional section
        print(
            "Warnung: Antennendaten konnten nicht geladen werden "
            f"({antenna_dir_name}): {exc}"
        )
        return None
