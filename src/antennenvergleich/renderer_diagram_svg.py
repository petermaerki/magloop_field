"""Generates compare.html — comparison table for magnetic loop antennas."""

import html
import math

from .antenna_calculations import (
    _make_calc,
)
from .constants import BANDS, C_LIGHT_MS
from .datatypes import Antenna

FILENAME_SVG_ETA_F = "generated_magnetic_loops_compare_eta_f.svg"
FILENAME_SVG_ETA_F_PER_ANTENNA = "eta_f_generated.svg"
ID_SVG_ETA_F = "id_svg_eta_f"
CLASS_SVG_LEGEND_ENTRY = "svg_legend_entry"
CLASS_SVG_SERIES = "svg_series"
FILENAME_SVG_ETA_DL = "generated_magnetic_loops_compare_eta_DL.svg"

SVG_WIDTH = 750
SVG_HEIGHT = 300
SVG_MARGIN_LEFT = 85  # 85
SVG_MARGIN_RIGHT_LEGEND = 230
SVG_MARGIN_RIGHT_NO_LEGEND = 5
SVG_MARGIN_TOP = 10
SVG_MARGIN_BOTTOM = 40

FONT_SIZE_NUMBERS = 15
FONT_SIZE_LABELS = 15
FONT_SIZE_LEGEND = 11

LABEL_OFFSET_X = 8
LABEL_OFFSET_Y = 4

LINE_WIDTH_GRID = 1
LINE_WIDTH_FRAME = 1.5
LINE_WIDTH_TICK = 1.5
LINE_WIDTH_TICK_100 = 4
LINE_WIDTH_SERIES = 1.8
LINE_WIDTH_SERIES_HIT = 12
LINE_WIDTH_HIGHLIGHT = 4
DOT_RADIUS = 4
DOT_RADIUS_HIGHLIGHT = 6
LINE_WIDTH_LEGEND = 2
LINE_WIDTH_LEGEND_DOT = 1

ORDINATE_TICK_VALUES = (
    1.0e-6,
    1.0e-5,
    1.0e-4,
    1.0e-3,
    1.0e-2,
    1.0e-1,
    1.0,
    10.0,
)


def _hover_style(series_count: int) -> str:
    """
    CSS embedded in the SVG: hovering legend entry i OR series i highlights
    both — the legend sample (line + dot + text) and the series
    (requires inline/standalone SVG, not <img>).
    """
    rules = []
    for i in range(series_count):
        hover = f"svg:has(.{CLASS_SVG_LEGEND_ENTRY}_{i}:hover, .{CLASS_SVG_SERIES}_{i}:hover)"
        series = f"{hover} .{CLASS_SVG_SERIES}_{i}"
        legend = f"{hover} .{CLASS_SVG_LEGEND_ENTRY}_{i}"
        rules.append(
            f"{series} polyline, {legend} line {{ stroke-width: {LINE_WIDTH_HIGHLIGHT}; }}"
        )
        rules.append(
            f"{series} circle, {legend} circle {{ r: {DOT_RADIUS_HIGHLIGHT}; }}"
        )
        rules.append(f"{legend} text {{ fill: #000; font-weight: bold; }}")
    joined = "\n    ".join(rules)
    return f"  <style>\n    {joined}\n  </style>"


