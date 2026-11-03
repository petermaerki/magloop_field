"""Structured data for the Peter Märki Tubby outdoor antenna."""

from antennenvergleich.datatypes import Antenna, BandData, FloatText

ANTENNENDATEN = Antenna(
    # color="#d60000",  # color from compare_colors.py
    dashed=False,
    selection_brand="Selfmade",
    selection_location="HB9ASB",
    selection_name="1_9_heliax",
    D_m=FloatText(1.9, "Source: QRZ Page HB9ASB"),
    d_m=FloatText(0.036, "Source: Heliax 1-1/4: coars extimate"),
    n=FloatText(1, ""),
    p_m=FloatText(0.0, ""),
    powerPfwd_W=FloatText(200.0, "Source: QRZ Page: Most of the Time 50W"),
    info_str="Mag loop made of Heliax 1-1/4 and variable vacuum capacitor.",
    overview_pictures=("images/p1012266_loop_overview.jpg",),
    measurement_html="measurement.html",
    environment_html="environment.html",
    info_environment_str="Indoor, 3rd floor.",
    info_conductor_str="Heliax 1-1/4 corrugated coaxial cable. Approx. 36 mm outer diameter.",
    info_capacitor_str="Variable vacuum capacitor 500 pF (Comet). For the 160 m band, two additional fixed-value vacuum capacitors are switched in.",
    final_remarks_html="final_remarks.html",
    info_thanks_str="Many thanks to Toni for sharing the measurement results and for the lively discussions on efficiency.",
    bands=[
        # 630m Band ausgeblendet weil es ein Langwellenband ist und kein Kurzwellenband
        # BandData(
        #     f_Hz=FloatText(475_000, "0475_kHz.jpg"),
        #     bw262_Hz=FloatText(1_180, "BW @ aboud SWR 2.62"),
        #     swr_min=FloatText(
        #         1.0,
        #         "Quite precice tuned to SWR 1.0 at center frequency. Unklar Skala, es ist unklar ob das der Reflexionskoeffizient oder das SWR dargestellt wird. Die Teilstriche passen nicht zu SWR.",
        #     ),
        # ),
        BandData(
            f_Hz=FloatText(1_900_000, "1900_khz.jpg"),
            bw262_Hz=FloatText(
                1_720, "BW @ SWR 2.62, from NanoVNA marker delta M2-M1 = 1.72 kHz"
            ),
            swr_min=FloatText(
                1.0,
                "Quite precice tuned to SWR 1.0 at center frequency. Unklar Skala, es ist unklar ob das der Reflexionskoeffizient oder das SWR dargestellt wird. Die Teilstriche passen nicht zu SWR.",
            ),
        ),
        BandData(
            f_Hz=FloatText(3_624_000, "3624_kHz.jpg"),
            bw262_Hz=FloatText(
                4_400, "BW @ SWR 2.62, from NanoVNA marker delta M2-M1 = 4.4 kHz"
            ),
            swr_min=FloatText(
                1.0,
                "Quite precice tuned to SWR 1.0 at center frequency. Unklar Skala, es ist unklar ob das der Reflexionskoeffizient oder das SWR dargestellt wird. Die Teilstriche passen nicht zu SWR.",
            ),
        ),
        BandData(
            f_Hz=FloatText(5_362_000, "5362_kHz.jpg"),
            bw262_Hz=FloatText(
                19_000, "BW @ SWR 2.62, from NanoVNA marker delta M2-M1 = 19 kHz"
            ),
            swr_min=FloatText(
                1.0,
                "Quite precice tuned to SWR 1.0 at center frequency. Unklar Skala, es ist unklar ob das der Reflexionskoeffizient oder das SWR dargestellt wird. Die Teilstriche passen nicht zu SWR.",
            ),
        ),
        BandData(
            f_Hz=FloatText(7_100_000, "7100_khz.jpg"),
            bw262_Hz=FloatText(
                33_200, "BW @ SWR 2.62, from NanoVNA marker delta M2-M1 = 33.2 kHz"
            ),
            swr_min=FloatText(
                1.0,
                "Quite precice tuned to SWR 1.0 at center frequency. Unklar Skala, es ist unklar ob das der Reflexionskoeffizient oder das SWR dargestellt wird. Die Teilstriche passen nicht zu SWR.",
            ),
        ),
        BandData(
            f_Hz=FloatText(10_100_000, "10100_kHz.jpg"),
            bw262_Hz=FloatText(
                154_000, "BW @ SWR 2.62, from NanoVNA marker delta M2-M1 = 154 kHz"
            ),
            swr_min=FloatText(
                1.0,
                "Quite precice tuned to SWR 1.0 at center frequency. Unklar Skala, es ist unklar ob das der Reflexionskoeffizient oder das SWR dargestellt wird. Die Teilstriche passen nicht zu SWR.",
            ),
        ),
    ],
    bandwidth_source_str="SWR = 2.62",
)
