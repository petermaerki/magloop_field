from __future__ import annotations

import importlib
import pathlib
import subprocess
from dataclasses import dataclass

from antennenvergleich.constants import DIRECTORY_SRC, RUFF_BIN
from antennenvergleich.datatypes import BandData, FloatText


@dataclass(frozen=True)
class AntennaModelFit:
    R_res_ohm: float
    L_res_H: float
    C_res_F: float
    L_P_H: float
    f0_Hz: float
    Q: float
    BSWR2_62_Hz: float
    alpha_db: float
    tau_s: float
    fit_residual: float
    fit_success: bool
    fit_message: str
    fit_iterations: int


@dataclass(frozen=True)
class SwrValues:
    swr_min: float
    eta_swr: float
    eta_swr_ant: float | None
    f_swr_hz_min: float
    z_swr_min: complex


@dataclass(frozen=True)
class S1pValues:
    filename: str
    swr_values : SwrValues
    model : AntennaModelFit | None
    b_tau_s :float

    @property
    def band_data(self) -> BandData:
        if self.model is None:
            raise ValueError("band_data requires a fitted model")

        return BandData(
            f_Hz=FloatText(self.model.f0_Hz, "s1p model fit"),
            bw262_Hz=FloatText(self.model.BSWR2_62_Hz, "s1p model fit"),
            swr_min=FloatText(self.swr_values.swr_min, "s1p measurement"),
        )

    def write_py(self, filename:pathlib.Path) ->None:
        assert isinstance(filename, pathlib.Path)

        with filename.open("w") as fw:
            fw.write("import numpy as np\n")
            fw.write("\n")
            fw.write(
                "from antennenvergleich.datatypes_s1p import AntennaModelFit, S1pValues, SwrValues\n"
            )
            fw.write(f"S1P_VALUES = {self!r}\n")

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
    def read_values_file(filename: pathlib.Path) -> "S1pValues":
        """Load swr_values and model from a generated *_values.py file."""
        try:
            relative_py = filename.resolve().relative_to(DIRECTORY_SRC)
        except ValueError as exc:
            raise RuntimeError(
                f"{filename} liegt nicht unter {DIRECTORY_SRC}"
            ) from exc

        module_name = ".".join(relative_py.with_suffix("").parts)
        module = importlib.import_module(module_name)
        module = importlib.reload(module)

        s1p_values = getattr(module, "S1P_VALUES", None)

        if s1p_values is None:
            raise TypeError(f"{filename.name}: S1P_VALUES does not exist!")

        if not isinstance(s1p_values, S1pValues):
            raise TypeError(f"{filename.name}: S1P_VALUES hat unerwarteten Typ")

        return s1p_values