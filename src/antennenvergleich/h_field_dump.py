import dataclasses
import html
import pathlib

from antennenvergleich.constants import C_LIGHT_MS
from antennenvergleich.datatypes import Antenna, AntennaPlusDirectory
from antennenvergleich.h_field_analysis import (
    FeedlineSegment,
    calculate_feedline_losses,
    expected_h_field_at_point,
    measured_h_field_and_factor,
    power_after_loss_db,
    select_closest_band,
)
from magloop_field.calculations import AntennaCalculator


@dataclasses.dataclass(frozen=True)
class HFieldMesspunkt:
    punkt_str: str
    f_Hz: float
    tx_power_w: float
    X_m: float
    Y_m: float
    Z_m: float
    P_dbm: float


@dataclasses.dataclass
class _FrequencyTables:
    f_hz: float
    summary_rows: list[tuple[str, str]]
    point_rows: list[dict[str, float | str]]


@dataclasses.dataclass(frozen=True)
class HFieldData:
    this_antenna_dir: pathlib.Path
    antennendaten: Antenna

    cables: list[FeedlineSegment]

    connectors_count: int
    connector_loss_db: float

    messpunkte: tuple[HFieldMesspunkt, ...] = ()

    # Legacy single-point fields (kept for backward compatibility)
    f_Hz: float | None = None
    A_X_m: float | None = None
    A_Y_m: float | None = None
    A_Z_m: float | None = None
    tx_power_w: float | None = None
    P_dbm: float | None = None

    def _iter_messpunkte(self) -> tuple[HFieldMesspunkt, ...]:
        if self.messpunkte:
            return self.messpunkte

        if (
            self.f_Hz is None
            or self.tx_power_w is None
            or self.A_X_m is None
            or self.A_Y_m is None
            or self.A_Z_m is None
            or self.P_dbm is None
        ):
            raise ValueError(
                "Either messpunkte must be provided or all legacy single-point fields must be set."
            )

        return (
            HFieldMesspunkt(
                punkt_str="single",
                f_Hz=self.f_Hz,
                tx_power_w=self.tx_power_w,
                X_m=self.A_X_m,
                Y_m=self.A_Y_m,
                Z_m=self.A_Z_m,
                P_dbm=self.P_dbm,
            ),
        )

    def print(self) -> None:
        # Antenna data from project files (geometry from HB0SM, band data from datasheet).
        # Same mechanism as run_2_html.py: enrich local antenna with fitted s1p_results.
        entry = AntennaPlusDirectory(antenna=self.antennendaten, directory=self.this_antenna_dir)
        entry.enrich_s1p()
        ant_datasheet = entry.antenna

        antenna_D_m = self.antennendaten.D_m.value
        antenna_d_m = self.antennendaten.d_m.value
        antenna_n = self.antennendaten.n.value
        antenna_p_m = self.antennendaten.p_m.value

        if not ant_datasheet.bands:
            raise ValueError(
                "No band data found in antennendaten.py and s1p_results"
            )

        sections_by_frequency: dict[float, _FrequencyTables] = {}
        frequency_sections: list[_FrequencyTables] = []

        for messpunkt in self._iter_messpunkte():
            print(f"=== Messpunkt {messpunkt.punkt_str} ===")

            losses_db, attenuation_cables_connectors_total_dbm = calculate_feedline_losses(
                f_hz=messpunkt.f_Hz,
                cables=self.cables,
                connectors_count=self.connectors_count,
                connector_loss_db=self.connector_loss_db,
            )

            for cable in self.cables:
                print(f"cable_a_loss_db: {losses_db[cable.name]:.4f} dB")
            print(f"connectors_loss_db: {losses_db['connectors']:.4f} dB")
            print(
                f"attenuation_cables_connectors_total_dbm: {attenuation_cables_connectors_total_dbm:.4f} dB"
            )

            tx_after_cable_w = power_after_loss_db(
                tx_power_w=messpunkt.tx_power_w,
                total_loss_db=attenuation_cables_connectors_total_dbm,
            )
            print(f"tx_after_cable_w: {tx_after_cable_w:.3f} W")

            closest_band = select_closest_band(antenna=ant_datasheet, f_hz=messpunkt.f_Hz)
            antenna_swr_min = closest_band.swr_min.value
            antenna_bw262_hz = closest_band.bw262_Hz.value

            r_m = (messpunkt.X_m**2 + messpunkt.Y_m**2 + messpunkt.Z_m**2) ** 0.5
            kr = 2.0 * 3.141592653589793 * messpunkt.f_Hz * r_m / C_LIGHT_MS

            debug_calc = AntennaCalculator(
                D_m=antenna_D_m,
                d_m=antenna_d_m,
                n=antenna_n,
                p_m=antenna_p_m,
                swr_min=antenna_swr_min,
                f_Hz=messpunkt.f_Hz,
                bw262_Hz=antenna_bw262_hz,
                powerP_W=tx_after_cable_w,
            )

            print("--- debug_h_field_inputs ---")
            print(
                f"closest_band_f_Hz: {closest_band.f_Hz.value:.1f} (source: {closest_band.f_Hz.source})"
            )
            print(
                f"closest_band_bw262_Hz: {closest_band.bw262_Hz.value:.6f} (source: {closest_band.bw262_Hz.source})"
            )
            print(
                f"closest_band_swr_min: {closest_band.swr_min.value:.6f} (source: {closest_band.swr_min.source})"
            )
            print(
                f"antenna_D_m: {antenna_D_m:.6f}, antenna_d_m: {antenna_d_m:.6f}, n: {antenna_n}, p_m: {antenna_p_m:.6f}"
            )
            print(
                f"point_xyz_m: ({messpunkt.X_m:.6f}, {messpunkt.Y_m:.6f}, {messpunkt.Z_m:.6f}), r_m: {r_m:.6f}, kr: {kr:.6f}"
            )
            print(f"tx_after_cable_w: {tx_after_cable_w:.6f}")
            print(
                f"I_main_loop_A: {debug_calc.I_main_loop_A:.6f}, m_Am2: {debug_calc.m_Am2:.6f}"
            )
            print("--- /debug_h_field_inputs ---")

            h_field_expected_A_m = expected_h_field_at_point(
                antenna_D_m=antenna_D_m,
                antenna_d_m=antenna_d_m,
                antenna_n=antenna_n,
                antenna_p_m=antenna_p_m,
                swr_min=antenna_swr_min,
                bw262_hz=antenna_bw262_hz,
                f_hz=messpunkt.f_Hz,
                power_into_antenna_w=tx_after_cable_w,
                x_m=messpunkt.X_m,
                y_m=messpunkt.Y_m,
                z_m=messpunkt.Z_m,
            )
            print(f"h_field_expected_A_m: {h_field_expected_A_m:.6f} A/m")

            h_field_measured_A_m, h_field_factor_measured_to_expected = (
                measured_h_field_and_factor(
                    p_dbm=messpunkt.P_dbm,
                    f_hz=messpunkt.f_Hz,
                    expected_h_field_a_m=h_field_expected_A_m,
                )
            )
            print(f"h_field_measured_A_m: {h_field_measured_A_m:.6f} A/m")
            print(
                f"h_field_factor_measured_to_expected: {h_field_factor_measured_to_expected:.3f}"
            )

            section = sections_by_frequency.get(messpunkt.f_Hz)
            if section is None:
                section = _FrequencyTables(
                    f_hz=messpunkt.f_Hz,
                    summary_rows=[],
                    point_rows=[],
                )
                sections_by_frequency[messpunkt.f_Hz] = section
                frequency_sections.append(section)

            if not section.summary_rows:
                section.summary_rows = [
                    ("tx_power_w", f"{messpunkt.tx_power_w:.1f}"),
                    ("f_Hz", f"{messpunkt.f_Hz:.0f}"),
                    (
                        "attenuation_cables_connectors_total_dbm",
                        f"{attenuation_cables_connectors_total_dbm:.2f} dB",
                    ),
                    ("tx_after_cable_w", f"{tx_after_cable_w:.1f}"),
                    ("I_main_loop_A", f"{debug_calc.I_main_loop_A:.1f}"),
                    ("magnetic dipole moment m (Am2)", f"{debug_calc.m_Am2:.1f}"),
                ]

            section.point_rows.append(
                {
                    "punkt": messpunkt.punkt_str,
                    "x_m": messpunkt.X_m,
                    "y_m": messpunkt.Y_m,
                    "z_m": messpunkt.Z_m,
                    "expected_a_m": h_field_expected_A_m,
                    "measured_a_m": h_field_measured_A_m,
                    "factor": h_field_factor_measured_to_expected,
                }
            )

        self._write_measurements_html(frequency_sections=frequency_sections)

    def _write_measurements_html(
        self,
        frequency_sections: list[_FrequencyTables],
    ) -> None:
        out_path = (
            self.this_antenna_dir / "h_field" / "h_field_measurements_generated.html"
        )

        sections_html = ""
        for section in frequency_sections:
            summary_html = "".join(
                (
                    "<tr>"
                    f"<td>{html.escape(label)}</td>"
                    f"<td>{html.escape(value)}</td>"
                    "</tr>"
                )
                for label, value in section.summary_rows
            )

            points_html = "".join(
                (
                    "<tr>"
                    f"<td class='point-col'>{html.escape(str(row['punkt']))}</td>"
                    f"<td>{float(row['x_m']):.1f}</td>"
                    f"<td>{float(row['y_m']):.1f}</td>"
                    f"<td>{float(row['z_m']):.1f}</td>"
                    f"<td>{float(row['expected_a_m']):.4f}</td>"
                    f"<td>{float(row['measured_a_m']):.4f}</td>"
                    f"<td class='hl-factor'>{float(row['factor']):.3f}</td>"
                    "</tr>"
                )
                for row in section.point_rows
            )

            sections_html += (
                f"<h4>f = {section.f_hz / 1e6:.3f} MHz</h4>\n"
                "<table class='h-field-summary'>"
                f"{summary_html}"
                "</table>\n"
                "<table class='measure-table'>"
                "<thead>"
                "<tr class='head-row'><th class='point-col'></th><th>X</th><th>Y</th><th>Z</th><th>expected</th><th>measured</th><th>factor</th></tr>"
                "<tr class='head-row'><th class='point-col'></th><th>m</th><th>m</th><th>m</th><th>A/m</th><th>A/m</th><th></th></tr>"
                "</thead>"
                "<tbody>"
                f"{points_html}"
                "</tbody>"
                "</table>\n"
            )

        doc = (
            "<!-- Automatically generated file by h_field_dump.py. Do not edit manually. -->\n"
            f"{sections_html}"
        )
        out_path.write_text(doc, encoding="utf-8")

