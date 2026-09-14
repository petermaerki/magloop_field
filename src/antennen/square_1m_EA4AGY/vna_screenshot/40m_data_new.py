import os

from antennen.square_1m_EA4AGY.vna_screenshot.bandwith_from_swr import (
    SWRInfos,
    plot_swr_overlay,
)

THIS_DIR = os.path.dirname(os.path.abspath(__file__))

infos_20m = SWRInfos(
    image_path=os.path.join(THIS_DIR, "40m_swr.png"),
    left_0_1=60 / 1553,
    right_0_1=1535 / 1553,
    top_0_1=5 / 1041,
    bottom_0_1=0.95,
    freq_min_hz=7_100_000,
    freq_max_hz=7_200_000,
    swr_min_axis=1.0,
    swr_max_axis=3.0,
    point_min_hz=7149600,
    point_min_swr=1.25,
    point_arb_hz=7114500,
    point_arb_swr=2.95,
)

if __name__ == "__main__":
    plot_swr_overlay(infos_20m)
