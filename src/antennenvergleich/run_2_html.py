"""Generates compare.html — comparison table for magnetic loop antennas."""

from . import constants, loop_directories, renderer_html, webui_filter


def main() -> None:
    antenna_entries = loop_directories.get_antennen_daten()

    for entry in antenna_entries:
        entry.enrich_s1p()

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

    generated_antennas = renderer_html._generate_antenna_html_files()
    print(f"Antenna HTML files generated/updated: {generated_antennas}")

    antennas = [entry.antenna for entry in antenna_entries]
    color_map = webui_filter.build_color_map_from_entries(antenna_entries)

    html_renderer = renderer_html.HtmlRenderer(color_map=color_map)
    html_renderer.render(antenna_entries)

    html = html_renderer.close()
    filename = constants.DIRECTORY_REPO / "generated_compare.html"
    filename.write_text(html, encoding="utf-8")
    print(f"Written: {filename}")

    svg = renderer_html.Diagramm_eta_f_svg().render(antennas, color_map=color_map)
    filename_svg = constants.DIRECTORY_REPO / renderer_html.FILENAME_SVG_ETA_F
    filename_svg.write_text(svg, encoding="utf-8")
    print(f"Written: {filename_svg}")

    svg = renderer_html.Diagramm_eta_D_lambda_svg().render(
        antennas, color_map=color_map
    )
    filename_svg = constants.DIRECTORY_REPO / renderer_html.FILENAME_SVG_ETA_DL
    filename_svg.write_text(svg, encoding="utf-8")
    print(f"Written: {filename_svg}")


if __name__ == "__main__":
    main()
