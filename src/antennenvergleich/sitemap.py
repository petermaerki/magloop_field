from __future__ import annotations

from html import escape
from pathlib import Path

from . import constants, loop_directories

SITEMAP_FILENAME = "sitemap.xml"
DEFAULT_BASE_URL = "https://petermaerki.github.io/magloop_field/"


def _build_urls(
    antenna_entries: list[loop_directories.AntennaPlusDirectory],
    base_url: str,
) -> list[str]:
    base = base_url.rstrip("/")
    repo = constants.DIRECTORY_REPO

    urls = [f"{base}/", f"{base}/generated_compare.html"]

    seen = set(urls)
    for entry in antenna_entries:
        generated_html = entry.directory / "generated_antenna.html"
        if not generated_html.is_file():
            continue
        rel_path = generated_html.relative_to(repo).as_posix()
        url = f"{base}/{rel_path}"
        if url not in seen:
            seen.add(url)
            urls.append(url)

    return urls


def _render_xml(urls: list[str]) -> str:
    lines = [
        "<?xml version='1.0' encoding='UTF-8'?>",
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for url in urls:
        lines.extend(["  <url>", f"    <loc>{escape(url)}</loc>", "  </url>"])
    lines.append("</urlset>")
    return "\n".join(lines) + "\n"


def write_sitemap(
    antenna_entries: list[loop_directories.AntennaPlusDirectory],
    *,
    base_url: str = DEFAULT_BASE_URL,
    output_file: Path | None = None,
) -> Path:
    # The draft antennas should NOT be part of sitemap.xml
    antenna_entries = [e for e in antenna_entries if not e.antenna.ctl_draft]

    target = output_file or (constants.DIRECTORY_REPO / SITEMAP_FILENAME)
    urls = _build_urls(antenna_entries=antenna_entries, base_url=base_url)
    xml = _render_xml(urls=urls)
    target.write_text(xml, encoding="utf-8")
    return target


def main() -> None:
    entries = loop_directories.get_antennen_daten()
    output = write_sitemap(entries)
    print(f"Written: {output}")


if __name__ == "__main__":
    main()
