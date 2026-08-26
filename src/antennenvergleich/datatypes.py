"""Shared antenna data structures and discovery logic."""

import importlib
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from antennenvergleich.constants_s1p import (
    CAP_VALUES_TAGS,
    RESULTS_SUBDIR,
    SKIP_VALUES_FILENAME_SUFFIX,
    VALUES_SUFFIX,
)


def _is_cap_values_file(path: Path) -> bool:
    stem_u = path.stem.upper()
    return any(tag in stem_u for tag in CAP_VALUES_TAGS)


class VnaCalibration(str, Enum):
    ANTENNA_FEED_POINT = "antenna_feed_point"
    AT_VNA = "at_vna"


@dataclass(frozen=True)
class FloatText:
    """Ein Messwert oder Spezifikationswert mit Quellenangabe."""

    value: float | None
    source: str | None = None


@dataclass(frozen=True)
class IntText:
    """Ein ganzzahliger Wert oder Spezifikationswert mit Quellenangabe."""

    value: int | None
    source: str | None = None

    def __post_init__(self) -> None:
        if self.value is not None:
            assert isinstance(self.value, int) and not isinstance(self.value, bool)


@dataclass(frozen=True)
class BandData:
    """Messdaten für ein Frequenzband."""

    f_Hz: FloatText
    bw262_Hz: FloatText
    swr_min: FloatText


@dataclass(frozen=True)
class AntennaPlusDirectory:
    antenna: "Antenna"
    directory: Path

    def enrich_s1p(self) -> None:
        """
        Append fitted S1P band data from this antenna's s1p_results files.
        """
        for values_path in self._iter_values_files(self.directory):
            values = Antenna._read_values_file(values_path)
            if values.model is None:
                continue
            self.antenna.bands.append(values.band_data)

    @staticmethod
    def _iter_values_files(antenna_dir: Path):
        results_dir = antenna_dir / RESULTS_SUBDIR
        if not results_dir.is_dir():
            return

        for values_path in sorted(results_dir.rglob(f"*{VALUES_SUFFIX}.py")):
            if values_path.name.endswith(SKIP_VALUES_FILENAME_SUFFIX):
                continue
            if _is_cap_values_file(values_path):
                continue
            yield values_path


@dataclass(frozen=True)
class Antenna:
    """Antennendaten: Geometrie und gemessene/herstellerangegebene Bandbreiten pro Band."""

    D_m: FloatText
    d_m: FloatText
    n: IntText
    p_m: FloatText
    info_str: str
    info_enviroment_str: str
    info_conductor_str: str
    info_capacitor_str: str
    powerP_W: FloatText
    color: str = "#000000"
    name: str = ""
    call: str = ""
    selection_brand: str = "-"
    selection_location: str = "-"
    selection_name: str = "-"
    info_thanks_str: str = ""
    vna_calibration: VnaCalibration = VnaCalibration.AT_VNA
    measurement_html: tuple[str, ...] = field(default_factory=tuple)
    enviroment_html: tuple[str, ...] = field(default_factory=tuple)
    overview_pictures: tuple[str, ...] = field(default_factory=tuple)
    inductivity_pictures: tuple[str, ...] = field(default_factory=tuple)
    bands: list[BandData] = field(default_factory=list)

    def __post_init__(self) -> None:
        value = self.vna_calibration

        def assert_selection(v: str) -> None:
            assert v == v.strip(), self.antenna_label
            assert len(v) > 0, self.antenna_label

        assert_selection(self.selection_brand)
        assert_selection(self.selection_name)
        assert_selection(self.selection_location)

        if isinstance(value, str):
            try:
                object.__setattr__(self, "vna_calibration", VnaCalibration(value))
            except ValueError as exc:
                raise ValueError(
                    "vna_calibration must be 'antenna_feed_point' or 'at_vna'"
                ) from exc
        elif not isinstance(value, VnaCalibration):
            raise TypeError("vna_calibration must be VnaCalibration or str")

    @property
    def antenna_label(self) -> str:
        return " ".join(
            (
                self.selection_brand,
                self.selection_name,
                self.selection_location,
            )
        )

    @staticmethod
    def _read_values_file(values_file: Path):
        from antennenvergleich.datatypes_s1p import (
            AntennaModelFit,
            SwrValues,
            ValuesDataFile,
        )

        directory_src = Path(__file__).resolve().parent.parent
        try:
            relative_py = values_file.resolve().relative_to(directory_src)
        except ValueError as exc:
            raise RuntimeError(
                f"{values_file} liegt nicht unter {directory_src}"
            ) from exc

        module_name = ".".join(relative_py.with_suffix("").parts)
        module = importlib.import_module(module_name)
        module = importlib.reload(module)

        swr_values = getattr(module, "swr_values", None)
        model = getattr(module, "model", None)

        if not isinstance(swr_values, SwrValues):
            raise TypeError(f"{values_file.name}: swr_values hat unerwarteten Typ")
        if model is not None and not isinstance(model, AntennaModelFit):
            raise TypeError(f"{values_file.name}: model hat unerwarteten Typ")

        return ValuesDataFile(swr_values=swr_values, model=model)
