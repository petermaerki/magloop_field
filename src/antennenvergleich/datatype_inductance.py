from __future__ import annotations

import importlib
import pathlib
import subprocess
from dataclasses import dataclass

from antennenvergleich.constants import DIRECTORY_SRC, RUFF_BIN


@dataclass(frozen=True)
class Inductance:
    cap_nix_file: str | None
    cap_off_file: str
    cap_100p_file: str
    cap_560p_file: str
    f_nix_hz: float | None
    f_off_hz: float
    f_100p_hz: float
    f_560p_hz: float
    l_100p_h: float
    l_560p_h: float
    c_nix_f: float | None

    def write_py(self, filename: pathlib.Path) -> None:
        assert isinstance(filename, pathlib.Path)

        with filename.open("w") as fw:
            fw.write(
                '"""Induktivitaet aus CAP-Schaltmessungen (automatisch erzeugt)."""\n\n'
            )
            fw.write("from antennenvergleich.datatype_inductance import Inductance\n\n")
            fw.write(f"INDUCTANCE = {self!r}\n")

        try:
            subprocess.run(
                [str(RUFF_BIN), "format", str(filename)],
                check=True,
            )
        except FileNotFoundError:
            print(f"Warnung: {RUFF_BIN} nicht gefunden, ueberspringe Formatierung.")
        except subprocess.CalledProcessError as exc:
            print(f"Warnung: ruff format fehlgeschlagen fuer {filename}: {exc}")

    @staticmethod
    def read_values_file(filename: pathlib.Path) -> "Inductance":
        """Load swr_values and model from a generated *_values.py file."""
        try:
            relative_py = filename.resolve().relative_to(DIRECTORY_SRC)
        except ValueError as exc:
            raise RuntimeError(f"{filename} liegt nicht unter {DIRECTORY_SRC}") from exc

        module_name = ".".join(relative_py.with_suffix("").parts)
        module = importlib.import_module(module_name)
        module = importlib.reload(module)

        inductance = getattr(module, "INDUCTANCE", None)

        if inductance is None:
            raise TypeError(f"{filename.name}: S1P_VALUES does not exist!")

        if not isinstance(inductance, Inductance):
            raise TypeError(f"{filename.name}: S1P_VALUES hat unerwarteten Typ")

        return inductance

