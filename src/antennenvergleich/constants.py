import pathlib
import sys
from math import pi, sqrt
from types import SimpleNamespace

from antennenvergleich.datatypes import Antenna, FloatText, IntText, VnaCalibration

IS_PYODIDE = sys.platform == "emscripten"

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent
DIRECTORY_REPO = DIRECTORY_OF_THIS_FILE.parent.parent
if not IS_PYODIDE:
    assert (DIRECTORY_REPO / "README.md").is_file(), str(DIRECTORY_REPO)

ANTENNENDATEN_FILENAME = "antennendaten.py"



BANDS = SimpleNamespace(
    f_hz_by_band_name={
        "10m": 28_500_000,
        "12m": 24_940_000,
        "15m": 21_200_000,
        "17m": 18_120_000,
        "20m": 14_150_000,
        "30m": 10_100_000,
        "40m": 7_100_000,
        "60m": 5_350_000,
        "80m": 3_650_000,
        "160m": 1_840_000,
    },
)

_power_standard_P_W = 100.0

PETER_TUBBY = Antenna(
    name="Tubby Peter Outdoor",
    call="HB9ISP",
    D_m=FloatText(
        1.014,
        "[Maerki2026] paper sec. 'Key Parameters': equivalent diameter 1.014 m (rechteckige Schleife 0.95 m × 0.85 m)",
    ),
    d_m=FloatText(
        0.100, "[Maerki2026] paper sec. 'Key Parameters': tubing diameter 100 mm"
    ),
    n=IntText(1, ""),
    p_m=FloatText(0.0, ""),
    powerP_W=FloatText(_power_standard_P_W, "typical power"),
    info_str="Homebrew rectangular loop made of thick copper tubing with vacuum capacitors, 10 m to 160 m.",
    info_enviroment_str="",
    info_conductor_str="Copper tube 100mm",
    info_capacitor_str="Vacuum Capacitor",
)


_STEALTH_AREA_M2 = 0.328
_STEALTH_PROFILE_W_MM = 60
_STEALTH_PROFILE_H_MM = 20

_MAZZONI_CONDUCTOR_BABY_MIDI = (
    "Aluminium tube, 2 mm wall thickness, bare untreated surface."
)
_MAZZONI_CAPACITOR_BABY_MIDI = "Variable air capacitor; the plate stack at the top of the antenna is telescoped in and out."
_MAZZONI_ENVIROMENT = "Unknown, values from datasheet."
_MAZZONI_INFO = "Widely used antenna from the manufacturer Mazzoni, Italy."
MAZZONI_STEALTH = SimpleNamespace(
    D_m=FloatText(
        2 * sqrt(_STEALTH_AREA_M2 / pi),
        "[MaerkiMD] Stealth: äquiv. Durchmesser = 2*sqrt(A/pi) mit A = 0.328 m^2 aus [MaerkiFCAD]",
    ),
    d_m=FloatText(
        2 * (_STEALTH_PROFILE_W_MM + _STEALTH_PROFILE_H_MM) / pi / 1000,
        "[MaerkiMD] Stealth: äquiv. Rohrdurchmesser = Umfang/pi, rechteckiges Profil 60 × 20 mm, 2 mm Wandstärke",
    ),
    n=IntText(1, ""),
    p_m=FloatText(0.0, ""),
    powerP_W=FloatText(_power_standard_P_W, "typical power"),
    info_str=_MAZZONI_INFO,
    info_enviroment_str=_MAZZONI_ENVIROMENT,
    info_conductor_str="Aluminium rectangular tube, painted gray.",
    info_capacitor_str="Air capacitor, likely aluminum, painted gray",
)

_MIDI_CONDUCTOR_WIDTH_m = 0.076
_MIDI_CONDUCTOR_HEIGT_m = 0.07
_MIDI_CONDUCTOR_AVERAGE_d_m = (_MIDI_CONDUCTOR_WIDTH_m + _MIDI_CONDUCTOR_HEIGT_m) / 2.0


MAZZONI_MIDI = SimpleNamespace(
    # D_m=FloatText(1.925, "[MaerkiMD] MIDI Loop: Durchmesser 1.925 m"),
    # d_m=FloatText(
    #    0.075,
    #    "[MaerkiMD] MIDI Loop: Rohrdurchmesser Ø 75 mm; Quelle unsicher, nicht im offiziellen Datenblatt angegeben, Fussnote [1]",
    # ),
    D_m=FloatText(1.92, "20260820 measured at midi loop HB0SM@ lowest frequency"),
    d_m=FloatText(
        _MIDI_CONDUCTOR_AVERAGE_d_m,
        "20260820 measured at midi loop HB0SM, average width and height",
    ),
    n=IntText(1, ""),
    p_m=FloatText(0.0, ""),
    powerP_W=FloatText(_power_standard_P_W, "typical power"),
    info_str=_MAZZONI_INFO,
    info_enviroment_str=_MAZZONI_ENVIROMENT,
    info_conductor_str=_MAZZONI_CONDUCTOR_BABY_MIDI,
    info_capacitor_str=_MAZZONI_CAPACITOR_BABY_MIDI,
)

MAZZONI_BABY = SimpleNamespace(
    # D_m=FloatText(0.95, "[MaerkiMD] Baby Loop: Durchmesser 0.95 m"),
    # d_m=FloatText(0.05, "[MaerkiMD] Baby Loop: Rohrdurchmesser Ø 50 mm"),
    D_m=FloatText(0.94, "20260820 measured at baby loop HB0SM@ lowest frequency"),
    d_m=FloatText(0.0494, "20260820 measured at baby loop HB0SM"),
    n=IntText(1, ""),
    p_m=FloatText(0.0, ""),
    powerP_W=FloatText(_power_standard_P_W, "typical power"),
    info_str=_MAZZONI_INFO,
    info_enviroment_str=_MAZZONI_ENVIROMENT,
    info_conductor_str=_MAZZONI_CONDUCTOR_BABY_MIDI,
    info_capacitor_str=_MAZZONI_CAPACITOR_BABY_MIDI,
)

DK3SS = SimpleNamespace(
    d_m=FloatText(0.01, "qrz_com_db_DK3SS.pdf"),
    n=IntText(2, "Fotos und Text, 20260808b_email_*.md "),
    p_m=FloatText(0.05, "EMail 20260809"),
    powerP_W=FloatText(10.0, "typical power"),
    info_str="Homebrew copper loop by DK3SS. Two turns; frequency is adjusted by varying the spacing between the turns.",
    info_enviroment_str="On a table in the middle of an attic apartment room, non-conductive building materials.",
    info_conductor_str="Copper tube 10mm",
    info_capacitor_str="Ceramic Disc Capacitors",
    info_thanks_str="Many thanks to Arno for answering my many questions by email.",
)


HB9SM = SimpleNamespace(
    info_enviroment_str="Indoor, 3rd floor below the roof.",
    info_thanks_str="Many thanks to Stefan for the support and for allowing me to publish these measurement values and supporting documents.",
    vna_calibration=VnaCalibration.ANTENNA_FEED_POINT,
)
