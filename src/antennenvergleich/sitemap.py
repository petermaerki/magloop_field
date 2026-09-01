from __future__ import annotations

from datetime import datetime, timezone
from html import escape
from pathlib import Path

from . import constants, loop_directories

SITEMAP_FILENAME = "sitemap.xml"
DEFAULT_BASE_URL = "https://petermaerki.github.io/magloop_field/"


def _build_public_urls(
    antenna_entries: list[loop_directories.AntennaPlusDirectory],
    base_url: str,
) -> list[str]:
    base = base_url.rstrip("/")

    relative_paths: list[str] = [
        "",
        "index.html?page=calculator",
        "index.html?page=compare",
        "generated_compare.html",
    ]

    for entry in antenna_entries:
        generated_html = entry.directory / "generated_antenna.html"
        if not generated_html.is_file():
            continue
        rel_path = generated_html.relative_to(constants.DIRECTORY_REPO).as_posix()
        relative_paths.append(rel_path)

    unique_urls: list[str] = []
    seen: set[str] = set()
    for rel_path in relative_paths:
        url = f"{base}/" if rel_path == "" else f"{base}/{rel_path}"
        if url in seen:
            continue
        seen.add(url)
        unique_urls.append(url)

    return unique_urls


def _render_xml(urls: list[str], lastmod: str) -> str:
    lines = [
        "<?xml version='1.0' encoding='UTF-8'?>",
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for url in urls:
        lines.extend(
            [
                "  <url>",
                f"    <loc>{escape(url)}</loc>",
                f"    <lastmod>{lastmod}</lastmod>",
                "  </url>",
            ]
        )
    lines.append("</urlset>")
    return "\n".join(lines) + "\n"


def write_sitemap(
    antenna_entries: list[loop_directories.AntennaPlusDirectory],
    *,
    base_url: str = DEFAULT_BASE_URL,
    output_file: Path | None = None,
) -> Path:
    target = output_file or (constants.DIRECTORY_REPO / SITEMAP_FILENAME)
    urls = _build_public_urls(antenna_entries=antenna_entries, base_url=base_url)
    lastmod = datetime.now(timezone.utc).date().isoformat()
    xml = _render_xml(urls=urls, lastmod=lastmod)
    target.write_text(xml, encoding="utf-8")
    return target


def main() -> None:
    entries = loop_directories.get_antennen_daten()
    output = write_sitemap(entries)
    print(f"Written: {output}")


if __name__ == "__main__":
    main()