class _DiagramSvgBase:
    """
    Renders a diagram: log-eta ordinate, series with hover highlighting, legend.

    Subclasses only define the abscissa: scale (_px), ticks (_x_ticks),
    data points (_points_for_antenna), axis label and optional autoscaling.
    """

    _X_AXIS_LABEL: str

    def __init__(self, *, show_legend: bool = True) -> None:
        self._show_legend = show_legend
        self._MR = (
            SVG_MARGIN_RIGHT_LEGEND if show_legend else SVG_MARGIN_RIGHT_NO_LEGEND
        )
        self._pw = SVG_WIDTH - SVG_MARGIN_LEFT - self._MR
        self._ph = SVG_HEIGHT - SVG_MARGIN_TOP - SVG_MARGIN_BOTTOM
        self._ETA_MIN = 1.0e-5
        self._ETA_MAX = 1.0  # overwritten in render() from data

    # ── abscissa, subclass-specific ────────────────────────────────────────────

    def _px(self, value: float, /) -> float:
        raise NotImplementedError

    def _x_ticks(self) -> list[tuple[float, str]]:
        """Tick positions (abscissa value) and their labels."""
        raise NotImplementedError

    def _points_for_antenna(self, antenna: Antenna) -> list[tuple[float, float]]:
        """Sorted (abscissa value, eta) points of one antenna."""
        raise NotImplementedError

    def _autoscale_x(self, xs: list[float]) -> None:
        """Adjust the abscissa range to the data. Default: fixed range."""

    # ── shared rendering ───────────────────────────────────────────────────────

    def _py(self, eta: float) -> float:
        if eta <= 0:
            return SVG_MARGIN_TOP + self._ph
        le = math.log10(eta)
        lmin = math.log10(self._ETA_MIN)
        lmax = math.log10(self._ETA_MAX)
        return SVG_MARGIN_TOP + (1.0 - (le - lmin) / (lmax - lmin)) * self._ph

    @staticmethod
    def _eta_label(eta: float) -> str:
        eta_percent = eta * 100.0
        return f"{eta_percent:g} %"

    def _collect_data(
        self, antennas: list[Antenna]
    ) -> list[tuple[Antenna, list[tuple[float, float]]]]:
        result = []
        for antenna in antennas:
            pts = self._points_for_antenna(antenna)
            if pts:
                result.append((antenna, pts))
        result.sort(key=lambda item: item[0].antenna_label.casefold())
        return result

    def render(
        self,
        antennas: list[Antenna],
    ) -> str:
        data = self._collect_data(antennas)
        all_etas = [e for _, pts in data for _, e in pts]
        if all_etas:
            min_eta = min(all_etas)
            max_eta = max(all_etas)
            self._ETA_MIN = self._previous_ordinate_tick(min_eta)
            self._ETA_MAX = max(self._next_ordinate_tick(max_eta), 1.0)
            if self._ETA_MIN == self._ETA_MAX:
                self._ETA_MIN /= 10.0
                self._ETA_MAX *= 10.0
        self._autoscale_x([x for _, pts in data for x, _ in pts])
        buf: list[str] = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{SVG_WIDTH}" height="{SVG_HEIGHT}" viewBox="0 0 {SVG_WIDTH} {SVG_HEIGHT}">',
            f'  <rect width="{SVG_WIDTH}" height="{SVG_HEIGHT}" fill="white"/>',
            f'  <clipPath id="plotarea"><rect x="{SVG_MARGIN_LEFT}" y="{SVG_MARGIN_TOP}" width="{self._pw}" height="{self._ph}"/></clipPath>',
            _hover_style(series_count=len(data)),
        ]
        buf += self._draw_grid()
        buf += self._draw_frame()
        buf += self._draw_x_ticks()
        buf += self._draw_y_ticks()
        buf += self._draw_axis_labels()
        for index, (antenna, pts) in enumerate(data):
            buf += self._draw_series(index, pts, antenna.color, antenna.dashed)  # type: ignore[arg-type]
        if self._show_legend:
            buf += self._draw_legend(
                [
                    (antenna.antenna_label, antenna.color, antenna.dashed)  # type: ignore[misc]
                    for antenna, _ in data
                ]
            )
        buf.append("</svg>")
        return "\n".join(buf)

    def _draw_grid(self) -> list[str]:
        lines = []
        x0, x1 = SVG_MARGIN_LEFT, SVG_MARGIN_LEFT + self._pw
        y0, y1 = SVG_MARGIN_TOP, SVG_MARGIN_TOP + self._ph
        for x_value, _ in self._x_ticks():
            x = self._px(x_value)
            lines.append(
                f'  <line x1="{x:.1f}" y1="{y0}" x2="{x:.1f}" y2="{y1}" stroke="#e0e0e0" stroke-width="{LINE_WIDTH_GRID}"/>'
            )
        for eta in self._ordinate_tick_values():
            y = self._py(eta)
            lines.append(
                f'  <line x1="{x0}" y1="{y:.1f}" x2="{x1}" y2="{y:.1f}" {self._ordinate_line_style(eta)}/>'
            )
        return lines

    def _draw_frame(self) -> list[str]:
        return [
            f'  <rect x="{SVG_MARGIN_LEFT}" y="{SVG_MARGIN_TOP}" width="{self._pw}" height="{self._ph}" fill="none" stroke="#888" stroke-width="{LINE_WIDTH_FRAME}"/>',
        ]

    def _draw_x_ticks(self) -> list[str]:
        lines = []
        y_base = SVG_MARGIN_TOP + self._ph
        for x_value, label in self._x_ticks():
            x = self._px(x_value)
            lines.append(
                f'  <line x1="{x:.1f}" y1="{y_base}" x2="{x:.1f}" y2="{y_base + 5}" stroke="#888" stroke-width="{LINE_WIDTH_TICK}"/>'
            )
            label_y = y_base + 22
            lines.append(
                f'  <text x="{x:.1f}" y="{label_y}" text-anchor="middle" font-size="{FONT_SIZE_NUMBERS}" font-family="Arial,sans-serif" fill="#333" transform="rotate(-90 {x:.1f} {label_y})">{label}</text>'
            )
        return lines

    def _draw_y_ticks(self) -> list[str]:
        lines = []
        for eta in self._ordinate_tick_values():
            y = self._py(eta)
            lines.append(
                f'  <line x1="{SVG_MARGIN_LEFT - 5}" y1="{y:.1f}" x2="{SVG_MARGIN_LEFT}" y2="{y:.1f}" {self._ordinate_line_style(eta)}/>'
            )
            lines.append(
                f'  <text x="{SVG_MARGIN_LEFT - LABEL_OFFSET_X}" y="{y + LABEL_OFFSET_Y:.1f}" text-anchor="end" font-size="{FONT_SIZE_NUMBERS}" font-family="Arial,sans-serif" fill="#333">{self._eta_label(eta)}</text>'
            )
        return lines

    def _ordinate_tick_values(self) -> list[float]:
        lower = self._ETA_MIN
        upper = self._ETA_MAX
        values = [eta for eta in ORDINATE_TICK_VALUES if lower <= eta <= upper]
        if values:
            return values
        return [self._ETA_MIN, self._ETA_MAX]

    @staticmethod
    def _previous_ordinate_tick(value: float) -> float:
        for tick in reversed(ORDINATE_TICK_VALUES):
            if tick <= value:
                return tick
        return ORDINATE_TICK_VALUES[0]

    @staticmethod
    def _next_ordinate_tick(value: float) -> float:
        for tick in ORDINATE_TICK_VALUES:
            if tick >= value:
                return tick
        return ORDINATE_TICK_VALUES[-1]

    @staticmethod
    def _ordinate_line_style(eta: float) -> str:
        if eta == 1.0:
            return f'stroke="#000" stroke-width="{LINE_WIDTH_TICK_100}"'
        return f'stroke="#888" stroke-width="{LINE_WIDTH_TICK}"'

    def _draw_axis_labels(self) -> list[str]:
        cy = SVG_MARGIN_TOP + self._ph / 2
        axis_end_x = SVG_MARGIN_LEFT + self._pw
        axis_end_y = SVG_MARGIN_TOP + self._ph + 22
        y_label_x = 25
        y_label_y = cy
        return [
            f'  <text x="{axis_end_x:.1f}" y="{axis_end_y}" text-anchor="middle" font-size="{FONT_SIZE_LABELS}" font-family="Arial,sans-serif" fill="#222" transform="rotate(-90 {axis_end_x:.1f} {axis_end_y})">{self._X_AXIS_LABEL}</text>',
            f'  <text transform="rotate(-90 {y_label_x} {y_label_y:.1f})" x="{y_label_x}" y="{y_label_y:.1f}" text-anchor="middle" font-size="{FONT_SIZE_LABELS}" font-family="Arial,sans-serif" fill="#222">η (Efficiency)</text>',
        ]

    def _draw_series(
        self,
        index: int,
        pts: list[tuple[float, float]],
        color: str,
        dashed: bool = False,
    ) -> list[str]:
        lines = [f'  <g class="{CLASS_SVG_SERIES}_{index}">']
        coords = " ".join(f"{self._px(x):.2f},{self._py(eta):.2f}" for x, eta in pts)
        dash_attr = ' stroke-dasharray="8,4"' if dashed else ""
        # Invisible wide polyline: easier hover target than the thin visible line.
        # Inline style outranks the hover rule, so its width never changes.
        lines.append(
            f'  <polyline points="{coords}" fill="none" stroke="transparent" style="stroke-width: {LINE_WIDTH_SERIES_HIT};" clip-path="url(#plotarea)"/>'
        )
        lines.append(
            f'  <polyline points="{coords}" fill="none" stroke="{color}" stroke-width="{LINE_WIDTH_SERIES}"{dash_attr} clip-path="url(#plotarea)"/>'
        )
        for x, eta in pts:
            lines.append(
                f'  <circle cx="{self._px(x):.2f}" cy="{self._py(eta):.2f}" r="{DOT_RADIUS}" fill="{color}" stroke="white" stroke-width="{LINE_WIDTH_LEGEND_DOT}" clip-path="url(#plotarea)"/>'
            )
        lines.append("  </g>")
        return lines

    def _draw_legend(self, entries: list[tuple[str, str, bool]]) -> list[str]:
        lines = []
        lx = SVG_MARGIN_LEFT + self._pw + 5
        ly = SVG_MARGIN_TOP + 0
        row_height = 14
        for i, (name, color, dashed) in enumerate(entries):
            y = ly + i * row_height
            dash_attr = ' stroke-dasharray="8,4"' if dashed else ""
            lines.append(f'  <g class="{CLASS_SVG_LEGEND_ENTRY}_{i}">')
            # Transparent rect: makes the whole row (including gaps) detect hover.
            lines.append(
                f'  <rect x="{lx}" y="{y}" width="{SVG_WIDTH - lx}" height="{row_height}" fill="transparent"/>'
            )
            lines.append(
                f'  <line x1="{lx}" y1="{y + 7}" x2="{lx + 25}" y2="{y + 7}" stroke="{color}" stroke-width="{LINE_WIDTH_LEGEND}"{dash_attr}/>'
            )
            lines.append(
                f'  <circle cx="{lx + 12}" cy="{y + 7}" r="{DOT_RADIUS}" fill="{color}" stroke="white" stroke-width="{LINE_WIDTH_LEGEND_DOT}"/>'
            )
            lines.append(
                f'  <text x="{lx + 32}" y="{y + 11}" font-size="{FONT_SIZE_LEGEND}" font-family="Arial,sans-serif" fill="#333">{html.escape(name)}</text>'
            )
            lines.append("  </g>")
        return lines


