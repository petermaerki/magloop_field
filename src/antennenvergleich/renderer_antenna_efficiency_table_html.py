import dataclasses

from magloop_field.calculations import AntennaCalculator as FieldAntennaCalculator

from .constants_s1p import DIRECTORY_S1P_RESULTS
from .datatypes import Antenna

ROW_SPECS: list[tuple[str, str, str, str]] = [
    ("Frequency <i>f</i>", "MHz", "f", "Mittenfrequenz des betrachteten Bandes."),
    (
        "Bandwidth <i>B</i><sub>SWR=2.62</sub>",
        "kHz",
        "bw",
        "Bandbreite am Antenneneingang beim Kriterium SWR = 2.62.",
    ),
    ("Loop diameter <i>D</i>", "m", "D", "Äquivalenter Durchmesser der Loop."),
    (
        "Conductor diameter <i>d</i>",
        "m",
        "d",
        "Äquivalenter Leiterdurchmesser der Loop.",
    ),
    ("Loop count <i>n</i>", "1", "n", "Anzahl der Windungen der Schleife."),
    (
        "Power into antenna <i>P</i>",
        "W",
        "P",
        "Eingespeiste Leistung in die Antenne.",
    ),
    ("Inductance <i>L</i>", "H", "L", "Berechnete Induktivität der Loop."),
    (
        "Capacitance <i>C</i>",
        "F",
        "C",
        "Erforderliche Resonanzkapazität bei der Bandfrequenz.",
    ),
    (
        "Unloaded Q<sub>0</sub>",
        "1",
        "Q0",
        "Unbelastete Güte, aus f / Bandbreite abgeschätzt.",
    ),
    (
        "Damping resistance <i>R</i><sub>T</sub>",
        "Ohm",
        "RT",
        "Gesamter Dämpfungswiderstand des Resonanzkreises.",
    ),
    (
        "Radiation resistance <i>R</i><sub>R</sub>",
        "Ohm",
        "RR",
        "Äquivalenter Strahlungswiderstand der Antenne.",
    ),
    (
        "Loss resistance <i>R</i><sub>Loss</sub>",
        "Ohm",
        "RLoss",
        "Verlustwiderstand: R_T - R_R.",
    ),
    ("swr_min", "1", "swr_min", "Minimales SWR am Antenneneingang."),
    (
        "eta<sub>SWR_ant</sub>",
        "%",
        "eta_swr",
        "Anpassungswirkungsgrad aus swr_min: eta = 4*SWR/(1+SWR)^2.",
    ),
    (
        "<b>Antenna efficiency <i>η</i></b>",
        "<b>%</b>",
        "eta",
        "Gesamteffizienz: (R_R / R_T) * eta_SWR_ant.",
    ),
    (
        "Loop current <i>I</i>",
        "A",
        "I",
        "Strom im Hauptloop bei der Referenzleistung.",
    ),
    (
        "Loop voltage <i>U</i><sub>loop</sub>",
        "V",
        "U",
        "Spannung über dem Loop bei Resonanz.",
    ),
    (
        "Magnetic dipole moment <i>m</i>",
        "A m²",
        "m",
        "Magnetisches Dipolmoment des Loops.",
    ),
]

MERGED_SINGLE_VALUE_KEYS = {"D", "d", "n", "L"}


@dataclasses.dataclass(frozen=True)
class EfficiencyCell:
    value: str
    tooltip: str
    css_class: str = "val"
    colspan: int = 1


@dataclasses.dataclass(frozen=True)
class EfficiencyRow:
    label_html: str
    unit_html: str
    tooltip: str
    cells: list[EfficiencyCell]
    css_class: str = ""


@dataclasses.dataclass(frozen=True)
class EfficiencyTable:
    """columns: one band label per column."""

    columns: list[str]
    rows: list[EfficiencyRow]
    empty_message: str


def _fmt_r(v: float) -> str:
    av = abs(v)
    if av < 1e-5:
        return f"{v:.2e}"
    if av < 1e-3:
        return f"{v:.6f}"
    if av < 1e-2:
        return f"{v:.5f}"
    if av < 0.1:
        return f"{v:.4f}"
    return f"{v:.3f}"


def _fmt_percent(v: float) -> str:
    av = abs(v)
    if av >= 100:
        return f"{v:.0f}"
    if av >= 10:
        return f"{v:.1f}"
    if av >= 1:
        return f"{v:.2f}"
    return f"{v:.3f}"


def _calc_for_item(
    item: dict[str, object], antenna_data: Antenna | None
) -> FieldAntennaCalculator | None:
    if antenna_data is None:
        return None
    f0_mhz = item.get("f0_mhz")
    bw_hz = item.get("bswr")
    swr_min = item.get("swr_min")
    if not (
        isinstance(f0_mhz, (int, float))
        and isinstance(bw_hz, (int, float))
        and isinstance(swr_min, (int, float))
    ):
        return None
    try:
        return FieldAntennaCalculator(
            D_m=antenna_data.D_m.value,
            d_m=antenna_data.d_m.value,
            n=antenna_data.n.value if antenna_data.n.value is not None else 1,
            p_m=antenna_data.p_m.value or 0.0,
            swr_min=float(swr_min),
            f_Hz=float(f0_mhz) * 1e6,
            bw262_Hz=float(bw_hz),
            powerP_W=antenna_data.powerP_W.value,
        )
    except Exception:
        return None


