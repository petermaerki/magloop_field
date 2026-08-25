import pathlib

from antennenvergleich.h_field_analysis import FeedlineSegment
from antennenvergleich.h_field_dump import HFieldData, HFieldMesspunkt

from ..antennendaten import ANTENNENDATEN

h_field_data = HFieldData(
    antennendaten=ANTENNENDATEN,
    this_antenna_dir=pathlib.Path(__file__).resolve().parent.parent,
    cables=[
        FeedlineSegment(
            name="cable_a",
            length_m=2.5,
            points=((10e6, 1.5), (50e6, 3.7)),
            unit="db_per_100ft",
        ),
        FeedlineSegment(
            name="cable_d",
            length_m=10.0,
            points=(
                (10e6, 1.2),
                (50e6, 2.8),
            ),  # finde kein passendes Datenblatt, aehnliches
            unit="db_per_100m",
        ),
    ],
    connectors_count=6,  # grob geschaetzt
    connector_loss_db=0.05,  # grob geschaetzt
    messpunkte=(
        HFieldMesspunkt(
            punkt_str="A",
            f_Hz=3740e3,
            # Anzeige von YAESU FTX-1 OPTIMA, Modulation FM
            tx_power_w=100,
            # Messposition
            X_m=-6.724,
            Y_m=-6.071,
            Z_m=-0.543,
            # Abgelesen vom h-field Meter
            P_dbm=-22.3,
        ),
    ),
)

if __name__ == "__main__":
    h_field_data.print()
