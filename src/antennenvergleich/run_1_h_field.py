"""Run all antenna h_field_data modules sequentially."""

from __future__ import annotations

from pathlib import Path

from antennenvergleich . h_field_dump import HFieldData

from antennenvergleich import loop_directories


def _iter_h_field_files() -> list[Path]:
    h_field_files: list[Path] = []
    for antenna_dir in loop_directories.get_antennen_directories():
        h_field_data_file = antenna_dir / "h_field" / "h_field_data.py"
        if not h_field_data_file.is_file():
            continue
        h_field_files.append(h_field_data_file)
    return h_field_files


def _log_path_for_h_field_file(h_field_data_file: Path) -> Path:
    return h_field_data_file.with_name("h_field_measurements_generated.log")


def main() -> None:
    h_field_files = _iter_h_field_files()
    assert h_field_files, "no h_field_data.py files found"

    for h_field_data_file in h_field_files:
        h_field_data= HFieldData.read_values_file(filename= h_field_data_file)
        print(f"run_1_h_field.py {h_field_data_file.parent.parent.name}", flush=True)
        log_path = _log_path_for_h_field_file(h_field_data_file)
        with log_path.open("w", encoding="utf-8") as out:
            h_field_data.print(out=out)


if __name__ == "__main__":
    main()
