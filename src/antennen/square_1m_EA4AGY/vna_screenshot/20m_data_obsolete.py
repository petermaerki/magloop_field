import os

from antennen.square_1m_EA4AGY.vna_screenshot.bandwith_from_swr import (
    SWRInfos,
    plot_swr_overlay,
)

THIS_DIR = os.path.dirname(os.path.abspath(__file__))

infos_20m = SWRInfos(
    image_path=os.path.join(THIS_DIR, "EA4AGY_20m_crop.jpg"),
    left_0_1=75 / 1553,
    right_0_1=1545 / 1553,
    top_0_1=5 / 1041,
    bottom_0_1=990 / 1041,
    freq_min_hz=14_000_000,
    freq_max_hz=14_400_000,
    swr_min_axis=1.0,
    swr_max_axis=3.0,
    point_min_hz=14_179_300,
    point_min_swr=1.28,
    point_arb_hz=14_099_900,
    point_arb_swr=2.08,
)

if __name__ == "__main__":
    plot_swr_overlay(infos_20m)
