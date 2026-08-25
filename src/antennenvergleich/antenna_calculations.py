"""Physics calculations for magnetic-loop antenna comparison."""

from magloop_field.calculations import AntennaCalculator

from antennenvergleich.datatypes import Antenna, BandData

P_W = 100.0  # reference transmit power into antenna (W)


def _make_calc(antenna: Antenna, bd: BandData) -> AntennaCalculator:
    return AntennaCalculator(
        D_m=antenna.D_m.value,
        d_m=antenna.d_m.value,
        n=antenna.n.value if antenna.n.value is not None else 1,
        p_m=antenna.p_m.value or 0.0,
        swr_min=bd.swr_min.value,
        f_Hz=bd.f_Hz.value,
        bw262_Hz=bd.bw262_Hz.value,
        P_W=P_W,
    )
