from antennenvergleich import loop_directories, renderer_html, webui_filter


def render_html() -> str:
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

    html_renderer = renderer_html.HtmlRenderer()
    for band in renderer_html.BAND_ORDER:
        antennas_in_band = renderer_html.get_antennas_in_band(antenna_entries, band)
        if len(antennas_in_band) == 0:
            continue
        html_renderer.render(band, antennas_in_band)
    html = html_renderer.close()

    return html
