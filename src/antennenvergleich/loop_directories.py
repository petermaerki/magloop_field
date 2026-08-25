import importlib
import pathlib

from antennenvergleich.constants import ANTENNENDATEN_FILENAME
from antennenvergleich.datatypes import AntennaPlusDirectory

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent
DIRECTORY_ANTENNEN = DIRECTORY_OF_THIS_FILE.parent / "antennen"
assert DIRECTORY_ANTENNEN.is_dir(), DIRECTORY_ANTENNEN

def get_antennen_daten() -> list[AntennaPlusDirectory]:
    antennas: list[AntennaPlusDirectory] = []
    for directory in get_antennen_directories():
        module = importlib.import_module(f"antennen.{directory.name}.antennendaten")
        antennas.append(
            AntennaPlusDirectory(
                antenna=module.ANTENNENDATEN,
                directory=directory,
            )
        )
    return antennas


def get_antennen_modules() -> list:
    return [
        importlib.import_module(f"antennen.{d.name}.antennendaten")
        for d in get_antennen_directories()
    ]


def get_antennen_directories() -> list[pathlib.Path]:
    directories: list[pathlib.Path] = []
    for dir_antenne in DIRECTORY_ANTENNEN.iterdir():
        file_antennendaten = dir_antenne / ANTENNENDATEN_FILENAME
        if not file_antennendaten.is_file():
            continue
        directories.append(dir_antenne)
    directories.sort()
    return directories


def main() -> None:
    # for antennendaten in get_antennen_modules():
    #     print(f"{antennendaten.__file__}: {antennendaten.ANTENNENDATEN.name}")
    for entry in get_antennen_daten():
        entry.enrich_s1p()
        print(f"{entry.antenna.name}")


if __name__ == "__main__":
    main()
