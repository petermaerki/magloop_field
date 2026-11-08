"""Physics calculations for magnetic-loop antenna comparison."""

from antennenvergleich.datatypes import Antenna, BandData
from magloop_field.calculations import AntennaCalculator


def _make_calc(antenna: Antenna, bd: BandData) -> AntennaCalculator:
    return AntennaCalculator(
        D_m=antenna.D_m.value,  # type: ignore[arg-type]
        d_m=antenna.d_m.value,  # type: ignore[arg-type]
        n=antenna.n.value if antenna.n.value is not None else 1,
        p_m=antenna.p_m.value or 0.0,
        swr_min=bd.swr_min.value,  # type: ignore[arg-type]
        f_Hz=bd.f_Hz.value,  # type: ignore[arg-type]
        bw262_Hz=bd.bw262_Hz.value,  # type: ignore[arg-type]
        powerPfwd_W=antenna.powerPfwd_W.value,  # type: ignore[arg-type]
    )
