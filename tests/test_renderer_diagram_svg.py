import math
import xml.etree.ElementTree as ET
from types import SimpleNamespace

import pytest

from antennenvergleich import renderer_diagram_svg
from antennenvergleich.constants import C_LIGHT_MS
from antennenvergleich.datatypes import Antenna, BandData, FloatText, IntText


@pytest.fixture
def antenna():
    def value(number):
        return FloatText(number, "")

    return Antenna(
        D_m=value(1),
        d_m=value(0.01),
        n=IntText(1, ""),
        p_m=value(0),
        info_str="",
        info_environment_str="",
        info_conductor_str="",
        info_capacitor_str="",
        powerPfwd_W=value(100),
        color="#123456",
        bands=[
            BandData(value(frequency), value(1000), value(1))
            for frequency in (10e6, 20e6, 30e6, 40e6)
        ],
    )


@pytest.mark.parametrize(
    "diagram",
    [
        renderer_diagram_svg.Diagramm_eta_f_svg(),
        renderer_diagram_svg.Diagramm_eta_f_svg(show_legend=False),
        renderer_diagram_svg.Diagramm_eta_C_lambda_svg(),
    ],
)
def test_accuracy_markers_and_highlight(diagram, monkeypatch, antenna):
    ratios = {10e6: 0.1, 20e6: 0.1999, 30e6: 0.2, 40e6: 0.3}
    monkeypatch.setattr(
        renderer_diagram_svg,
        "_make_calc",
        lambda antenna, band: SimpleNamespace(eta=0.1, C_lambda=ratios[band.f_Hz.value]),
    )

    svg = ET.fromstring(diagram.render([antenna]))
    ns = {"svg": "http://www.w3.org/2000/svg"}
    for group in (
        svg.find(".//svg:g[@class='svg_series_0']", ns),
        svg.find(".//svg:g[@class='hl_0']", ns),
    ):
        assert group is not None
        circles = group.findall("svg:circle", ns)
        assert [(circle.get("fill"), circle.get("stroke")) for circle in circles] == [
            ("#123456", "white"),
            ("#123456", "white"),
            ("white", "#123456"),
            ("white", "#123456"),
        ]


@pytest.mark.parametrize(
    ("diagram", "ratio", "expected"),
    [
        (renderer_diagram_svg.Diagramm_eta_f_svg(), 0.1999, False),
        (renderer_diagram_svg.Diagramm_eta_f_svg(), 0.2, True),
        (renderer_diagram_svg.Diagramm_eta_f_svg(), 0.3, True),
        (renderer_diagram_svg.Diagramm_eta_f_svg(show_legend=False), 0.3, True),
        (renderer_diagram_svg.Diagramm_eta_f_svg(show_legend=False), 0.1, False),
        (renderer_diagram_svg.Diagramm_eta_C_lambda_svg(), 0.2, True),
        (renderer_diagram_svg.Diagramm_eta_C_lambda_svg(), 0.1999, False),
    ],
)
def test_accuracy_legend_only_when_needed(diagram, ratio, expected, monkeypatch, antenna):
    monkeypatch.setattr(
        renderer_diagram_svg,
        "_make_calc",
        lambda antenna, band: SimpleNamespace(eta=0.1, C_lambda=ratio),
    )
    svg = ET.fromstring(diagram.render([antenna]))
    ns = {"svg": "http://www.w3.org/2000/svg"}
    legend = svg.find(".//svg:g[@class='accuracy_legend']", ns)
    assert (legend is not None) == expected
    if legend is not None:
        assert legend.find("svg:line", ns) is None
        circles = legend.findall("svg:circle", ns)
        assert [(circle.get("fill"), circle.get("stroke")) for circle in circles] == [
            ("#333", "white"),
            ("white", "#333"),
        ]
        texts = legend.findall("svg:text", ns)
        assert [text.text for text in texts] == [
            "C/λ < 0.2: small magnetic loop",
            "C/λ ≥ 0.2: values less accurate",
        ]
        plot = svg.find(".//svg:clipPath[@id='plotarea']/svg:rect", ns)
        assert plot is not None
        right = float(plot.get("x")) + float(plot.get("width"))
        bottom = float(plot.get("y")) + float(plot.get("height"))
        assert all(text.get("text-anchor") == "end" for text in texts)
        assert all(float(text.get("x")) == right - 8 for text in texts)
        assert all(
            float(circle.get("cx")) + float(circle.get("r"))
            < float(text.get("x")) - float(text.get("textLength"))
            for circle, text in zip(circles, texts, strict=True)
        )
        assert all(
            float(plot.get("x")) < float(circle.get("cx")) < right
            and float(plot.get("y")) < float(circle.get("cy")) < bottom
            for circle in circles
        )
        assert float(texts[-1].get("y")) < bottom
        assert float(svg.get("height")) == renderer_diagram_svg.SVG_HEIGHT