class Diagramm_eta_f_svg(_DiagramSvgBase):
    """Eta over frequency: logarithmic abscissa, ticks at the band centers."""

    _BAND_CENTERS_MHZ = sorted(f_hz / 1e6 for f_hz in BANDS.values())

    _F_MIN_HZ = 1.5e6
    _F_MAX_HZ = 60.0e6  # vorher 35.0e6

    _X_AXIS_LABEL = "MHz"

    def _px(self, f_Hz: float) -> float:
        lf = math.log10(f_Hz)
        lmin = math.log10(self._F_MIN_HZ)
        lmax = math.log10(self._F_MAX_HZ)
        return SVG_MARGIN_LEFT + (lf - lmin) / (lmax - lmin) * self._pw

    def _x_ticks(self) -> list[tuple[float, str]]:
        return [
            (f_mhz * 1e6, f"{f_mhz:.1f}")
            for f_mhz in self._BAND_CENTERS_MHZ
            if self._F_MIN_HZ <= f_mhz * 1e6 <= self._F_MAX_HZ
        ]

    def _points_for_antenna(self, antenna: Antenna) -> list[tuple[float, float]]:
        pts: list[tuple[float, float]] = []
        for bd in antenna.bands:
            calc = _make_calc(antenna, bd)
            if calc.eta > 0:
                pts.append((bd.f_Hz.value, calc.eta))
        pts.sort()
        return pts


