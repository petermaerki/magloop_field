import math

from antennenvergleich.datatypes import Antenna, BandData, FloatText, IntText

SOURCES = ["youtube, slides"]

NOTES = [
    "",
]

FOOTNOTES = {
    "1": "",
}

rectangle_width_m = 1.2192
A_m2 = rectangle_width_m * rectangle_width_m
aequivalent_D_m = 2 * math.sqrt(A_m2 / math.pi)


# Idee: umrechnen einer idealen SWR 10 messung in die Bandbreite 2.62
# Beim 40 Meter band weiss ich nicht ob über oder unterkoppelt. Unklar. Ich schätze
bandbreite_Hz_swr10 = 7190000 - 6690000
bandbreite_HZ_von_auge_262 = 7040000 - 6830000


def _norm_reactance_from_swr(swr: float) -> float:
    rho = (swr - 1.0) / (swr + 1.0)
    return 2.0 * rho / math.sqrt(1.0 - rho * rho)


_bw_factor_swr10_to_swr262 = _norm_reactance_from_swr(2.62) / _norm_reactance_from_swr(
    10.0
)
calculated_bandbreite_Hz_swr262 = bandbreite_Hz_swr10 * _bw_factor_swr10_to_swr262
bandwith_262_entscheid_Hz = 200000
print(
    f"{calculated_bandbreite_Hz_swr262=}, {bandbreite_HZ_von_auge_262=}, {bandwith_262_entscheid_Hz=}"
)


ANTENNENDATEN = Antenna(
    #name="epicenter",
    #call="W6NBC",
    color="#d60000",
    selection_brand="Selfmade",
    selection_location="W6NBC",
    selection_name="epicenter",
    D_m=FloatText(
        aequivalent_D_m,
        "YouTube: square loop 4 ft x 4 ft -> equivalent D = 2*sqrt(A/pi)",
    ),
    d_m=FloatText(0.04826, "youtube, OD1.9 Inch"),
    n=IntText(1, ""),
    p_m=FloatText(0.0, ""),
    powerP_W=FloatText(50.0, "estimated reference power; not documented in the available sources"),
    info_str="Rectangular loop, PVC pipe wrapped with aluminum foil. The frequency is tuned by sliding an aluminum-foil-covered tube back and forth in the upper segment.",
    overview_pictures=("images/epicenter_overview.png",),
    info_enviroment_str="Outdoor, details unknown.",
    info_conductor_str="PVC pipe wrapped with aluminum foil.",
    info_capacitor_str="Variable capacitor made from telescoping PVC pipes wrapped with aluminum foil.",
    info_thanks_str="Many thanks to W6NBC (Silent Key) for the many publicly available contributions.",
    measurement_html=("measurement.html",),
    bands=[
        BandData(
            f_Hz=FloatText(31_870_000, "screenshot"),
            bw262_Hz=FloatText(32200000 - 31500000, "screenshot"),
            swr_min=FloatText(1.1, "screenshot"),
        ),
        BandData(
            f_Hz=FloatText(6940000, "screenshot"),
            bw262_Hz=FloatText(
                bandwith_262_entscheid_Hz, "rough estimate from the screenshot, "
            ),
            swr_min=FloatText(2.7, ""),
        ),
    ],
)
