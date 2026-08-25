from __future__ import annotations

from dataclasses import dataclass

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
class ValuesDataFile:
    swr_values: SwrValues
    model: AntennaModelFit | None

    @property
    def band_data(self) -> BandData:
        if self.model is None:
            raise ValueError("band_data requires a fitted model")

        return BandData(
            f_Hz=FloatText(self.model.f0_Hz, "s1p model fit"),
            bw262_Hz=FloatText(self.model.BSWR2_62_Hz, "s1p model fit"),
            swr_min=FloatText(self.swr_values.swr_min, "s1p measurement"),
        )