class Diagramm_eta_D_lambda_svg(_DiagramSvgBase):
    """Eta over D/lambda: linear abscissa, autoscaled to the data."""

    _X_AXIS_LABEL = "D / λ"

    def __init__(self) -> None:
        super().__init__()
        self._X_MIN = 0.0
        self._X_MAX = 1.0
        self._has_x_values = False

    def _px(self, x_value: float) -> float:
        return (
            SVG_MARGIN_LEFT
            + (x_value - self._X_MIN) / (self._X_MAX - self._X_MIN) * self._pw
        )

    def _autoscale_x(self, xs: list[float]) -> None:
        self._has_x_values = bool(xs)
        if xs:
            self._X_MIN = min(xs) * 0.95 if min(xs) > 0 else 0.0
            self._X_MAX = max(xs) * 1.05 if max(xs) > self._X_MIN else self._X_MIN + 1.0

    def _x_ticks(self) -> list[tuple[float, str]]:
        if not self._has_x_values:
            return []
        ticks = []
        for tick in range(6):
            x_value = self._X_MIN + (self._X_MAX - self._X_MIN) * tick / 5.0
            label = f"{x_value:.2f}".rstrip("0").rstrip(".") if x_value != 0 else "0"
            ticks.append((x_value, label))
        return ticks

    def _points_for_antenna(self, antenna: Antenna) -> list[tuple[float, float]]:
        pts: list[tuple[float, float]] = []
        for bd in antenna.bands:
            calc = _make_calc(antenna, bd)
            if calc.eta > 0:
                wavelength_m = C_LIGHT_MS / bd.f_Hz.value
                pts.append((antenna.D_m.value / wavelength_m, calc.eta))
        pts.sort()
        return pts