def test_legend_uses_same_threshold_as_markers(monkeypatch, antenna):
    monkeypatch.setattr(renderer_diagram_svg, "C_LAMBDA_LIMIT_0p2", 0.25)
    monkeypatch.setattr(
        renderer_diagram_svg,
        "_make_calc",
        lambda antenna, band: SimpleNamespace(
            eta=0.1, C_lambda=0.2 if band.f_Hz.value < 30e6 else 0.3
        ),
    )
    svg = ET.fromstring(renderer_diagram_svg.Diagramm_eta_f_svg().render([antenna]))
    ns = {"svg": "http://www.w3.org/2000/svg"}
    circles = svg.findall(".//svg:g[@class='svg_series_0']/svg:circle", ns)
    assert [circle.get("fill") for circle in circles] == [
        "#123456", "#123456", "white", "white"
    ]
    texts = svg.findall(".//svg:g[@class='accuracy_legend']/svg:text", ns)
    assert [text.text for text in texts] == [
        "C/λ < 0.25: small magnetic loop",
        "C/λ ≥ 0.25: values less accurate",
    ]
    assert "C/λ ≥ 0.25" in svg.findtext("svg:desc", default="", namespaces=ns)


def test_c_lambda_axis_uses_circumference_over_wavelength(antenna):
    diagram = renderer_diagram_svg.Diagramm_eta_C_lambda_svg()
    points = diagram._points_for_antenna(antenna)
    expected = [
        math.pi * antenna.D_m.value * band.f_Hz.value / C_LIGHT_MS
        for band in antenna.bands
    ]
    assert [point.x for point in points] == pytest.approx(expected)
    assert [point.reduced_accuracy for point in points] == [False, True, True, True]

    svg = ET.fromstring(diagram.render([antenna]))
    ns = {"svg": "http://www.w3.org/2000/svg"}
    assert any(text.text == "C / λ" for text in svg.findall("svg:text", ns))
    circles = svg.findall(".//svg:g[@class='svg_series_0']/svg:circle", ns)
    assert [float(circle.get("cx")) for circle in circles] == pytest.approx(
        [diagram._px(value) for value in expected], abs=0.0051
    )
    ticks = diagram._x_ticks()
    assert ticks == [
        (0.0, "0"), (0.1, "0.1"), (0.2, "0.2"),
        (0.3, "0.3"), (0.4, "0.4"), (0.5, "0.5"),
    ]
    assert ticks[-1][0] > max(expected)


@pytest.mark.parametrize(
    ("values", "last_tick"),
    [([0.01], 0.1), ([0.3], 0.4), ([0.41], 0.5), ([0.6], 0.7), ([0.0], 0.1)],
)
def test_c_lambda_axis_extends_to_next_tick(values, last_tick):
    diagram = renderer_diagram_svg.Diagramm_eta_C_lambda_svg()
    diagram._autoscale_x(values)
    ticks = diagram._x_ticks()
    assert ticks[0] == (0.0, "0")
    assert ticks[-1][0] == pytest.approx(last_tick)
    assert [value for value, _ in ticks] == pytest.approx(
        [i / 10 for i in range(len(ticks))]
    )
    assert ticks[-1][0] > max(values)
