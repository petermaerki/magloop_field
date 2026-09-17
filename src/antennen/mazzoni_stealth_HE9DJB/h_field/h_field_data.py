import pathlib

from antennenvergleich.h_field_analysis import FeedlineSegment
from antennenvergleich.h_field_dump import HFieldData, HFieldMesspunkt

from ..antennendaten import ANTENNENDATEN

h_field_data = HFieldData(
    antennendaten=ANTENNENDATEN,
    this_antenna_dir=pathlib.Path(__file__).resolve().parent.parent,
    cables=[
        FeedlineSegment(
            name="LMR195_10m",
            length_m=5.0,
            points=(
                (30e6, 7.7),
                (50e6, 9.9),
            ),
            unit="db_per_100m",
        ),
        FeedlineSegment(
            name="10mm_cable_aircom_premium",
            length_m=40,
            points=((10e6, 1.1), (100e6, 3.6)),
            unit="db_per_100m",
        ),
    ],
    connectors_count=6,  # grob geschaetzt
    connector_loss_db=0.05,  # grob geschaetzt
    messpunkte=(
        HFieldMesspunkt(
            punkt_str="A",
            f_Hz=7023000,
            # Peters FT911A
            tx_power_w=100,
            # Messposition
            X_m=10,
            Y_m=0,
            Z_m=1.7,
            # Abgelesen vom h-field Meter
            P_dbm=-40.4,
        ),
        HFieldMesspunkt(
            punkt_str="B",
            f_Hz=7023000,
            # Peters FT911A
            tx_power_w=100,
            # Messposition
            X_m=0,
            Y_m=10,
            Z_m=2.1,
            # Abgelesen vom h-field Meter
            P_dbm=-34.3,
        ),
        HFieldMesspunkt(
            punkt_str="A",
            f_Hz=14055000,
            # Peters FT911A
            tx_power_w=10,
            # Messposition
            X_m=10,
            Y_m=0,
            Z_m=1.7,
            # Abgelesen vom h-field Meter
            P_dbm=-40.3,
        ),
        HFieldMesspunkt(
            punkt_str="B",
            f_Hz=14055000,
            # Peters FT911A
            tx_power_w=10,
            # Messposition
            X_m=0,
            Y_m=10,
            Z_m=2.1,
            # Abgelesen vom h-field Meter
            P_dbm=-37.5,
        ),
        HFieldMesspunkt(
            punkt_str="A",
            f_Hz=28050000,
            # Peters FT911A
            tx_power_w=10,
            # Messposition
            X_m=10,
            Y_m=0,
            Z_m=1.7,
            # Abgelesen vom h-field Meter
            P_dbm=-37.6,
        ),
        HFieldMesspunkt(
            punkt_str="B",
            f_Hz=28050000,
            # Peters FT911A
            tx_power_w=10,
            # Messposition
            X_m=0,
            Y_m=10,
            Z_m=2.1,
            # Abgelesen vom h-field Meter
            P_dbm=-34.5,
        ),
    ),
)

if __name__ == "__main__":
    h_field_data.print()
