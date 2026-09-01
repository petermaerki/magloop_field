import html
import os
import pathlib
from collections.abc import Callable

from antennenvergleich import constants_s1p
from antennenvergleich.datatype_inductance import Inductance
from antennenvergleich.datatypes_s1p import S1pValues
from magloop_field.calculations import AntennaCalculator as FieldAntennaCalculator

from .constants import DIRECTORY_SRC


def build_inductance_section_html(
    output_subdir: pathlib.Path,
    antenna_dir: pathlib.Path,
    antenna_data: object | None,
    first_values_with_model: S1pValues | None,
    antenna_dir_name: str,
    rewrite_local_links: Callable[[str, pathlib.Path, pathlib.Path], str],
) -> str:
    """Generate the complete inductance section HTML.

    Returns the full inductance section including header, or empty string if no data.
    """
    assert isinstance(first_values_with_model, S1pValues | None)
    inductivity_values_html = ""
    inductivity_text_html = ""
    inductivity_pictures_html = ""

    inductance_file = output_subdir / "inductance.py"
    if not inductance_file.exists():
        return ""

    inductance = Inductance.read_values_file(filename=inductance_file)

    inductivity_text_file = (
        DIRECTORY_SRC / "shared" / "inductivity" / "inductivity.html"
    )
    inductivity_text_html = inductivity_text_file.read_text(encoding="utf-8")
    inductivity_text_html = rewrite_local_links(
        inductivity_text_html,
        fragment_dir=inductivity_text_file.parent,
        destination_dir=antenna_dir,
    )

    try:
        picture_rel_paths = tuple(
            getattr(antenna_data, "inductivity_pictures", ()) or ()
        )
        picture_caption_html = str(
            getattr(antenna_data, "inductivity_pictures_caption_str", "") or ""
        ).strip()
        if picture_rel_paths:
            image_tags: list[str] = []
            for picture_rel in picture_rel_paths:
                pic_path = output_subdir.parent / picture_rel
                if not pic_path.is_file():
                    continue
                rel_to_antenna = pathlib.Path(
                    os.path.relpath(pic_path, antenna_dir)
                ).as_posix()
                alt = html.escape(f"Inductivity picture: {pic_path.name}", quote=True)
                src = html.escape(rel_to_antenna, quote=True)
                figure_html = (
                    "<figure>"
                    f'<a href="{src}"><img class="inductivity-picture" src="{src}" alt="{alt}"></a>'
                )
                if picture_caption_html:
                    figure_html += f"<figcaption>{picture_caption_html}</figcaption>"
                figure_html += "</figure>"
                image_tags.append(figure_html)
            if image_tags:
                inductivity_pictures_html = (
                    '<div class="inductivity-pictures">'
                    + "".join(image_tags)
                    + "</div>"
                )
    except Exception as exc:  # pragma: no cover - best effort for optional section
        print(
            f"Warnung: Induktivitaets-Bilder konnten nicht geladen werden ({antenna_dir_name}): {exc}"
        )

    l_h_geometry_value: float | None = None
    if antenna_data is not None and first_values_with_model is not None:
        try:
            calc = FieldAntennaCalculator(
                D_m=antenna_data.D_m.value,
                d_m=antenna_data.d_m.value,
                n=antenna_data.n.value if antenna_data.n.value is not None else 1,
                p_m=antenna_data.p_m.value or 0.0,
                swr_min=first_values_with_model.swr_values.swr_min,
                f_Hz=first_values_with_model.model.f0_Hz,
                bw262_Hz=first_values_with_model.model.BSWR2_62_Hz,
                powerPfwd_W=100.0,
            )
            l_h_geometry_value = float(calc.L_H)
        except Exception as exc:  # pragma: no cover - best effort for optional section
            print(
                f"Warnung: L_H aus Geometrie konnte nicht berechnet werden ({antenna_dir_name}): {exc}"
            )

    if (
        l_h_geometry_value is not None
        or inductance.l_100p_h_value is not None
        or inductance.l_560p_h is not None
        or inductance.cap_nix_f is not None
    ):

        def fmt_sig4(value: float | None) -> str:
            if isinstance(value, (int, float)):
                return f"{value:.4g}"
            return "n/a"

        def deviation_percent(measured: float | None, reference: float | None) -> str:
            if measured is None or reference is None or reference == 0:
                return "n/a"
            return f"{((measured - reference) / reference * 100.0):+.0f}%"

        def highlight_deviation_text(text: str) -> str:
            escaped = html.escape(text)
            if text in {"+4%", "+6%"}:
                return f"<span class='hl-yellow'>{escaped}</span>"
            return escaped

        def highlight_inductance_value_text(value: float | None) -> str:
            return f"<span class='hl-yellow'>{html.escape(fmt_sig4(value))}</span>"

        def plain_mhz_text(value: float | None) -> str:
            if value is None:
                return ""
            return html.escape(f"{value / 1_000_000.0:.6f}")

        def plain_pf_text(value: float | None) -> str:
            if value is None:
                return ""
            return html.escape(f"{value * 1e12:.1f}")

        rows_html: list[str] = []
        if inductance.f_nix_hz is not None:
            rows_html.append(
                "<tr>"
                "<td>f<sub>NIX</sub></td>"
                f"<td class='val'>{plain_mhz_text(inductance.f_nix_hz)}</td>"
                "<td class='unit'>MHz</td>"
                "<td>Resonance frequency with no additional capacitors connected.</td>"
                "</tr>"
            )

        if inductance.f_off_hz is not None:
            rows_html.append(
                "<tr>"
                "<td>f<sub>OFF</sub></td>"
                f"<td class='val'>{plain_mhz_text(inductance.f_off_hz)}</td>"
                "<td class='unit'>MHz</td>"
                "<td>Capacitors and switches are physically connected at the antenna capacitor.<br>A small parasitic capacitance from wiring and switches lowers the resonance frequency.</td>"
                "</tr>"
            )

        if inductance.f_100p_hz is not None:
            rows_html.append(
                "<tr>"
                "<td>f<sub>100</sub></td>"
                f"<td class='val'>{plain_mhz_text(inductance.f_100p_hz)}</td>"
                "<td class='unit'>MHz</td>"
                "<td>Resonance frequency with an additional 100 pF capacitor switched in.</td>"
                "</tr>"
            )

        if inductance.f_560p_hz is not None:
            rows_html.append(
                "<tr>"
                "<td>f<sub>560</sub></td>"
                f"<td class='val'>{plain_mhz_text(inductance.f_560p_hz)}</td>"
                "<td class='unit'>MHz</td>"
                "<td>Resonance frequency with an additional 560 pF capacitor switched in.</td>"
                "</tr>"
            )

        rows_html.append(
            "<tr>"
            "<td>C<sub>100</sub></td>"
            f"<td class='val'>{plain_pf_text(constants_s1p.C_100P_F)}</td>"
            "<td class='unit'>pF</td>"
            "<td>Additional capacitance used for the 100 pF branch.</td>"
            "</tr>"
        )

        rows_html.append(
            "<tr>"
            "<td>C<sub>560</sub></td>"
            f"<td class='val'>{plain_pf_text(constants_s1p.C_560P_F)}</td>"
            "<td class='unit'>pF</td>"
            "<td>Additional capacitance used for the 560 pF branch.</td>"
            "</tr>"
        )

        if l_h_geometry_value is not None:
            rows_html.append(
                "<tr>"
                "<td>L</td>"
                f"<td class='val'>{highlight_inductance_value_text(l_h_geometry_value)}</td>"
                "<td class='unit'>H</td>"
                "<td>Calculated from geometry of the main loop.</td>"
                "</tr>"
            )

        dev_100 = deviation_percent(inductance.l_100p_h, l_h_geometry_value)
        dev_100_html = highlight_deviation_text(dev_100)
        rows_html.append(
            "<tr>"
            "<td>L<sub>100</sub></td>"
            f"<td class='val'>{highlight_inductance_value_text(inductance.l_100p_h)}</td>"
            "<td class='unit'>H</td>"
            f"<td>Derived from the resonance frequencies f<sub>OFF</sub> and f<sub>100</sub><br>deviation {dev_100_html} vs L</td>"
            "</tr>"
        )

        dev_560 = deviation_percent(inductance.l_560p_h, l_h_geometry_value)
        dev_560_html = highlight_deviation_text(dev_560)
        rows_html.append(
            "<tr>"
            "<td>L<sub>560</sub></td>"
            f"<td class='val'>{highlight_inductance_value_text(inductance.l_560p_h)}</td>"
            "<td class='unit'>H</td>"
            f"<td>Derived from the resonance frequencies f<sub>OFF</sub> and f<sub>560</sub><br>deviation {dev_560_html} vs L</td>"
            "</tr>"
        )

        if inductance.c_nix_f is not None:
            rows_html.append(
                "<tr>"
                "<td>C<sub>NIX</sub></td>"
                f"<td class='val'>{html.escape(fmt_sig4(inductance.c_nix_f))}</td>"
                "<td class='unit'>As/V</td>"
                "<td>Derived from using L<sub>100</sub>, f<sub>OFF</sub>, and f<sub>NIX</sub><br>estimated parasitic capacitance of switches and wiring; expected value 1 ... 5 pF</td>"
                "</tr>"
            )

        deviations = []
        for measured in (inductance.l_100p_h, inductance.l_560p_h):
            if measured is not None and l_h_geometry_value not in (None, 0):
                deviations.append(
                    (measured - l_h_geometry_value) / l_h_geometry_value * 100.0
                )

        summary_html = ""
        if deviations:
            max_deviation = max(deviations, key=lambda value: abs(value))
            max_deviation_text = f"{max_deviation:+.0f}%"
            max_deviation_html = highlight_deviation_text(max_deviation_text)
            summary_html = (
                "<p>"
                "The maximum deviation between L and the capacitor-based L<sub>1x</sub> values "
                f"is {max_deviation_html}. "
                "This is considered a small deviation and is accepted. "
                "L is used for the calculations of the antenna efficiency."
                "</p>"
            )

        inductivity_values_html = (
            '<table class="compact">'
            "<tbody>"
            f"{''.join(rows_html)}"
            "</tbody>"
            "</table>"
            f"{summary_html}"
        )

    if inductivity_values_html or inductivity_pictures_html:
        return (
            "<h2>Inductance</h2>\n"
            f"{inductivity_text_html}\n"
            f"{inductivity_pictures_html}\n"
            '<p class="section-label"> </p>\n'
            f"{inductivity_values_html}"
        )

    return ""
