import dataclasses
import importlib
import io
import pathlib

from antennenvergleich.constants import DIRECTORY_SRC
from antennenvergleich.datatypes import Antenna
from antennenvergleich.h_field_analysis import FeedlineSegment, db_per_m_from_points


@dataclasses.dataclass(frozen=True)
class VnaCableData:
    antennendaten: Antenna | None
    this_antenna_dir: pathlib.Path | None
    cables: list[FeedlineSegment]
    connectors_count: int
    connector_loss_db: float

    def alpha_db_at_f_hz(self, f_hz: float) -> float:
        total_db = 0.0
        for cable in self.cables:
            db_per_m = db_per_m_from_points(
                points=cable.points,
                unit=cable.unit,
                f_hz=f_hz,
            )
            total_db += db_per_m * cable.length_m
        return total_db

    def tau_ns_at_f_hz(self, f_hz: float) -> float:
        deltas_ns = 0.0
        for cable in self.cables:
            if cable.delay_ns_m is None:
                continue
            deltas_ns += cable.delay_ns_m * cable.length_m
        return deltas_ns

    @staticmethod
    def read_values_file(filename: pathlib.Path) -> "VnaCableData":
        relative_py = filename.resolve().relative_to(DIRECTORY_SRC)
        module_name = ".".join(relative_py.with_suffix("").parts)
        module = importlib.import_module(module_name)
        module = importlib.reload(module)

        cable_data = getattr(module, "vna_cable_data", None)
        if cable_data is None:
            raise TypeError(f"{filename.name}: vna_cable_data does not exist!")
        if not isinstance(cable_data, VnaCableData):
            raise TypeError(f"{filename.name}: vna_cable_data has unexpected type")
        return cable_data

    def print(self, out: io.TextIOWrapper | None = None) -> None:
        stream = out if out is not None else io.StringIO()
        for cable in self.cables:
            print(
                f"{cable.name}: length={cable.length_m} m, unit={cable.unit}",
                file=stream,
            )
            if cable.delay_ns_m is not None:
                print(f"  delay={cable.delay_ns_m} ns/m", file=stream)
        print(f"connectors_count={self.connectors_count}", file=stream)
        print(f"connector_loss_db={self.connector_loss_db}", file=stream)
        if out is None:
            print(stream.getvalue(), end="")
