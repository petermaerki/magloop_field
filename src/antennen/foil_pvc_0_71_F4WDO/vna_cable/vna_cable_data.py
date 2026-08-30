import pathlib

from antennenvergleich.h_field_analysis import FeedlineSegment
from antennenvergleich.vna_cable import VnaCableData

from ..antennendaten import ANTENNENDATEN

vna_cable_data = VnaCableData(
    antennendaten=ANTENNENDATEN,
    this_antenna_dir=pathlib.Path(__file__).resolve().parent.parent,
    cables=[
        FeedlineSegment(
            name="LLF240",
            length_m=20.0,
            points=((10e6, 2.9), (30e6, 4.1)),
            unit="db_per_100m",
            delay_ns_m=4.0,
        ),
    ],
    connectors_count=4,  # grob geschaetzt
    connector_loss_db=0.05,  # grob geschaetzt
)

if __name__ == "__main__":
    vna_cable_data.print()
