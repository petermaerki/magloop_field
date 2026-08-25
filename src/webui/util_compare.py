from antennenvergleich import loop_directories, renderer_html, webui_filter


class FilterWrapper:
    def __init__(self) -> str:
        self.antenna_entries = loop_directories.get_antennen_daten()
        self.filtered_antenna_entries = self.antenna_entries

        # Filter
        antenna_joins = webui_filter.get_antenna_joins(
            antenna_entries=self.antenna_entries
        )
        self.filter = webui_filter.Filter(antenna_joins=antenna_joins)

    def apply_filter(self) -> None:
        self.filtered_antenna_entries = [
            a
            for a in self.antenna_entries
            if a.directory in self.filter.set_antenna_dir
        ]
        print(f"apply_filter() {len(self.filtered_antenna_entries)} remaining")

    def render_results_html(self) -> str:
        html_renderer = renderer_html.HtmlRenderer()

        for band in renderer_html.BAND_ORDER:
            antennas_in_band = renderer_html.get_antennas_in_band(
                self.filtered_antenna_entries, band
            )
            if len(antennas_in_band) == 0:
                continue
            html_renderer.render(band, antennas_in_band)
        html = html_renderer.close()

        return html

    def render_eta_f_svg(self) -> str:
        antennas = [entry.antenna for entry in self.filtered_antenna_entries]

        return renderer_html.Diagramm_eta_f_svg().render(antennas)
