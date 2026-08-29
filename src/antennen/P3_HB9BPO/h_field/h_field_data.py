import pathlib

from antennenvergleich.h_field_analysis import FeedlineSegment
from antennenvergleich.h_field_dump import HFieldData, HFieldMesspunkt

from ..antennendaten import ANTENNENDATEN

_f_14M_Hz = 14072e3
_f_18M_Hz = 18116e3
_f_21M_Hz = 21253e3
_f_25M_Hz = 24947e3
_f_28M_Hz = 28604e3

_power_W = 10.0

h_field_data = HFieldData(
    antennendaten=ANTENNENDATEN,
    this_antenna_dir=pathlib.Path(__file__).resolve().parent.parent,
    cables=[
        FeedlineSegment(
            name="LMR195_10m",
            length_m=10.0,
            points=(
                (30e6, 7.7),
                (50e6, 9.9),
            ),
            unit="db_per_100m",
        ),
        FeedlineSegment(
            name="RG400_0p8m",
            length_m=0.8,
            points=(
                (200e6, 19.3),
                (400e6, 28.3),
            ),
            unit="db_per_100m",
        ),
    ],
    connectors_count=4,
    connector_loss_db=0.05,  # grob geschaetzt
    messpunkte=(
        HFieldMesspunkt(
            punkt_str="A",
            f_Hz=_f_14M_Hz,
            # Anzeige von Icom IC7300 MK2, Modulation FM
            tx_power_w=_power_W,
            # Messposition
            X_m=0.0,
            Y_m=2.0,
            Z_m=0.0,
            # Abgelesen vom h-field Meter
            P_dbm=-29.6,
        ),
        HFieldMesspunkt(
            punkt_str="B",
            f_Hz=_f_14M_Hz,
            # Anzeige von Icom IC7300 MK2, Modulation FM
            tx_power_w=_power_W,
            # Messposition
            X_m=0.0,
            Y_m=7.0,
            Z_m=0.0,
            # Abgelesen vom h-field Meter
            P_dbm=-38.7,
        ),
        HFieldMesspunkt(
            punkt_str="C",
            f_Hz=_f_14M_Hz,
            # Anzeige von Icom IC7300 MK2, Modulation FM
            tx_power_w=_power_W,
            # Messposition
            X_m=-2.0,
            Y_m=0.0,
            Z_m=0.0,
            # Abgelesen vom h-field Meter
            P_dbm=-20.8,
        ),
        # --------------------------------------------------18M
        HFieldMesspunkt(
            punkt_str="A",
            f_Hz=_f_18M_Hz,
            # Anzeige von Icom IC7300 MK2, Modulation FM
            tx_power_w=_power_W,
            # Messposition
            X_m=0.0,
            Y_m=2.0,
            Z_m=0.0,
            # Abgelesen vom h-field Meter
            P_dbm=-25.5,
        ),
        HFieldMesspunkt(
            punkt_str="B",
            f_Hz=_f_18M_Hz,
            # Anzeige von Icom IC7300 MK2, Modulation FM
            tx_power_w=_power_W,
            # Messposition
            X_m=0.0,
            Y_m=7.0,
            Z_m=0.0,
            # Abgelesen vom h-field Meter
            P_dbm=-36.8,
        ),
        HFieldMesspunkt(
            punkt_str="C",
            f_Hz=_f_18M_Hz,
            # Anzeige von Icom IC7300 MK2, Modulation FM
            tx_power_w=_power_W,
            # Messposition
            X_m=-2.0,
            Y_m=0.0,
            Z_m=0.0,
            # Abgelesen vom h-field Meter
            P_dbm=-22.1,
        ),
        # --------------------------------------------------21M
        HFieldMesspunkt(
            punkt_str="A",
            f_Hz=_f_21M_Hz,
            # Anzeige von Icom IC7300 MK2, Modulation FM
            tx_power_w=_power_W,
            # Messposition
            X_m=0.0,
            Y_m=2.0,
            Z_m=0.0,
            # Abgelesen vom h-field Meter
            P_dbm=-21.2,
        ),
        HFieldMesspunkt(
            punkt_str="B",
            f_Hz=_f_21M_Hz,
            # Anzeige von Icom IC7300 MK2, Modulation FM
            tx_power_w=_power_W,
            # Messposition
            X_m=0.0,
            Y_m=7.0,
            Z_m=0.0,
            # Abgelesen vom h-field Meter
            P_dbm=-36.3,
        ),
        HFieldMesspunkt(
            punkt_str="C",
            f_Hz=_f_21M_Hz,
            # Anzeige von Icom IC7300 MK2, Modulation FM
            tx_power_w=_power_W,
            # Messposition
            X_m=-2.0,
            Y_m=0.0,
            Z_m=0.0,
            # Abgelesen vom h-field Meter
            P_dbm=-21.4,
        ),
        # --------------------------------------------------25M
        HFieldMesspunkt(
            punkt_str="A",
            f_Hz=_f_25M_Hz,
            # Anzeige von Icom IC7300 MK2, Modulation FM
            tx_power_w=_power_W,
            # Messposition
            X_m=0.0,
            Y_m=2.0,
            Z_m=0.0,
            # Abgelesen vom h-field Meter
            P_dbm=-20.3,
        ),
        HFieldMesspunkt(
            punkt_str="B",
            f_Hz=_f_25M_Hz,
            # Anzeige von Icom IC7300 MK2, Modulation FM
            tx_power_w=_power_W,
            # Messposition
            X_m=0.0,
            Y_m=7.0,
            Z_m=0.0,
            # Abgelesen vom h-field Meter
            P_dbm=-33.6,
        ),
        HFieldMesspunkt(
            punkt_str="C",
            f_Hz=_f_25M_Hz,
            # Anzeige von Icom IC7300 MK2, Modulation FM
            tx_power_w=_power_W,
            # Messposition
            X_m=-2.0,
            Y_m=0.0,
            Z_m=0.0,
            # Abgelesen vom h-field Meter
            P_dbm=-21.6,
        ),
        # --------------------------------------------------28M
        HFieldMesspunkt(
            punkt_str="A",
            f_Hz=_f_28M_Hz,
            # Anzeige von Icom IC7300 MK2, Modulation FM
            tx_power_w=_power_W,
            # Messposition
            X_m=0.0,
            Y_m=2.0,
            Z_m=0.0,
            # Abgelesen vom h-field Meter
            P_dbm=-22.4,
        ),
        HFieldMesspunkt(
            punkt_str="B",
            f_Hz=_f_28M_Hz,
            # Anzeige von Icom IC7300 MK2, Modulation FM
            tx_power_w=_power_W,
            # Messposition
            X_m=0.0,
            Y_m=7.0,
            Z_m=0.0,
            # Abgelesen vom h-field Meter
            P_dbm=-29.6,
        ),
        HFieldMesspunkt(
            punkt_str="C",
            f_Hz=_f_28M_Hz,
            # Anzeige von Icom IC7300 MK2, Modulation FM
            tx_power_w=_power_W,
            # Messposition
            X_m=-2.0,
            Y_m=0.0,
            Z_m=0.0,
            # Abgelesen vom h-field Meter
            P_dbm=-18.6,
        ),
    ),
)

if __name__ == "__main__":
    h_field_data.print()
