"""CLI entrypoint for Ninja page generation."""

from __future__ import annotations

import argparse

from . import loader, render


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--antenna-dir",
        help=(
            "Optional: antenna directory name under src/antennen/ or absolute path. "
            "If omitted, all antennas are generated."
        ),
    )
    args = parser.parse_args()

    if args.antenna_dir:
        antenna_dir = loader.resolve_antenna_dir(args.antenna_dir)
        output_file = render.generate_one(antenna_dir)
        print(f"Written: {output_file}")
        print("Ninja pages generated: 1")
        return

    count = 0
    for antenna_dir in loader.iter_antenna_dirs():
        output_file = render.generate_one(antenna_dir)
        print(f"Written: {output_file}")
        count += 1

    print(f"Ninja pages generated: {count}")