def _value_source(
    item: dict[str, object],
    key: str,
    calc: FieldAntennaCalculator | None,
    antenna_data: Antenna | None,
) -> str:
    file_name = str(item.get("file") or "")
    if key == "D":
        if antenna_data is None:
            return file_name
        return str(getattr(antenna_data.D_m, "source", "") or "")
    if key == "d":
        if antenna_data is None:
            return file_name
        return str(getattr(antenna_data.d_m, "source", "") or "")
    if key == "n":
        if antenna_data is None:
            return file_name
        return str(getattr(antenna_data.n, "source", "") or "")
    if key == "f":
        return str(item.get("source_f") or file_name)
    if key == "bw":
        return str(item.get("source_bw") or file_name)
    if key == "swr_min":
        return str(item.get("source_swr") or file_name)
    if key == "eta_swr":
        return f"[{file_name}] Berechnet aus swr_min: eta = 4*SWR/(1+SWR)^2."
    if key == "P":
        if antenna_data is None:
            return file_name
        return str(getattr(antenna_data.powerP_W, "source", "") or file_name)
    if key in {"L", "C", "Q0", "RT", "RR", "RLoss", "eta", "I", "U", "m"}:
        return (
            f"[{file_name}] Berechnet aus Geometrie- und Messdaten."
            if calc is not None
            else file_name
        )
    return file_name


def _format_value(calc: FieldAntennaCalculator | None, key: str) -> str:
    if calc is None:
        return "-"
    if key == "D":
        return f"{calc.D_m:.3f}"
    if key == "d":
        return f"{calc.d_m:.3f}"
    if key == "n":
        return f"{calc.n:.0f}"
    if key == "f":
        return f"{calc.f_Hz / 1e6:.3f}"
    if key == "bw":
        return f"{calc.bw262_Hz / 1e3:.1f}"
    if key == "P":
        return f"{calc.powerP_W:.0f}"
    if key == "L":
        return f"{calc.L_H:.2e}"
    if key == "C":
        return f"{calc.C_F:.2e}"
    if key == "Q0":
        return f"{calc.Q0:.0f}"
    if key == "RT":
        return _fmt_r(calc.RT_Ohm)
    if key == "RR":
        return _fmt_r(calc.RR_Ohm)
    if key == "RLoss":
        return _fmt_r(calc.RLoss_Ohm)
    if key == "swr_min":
        return f"{calc.swr_min:.2f}"
    if key == "eta_swr":
        return _fmt_percent(calc.eta_SWR_ant * 100)
    if key == "eta":
        return _fmt_percent(calc.eta * 100)
    if key == "I":
        return f"{calc.I_main_loop_A:.2f}"
    if key == "U":
        return f"{calc.U_loop_V:.0f}"
    if key == "m":
        return f"{calc.m_Am2:.3f}"
    return "-"


def build_efficiency_table(
    band_data_rows: list[dict[str, object]],
    band_order: list[str],
    antenna_data: Antenna | None,
) -> EfficiencyTable:
    sorted_band_items = sorted(
        band_data_rows,
        key=lambda x: (
            band_order.index(str(x["band"])) if str(x["band"]) in band_order else 999,
            float(x["f0_mhz"]) if isinstance(x["f0_mhz"], (int, float)) else 0.0,
        ),
    )

    seen: dict[str, int] = {}
    band_columns: list[str] = []
    for item in sorted_band_items:
        base = str(item["band"])
        count = seen.get(base, 0) + 1
        seen[base] = count
        band_columns.append(base if count == 1 else f"{base} #{count}")

    rows: list[EfficiencyRow] = []
    for label_html, unit_html, key, tooltip in ROW_SPECS:
        cells: list[EfficiencyCell] = []
        if key in MERGED_SINGLE_VALUE_KEYS and sorted_band_items:
            first_item = sorted_band_items[0]
            first_calc = _calc_for_item(first_item, antenna_data)
            cells.append(
                EfficiencyCell(
                    value=_format_value(first_calc, key),
                    tooltip=_value_source(first_item, key, first_calc, antenna_data),
                    css_class="val merged",
                    colspan=len(sorted_band_items),
                )
            )
        else:
            for item in sorted_band_items:
                calc = _calc_for_item(item, antenna_data)
                css = "val"
                if key == "RLoss" and calc is not None and calc.RLoss_Ohm < 0:
                    css += " neg"
                if key == "eta" and calc is not None and (calc.eta * 100) > 100:
                    css += " neg"
                cells.append(
                    EfficiencyCell(
                        value=_format_value(calc, key),
                        tooltip=_value_source(item, key, calc, antenna_data),
                        css_class=css,
                    )
                )
        rows.append(
            EfficiencyRow(
                label_html=label_html,
                unit_html=unit_html,
                tooltip=tooltip,
                cells=cells,
                css_class="eff-row" if key == "eta" else "",
            )
        )

    return EfficiencyTable(
        columns=band_columns,
        rows=rows,
        empty_message=f"Keine Banddaten vorhanden ({DIRECTORY_S1P_RESULTS} fehlt oder ist leer).",
    )
