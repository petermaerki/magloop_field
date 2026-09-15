from __future__ import annotations

import importlib
import pathlib
from dataclasses import dataclass

from antennenvergleich.constants import DIRECTORY_SRC
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

    def __repr__(self) -> str:
        return _fmt_dataclass_block(
            "AntennaModelFit",
            [
                f"R_res_ohm={self.R_res_ohm!r}",
                f"L_res_H={self.L_res_H!r}",
                f"C_res_F={self.C_res_F!r}",
                f"L_P_H={self.L_P_H!r}",
                f"f0_Hz={self.f0_Hz!r}",
                f"Q={self.Q!r}",
                f"BSWR2_62_Hz={self.BSWR2_62_Hz!r}",
                f"alpha_db={self.alpha_db!r}",
                f"tau_s={self.tau_s!r}",
                f"fit_residual={self.fit_residual!r}",
                f"fit_success={self.fit_success!r}",
                f"fit_message={self.fit_message!r}",
                f"fit_iterations={self.fit_iterations!r}",
            ],
        )


@dataclass(frozen=True)
class SwrValues:
    swr_min: float
    eta_swr: float
    eta_swr_ant: float | None
    f_swr_hz_min: float
    z_swr_min: complex

    def __repr__(self) -> str:
        return _fmt_dataclass_block(
            "SwrValues",
            [
                f"swr_min={self.swr_min!r}",
                f"eta_swr={self.eta_swr!r}",
                f"eta_swr_ant={self.eta_swr_ant!r}",
                f"f_swr_hz_min={self.f_swr_hz_min!r}",
                f"z_swr_min=np.complex128({_fmt_z(self.z_swr_min)})",
            ],
        )


def _fmt_z(z: complex) -> str:
    """Format complex without outer parens: 're + imj' or 're - imj'."""
    real = float(z.real)
    imag = float(z.imag)
    if imag >= 0:
        return f"{real!r} + {imag!r}j"
    return f"{real!r} - {abs(imag)!r}j"


def _fmt_result_str(s: str) -> str:
    """Format a multiline string as concatenated quoted literals, one per line."""
    parts = s.split("\n")
    if s.endswith("\n"):
        parts = parts[:-1]
        segments = [repr(p + "\n") for p in parts]
    else:
        segments = [repr(p + "\n") for p in parts[:-1]]
        if parts[-1]:
            segments.append(repr(parts[-1]))
    if len(segments) <= 1:
        return repr(s)
    return "(\n    " + "\n    ".join(segments) + "\n)"


def _fmt_dataclass_block(name: str, fields: list[str]) -> str:
    return f"{name}(\n        " + ",\n        ".join(fields) + ",\n    )"


def _fmt_measurement_block(
    measurements: tuple[tuple[float, complex, float], ...],
) -> str:
    lines = ["("]
    for frequency_hz, impedance, swr in measurements:
        lines.append(f"            ({frequency_hz!r}, {_fmt_z(impedance)}, {swr!r}),")
    lines.append("        )")
    return "\n".join(lines)


def _fmt_debug_swr_only_str(s: str) -> str:
    """Format the SWR-only debug note with an explicit comment and line breaks."""
    parts = s.split("\n")
    if len(parts) <= 1:
        return repr(s)

    if s.endswith("\n"):
        parts = parts[:-1]

    lines = ["("]
    for index, part in enumerate(parts):
        literal = part + "\n" if index < len(parts) - 1 else part
        lines.append(f"    {literal!r}")
    lines.append(")")
    return "\n".join(lines)


def _fmt_debug_swr_only_block(s: str) -> str:
    """Format the SWR-only field as a multiline assignment block."""
    parts = s.split("\n")
    if len(parts) <= 1:
        return f"debug_swr_only={s!r}"

    if s.endswith("\n"):
        parts = parts[:-1]

    lines = ["debug_swr_only=("]
    for index, part in enumerate(parts):
        literal = part + "\n" if index < len(parts) - 1 else part
        lines.append(f"        {literal!r}")
    lines.append("    )")
    return "\n".join(lines)


@dataclass(frozen=True, repr=False)
class Debug3Point:
    impedances_around_resonance: tuple[tuple[float, complex, float], ...]
    debug_impedances_3_selected: tuple[tuple[float, complex, float], ...]
    debug_result_3_impedances: str

    def __repr__(self) -> str:
        return _fmt_dataclass_block(
            "Debug3Point",
            [
                f"impedances_around_resonance={_fmt_measurement_block(self.impedances_around_resonance)}",
                f"debug_impedances_3_selected={_fmt_measurement_block(self.debug_impedances_3_selected)}",
                f"debug_result_3_impedances={_fmt_result_str(self.debug_result_3_impedances)}",
            ],
        )


@dataclass(frozen=True, repr=False)
class S1pValues:
    filename: str
    swr_values: SwrValues
    model: AntennaModelFit | None
    b_tau_s: float
    debug_swr_only: str | None = None
    debug_from_3_point_measurement: Debug3Point | None = None

    def __repr__(self) -> str:
        parts = [
            f"filename={self.filename!r}",
            f"swr_values={self.swr_values!r}",
            f"model={self.model!r}",
            f"b_tau_s={self.b_tau_s!r}",
        ]
        if self.debug_swr_only is not None:
            parts.append(_fmt_debug_swr_only_block(self.debug_swr_only))
        if self.debug_from_3_point_measurement is not None:
            parts.append(
                f"debug_from_3_point_measurement={self.debug_from_3_point_measurement!r}"
            )
        return "S1pValues(\n    " + ",\n    ".join(parts) + ",\n)"

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

        imports = ["AntennaModelFit", "S1pValues", "SwrValues"]
        if self.debug_from_3_point_measurement is not None:
            imports = ["AntennaModelFit", "Debug3Point", "S1pValues", "SwrValues"]

        text = "\n".join(
            [
                "import numpy as np",
                "",
                "from antennenvergleich.datatypes_s1p import " + ", ".join(imports),
                "",
                f"S1P_VALUES = {self!r}",
                "",
            ]
        )
        filename.write_text(text)

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
