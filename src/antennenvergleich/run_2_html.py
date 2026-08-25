"""Generates compare.html — comparison table for magnetic loop antennas."""

from antennenvergleich import loop_directories, renderer_html, webui_filter


def main() -> None:
    antenna_entries = loop_directories.get_antennen_daten()

    if False:
        # Filter
        antenna_joins = webui_filter.get_antenna_joins(antenna_entries=antenna_entries)
        filter = webui_filter.Filter(antenna_joins=antenna_joins)
        filter.dump()
        # filter.update_level(webui_filter.EnumCategory.NAME, {"Baby", "Tubby indoor", "Tubby outdoor"})
        filter.update_level(webui_filter.EnumCategory.LOCATION, {"HB9ISP"})
        # filter.update_level(webui_filter.EnumCategory.BAND, {"160m"})
        filter.dump()
        antenna_entries = [
            a for a in antenna_entries if a.directory in filter.set_antenna_dir
        ]

    antennas = [entry.antenna for entry in antenna_entries]
    for entry in antenna_entries:
        entry.enrich_s1p()

    generated_antennas = renderer_html._generate_antenna_html_files()
    print(f"Antenna HTML files generated/updated: {generated_antennas}")

    html_renderer = renderer_html.HtmlRenderer()
    for band in renderer_html.BAND_ORDER:
        antennas_in_band = renderer_html.get_antennas_in_band(antenna_entries, band)
        # antennas_in_band = [a for a in antennas_in_band if a.antenna_dir in filter.set_antenna_dir]
        if len(antennas_in_band) == 0:
            continue
        html_renderer.render(band, antennas_in_band)
    html_renderer.close()

    renderer_html.Diagramm_eta_f_svg().render(antennas)
    renderer_html.Diagramm_eta_D_lambda_svg().render(antennas)


if __name__ == "__main__":
    main()
