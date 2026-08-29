"""Generates compare.html — comparison table for magnetic loop antennas."""

from . import (
    constants,
    loop_directories,
    renderer_antenna_html,
    renderer_compare_html,
    renderer_diagram_svg,
    webui_filter,
)


def _assert_unique_antenna_colors(
    antenna_entries: list[loop_directories.AntennaPlusDirectory],
) -> None:
    color_to_antennas: dict[str, list[str]] = {}
    for entry in antenna_entries:
        antenna = entry.antenna
        label = antenna.antenna_label
        color_to_antennas.setdefault(antenna.color, []).append(label)

    duplicates = {
        color: labels for color, labels in color_to_antennas.items() if len(labels) > 1
    }

    detail_lines = [
        f"  {color}: {', '.join(labels)}"
        for color, labels in sorted(duplicates.items())
    ]
    details = "\n".join(detail_lines)
    assert not duplicates, (
        "Duplicate antenna colors detected. "
        "Each antenna must have a unique color in antennendaten.py.\n"
        f"{details}"
    )


def main() -> None:
    antenna_entries = loop_directories.get_antennen_daten()

    for entry in antenna_entries:
        entry.enrich_s1p()

    if False:
        # Filter
        antenna_joins = webui_filter.get_antenna_joins(antenna_entries=antenna_entries)
        filter = webui_filter.Filter(antenna_joins=antenna_joins)
        print("\n=== FILTER DEBUG: initial state ===")
        filter.dump()

        # Manual checkbox toggles for text-based filter debugging.
        # Add or remove entries as needed for your experiments.
        debug_toggles: list[tuple[webui_filter.EnumCategory, str, bool]] = [
            (webui_filter.EnumCategory.BRAND, "Mazzoni", False),
            # (webui_filter.EnumCategory.NAME, "Baby", False),
            # (webui_filter.EnumCategory.LOCATION, "HB0SM", True),
            # (webui_filter.EnumCategory.BAND, "160m", True),
        ]

        for debug_category, debug_option_name, debug_checked in debug_toggles:
            category_stats = filter.find_category(debug_category)
            try:
                checkbox = category_stats.find_checkbox(debug_option_name)
                checkbox.set_checked(debug_checked)
                print(
                    "FILTER DEBUG toggle: "
                    f"{debug_category.name}/{debug_option_name} -> {debug_checked}"
                )
            except ValueError:
                available = ", ".join(cb.name for cb in category_stats.checkboxes)
                print(
                    "FILTER DEBUG warning: option not found "
                    f"({debug_category.name}/{debug_option_name}). "
                    f"Available: {available}"
                )
        filter.update_grey_states()

        print("\n=== FILTER DEBUG: after manual toggle ===")
        filter.dump()

        selected_dirs = sorted(str(path) for path in filter.set_antenna_dir)
        print(f"Remaining antennas after filter: {len(selected_dirs)}")
        for directory in selected_dirs:
            print(f"  {directory}")

        antenna_entries = [
            a for a in antenna_entries if a.directory in filter.set_antenna_dir
        ]

    _assert_unique_antenna_colors(antenna_entries)

    generated_antennas = renderer_antenna_html.generate_antenna_html_files()
    print(f"Antenna HTML files generated/updated: {generated_antennas}")

    antennas = [entry.antenna for entry in antenna_entries]

    html_renderer = renderer_compare_html.HtmlRenderer()
    html_renderer.render(antenna_entries)

    html = html_renderer.close(body_only=False)
    filename = constants.DIRECTORY_REPO / "generated_compare.html"
    filename.write_text(html, encoding="utf-8")
    print(f"Written: {filename}")

    svg = renderer_diagram_svg.Diagramm_eta_f_svg().render(antennas)
    filename_svg = constants.DIRECTORY_REPO / renderer_diagram_svg.FILENAME_SVG_ETA_F
    filename_svg.write_text(svg, encoding="utf-8")
    print(f"Written: {filename_svg}")

    svg = renderer_diagram_svg.Diagramm_eta_D_lambda_svg().render(antennas)
    filename_svg = constants.DIRECTORY_REPO / renderer_diagram_svg.FILENAME_SVG_ETA_DL
    filename_svg.write_text(svg, encoding="utf-8")
    print(f"Written: {filename_svg}")


if __name__ == "__main__":
    main()
