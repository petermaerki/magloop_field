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


def _fmt_z(z: complex) -> str:
    """Format complex without outer parens: 're + imj' or 're - imj'."""
    if z.imag >= 0:
        return f"{z.real!r} + {z.imag!r}j"
    return f"{z.real!r} - {abs(z.imag)!r}j"


@dataclass(frozen=True, repr=False)
class Debug3Point:
    impedances_around_resonance: tuple[tuple[float, complex, float], ...]
    impedances_3_selected: tuple[tuple[float, complex, float], ...]

    def __repr__(self) -> str:
        inner_all = ", ".join(
            f"({f!r}, {_fmt_z(z)}, {swr!r})"
            for f, z, swr in self.impedances_around_resonance
        )
        inner_sel = ", ".join(
            f"({f!r}, {_fmt_z(z)}, {swr!r})" for f, z, swr in self.impedances_3_selected
        )
        return (
            f"Debug3Point("
            f"impedances_around_resonance=({inner_all},), "
            f"impedances_3_selected=({inner_sel},)"
            f")"
        )


@dataclass(frozen=True)
class S1pValues:
    filename: str
    swr_values: SwrValues
    model: AntennaModelFit | None
    b_tau_s: float
    debug_from_3_point_measurement: Debug3Point | None = None

    @property
    def band_data(self) -> BandData:
        if self.model is None:
            raise ValueError("band_data requires a fitted model")

        return BandData(
            f_Hz=FloatText(self.model.f0_Hz, "s1p model fit"),
            bw262_Hz=FloatText(self.model.BSWR2_62_Hz, "s1p model fit"),
            swr_min=FloatText(self.swr_values.swr_min, "s1p measurement"),
        )

    def write_py(self, filename: pathlib.Path) -> None:
        assert isinstance(filename, pathlib.Path)

        with filename.open("w") as fw:
            fw.write("import numpy as np\n")
            fw.write("\n")
            imports = "AntennaModelFit, S1pValues, SwrValues"
            if self.debug_from_3_point_measurement is not None:
                imports = "AntennaModelFit, Debug3Point, S1pValues, SwrValues"
            fw.write(f"from antennenvergleich.datatypes_s1p import {imports}\n")
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
    def read_values_file(filename: pathlib.Path) -> S1pValues:
        """Load swr_values and model from a generated *_values.py file."""
        try:
            relative_py = filename.resolve().relative_to(DIRECTORY_SRC)
        except ValueError as exc:
            raise RuntimeError(f"{filename} liegt nicht unter {DIRECTORY_SRC}") from exc

        module_name = ".".join(relative_py.with_suffix("").parts)
        module = importlib.import_module(module_name)
        module = importlib.reload(module)

        s1p_values = getattr(module, "S1P_VALUES", None)

        if s1p_values is None:
            raise TypeError(f"{filename.name}: S1P_VALUES does not exist!")

        if not isinstance(s1p_values, S1pValues):
            raise TypeError(f"{filename.name}: S1P_VALUES hat unerwarteten Typ")

        return s1p_values
