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


class Diagramm_eta_f_svg:
    _BAND_CENTERS_MHZ = sorted(f_hz / 1e6 for f_hz in BANDS.f_hz_by_band_name.values())

    _F_MIN_HZ = 1.5e6
    _F_MAX_HZ = 35.0e6

    def __init__(self, *, show_legend: bool = True) -> None:
        self._show_legend = show_legend
        self._MR = (
            SVG_MARGIN_RIGHT_LEGEND if show_legend else SVG_MARGIN_RIGHT_NO_LEGEND
        )
        self._pw = SVG_WIDTH - SVG_MARGIN_LEFT - self._MR
        self._ph = SVG_HEIGHT - SVG_MARGIN_TOP - SVG_MARGIN_BOTTOM
        self._ETA_MIN = 1.0e-5
        self._ETA_MAX = 1.0  # overwritten in render() from data

    def _px(self, f_Hz: float) -> float:
        lf = math.log10(f_Hz)
        lmin = math.log10(self._F_MIN_HZ)
        lmax = math.log10(self._F_MAX_HZ)
        return SVG_MARGIN_LEFT + (lf - lmin) / (lmax - lmin) * self._pw

    def _visible_band_centers_mhz(self) -> list[float]:
        return [
            f_mhz
            for f_mhz in self._BAND_CENTERS_MHZ
            if self._F_MIN_HZ <= f_mhz * 1e6 <= self._F_MAX_HZ
        ]

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

    @staticmethod
    def _eta_points_for_antenna(antenna: Antenna) -> list[tuple[float, float]]:
        pts: list[tuple[float, float]] = []
        for bd in antenna.bands:
            if bd.f_Hz.value is None or bd.bw262_Hz.value is None:
                continue
            calc = _make_calc(antenna, bd)
            if calc.eta > 0:
                pts.append((bd.f_Hz.value, calc.eta))
        pts.sort()
        return pts

    def _collect_data(
        self, antennas: list[Antenna]
    ) -> list[tuple[Antenna, list[tuple[float, float]]]]:
        result = []
        for antenna in antennas:
            if antenna.D_m.value is None or antenna.d_m.value is None:
                continue
            pts = self._eta_points_for_antenna(antenna)
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
        buf: list[str] = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{SVG_WIDTH}" height="{SVG_HEIGHT}" viewBox="0 0 {SVG_WIDTH} {SVG_HEIGHT}">',
            f'  <rect width="{SVG_WIDTH}" height="{SVG_HEIGHT}" fill="white"/>',
            f'  <clipPath id="plotarea"><rect x="{SVG_MARGIN_LEFT}" y="{SVG_MARGIN_TOP}" width="{self._pw}" height="{self._ph}"/></clipPath>',
        ]
        buf += self._draw_grid()
        buf += self._draw_frame()
        buf += self._draw_x_ticks()
        buf += self._draw_y_ticks()
        buf += self._draw_axis_labels()
        for antenna, pts in data:
            buf += self._draw_series(pts, antenna.color)
        if self._show_legend:
            buf += self._draw_legend(
                [(antenna.antenna_label, antenna.color) for antenna, _ in data]
            )
        buf.append("</svg>")
        return "\n".join(buf)

    def _draw_grid(self) -> list[str]:
        lines = []
        x0, x1 = SVG_MARGIN_LEFT, SVG_MARGIN_LEFT + self._pw
        y0, y1 = SVG_MARGIN_TOP, SVG_MARGIN_TOP + self._ph
        for f_mhz in self._visible_band_centers_mhz():
            x = self._px(f_mhz * 1e6)
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
        for f_mhz in self._visible_band_centers_mhz():
            x = self._px(f_mhz * 1e6)
            lines.append(
                f'  <line x1="{x:.1f}" y1="{y_base}" x2="{x:.1f}" y2="{y_base + 5}" stroke="#888" stroke-width="{LINE_WIDTH_TICK}"/>'
            )
            label_y = y_base + 22
            lines.append(
                f'  <text x="{x:.1f}" y="{label_y}" text-anchor="middle" font-size="{FONT_SIZE_NUMBERS}" font-family="Arial,sans-serif" fill="#333" transform="rotate(-90 {x:.1f} {label_y})">{f_mhz:.1f}</text>'
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
            f'  <text x="{axis_end_x:.1f}" y="{axis_end_y}" text-anchor="middle" font-size="{FONT_SIZE_LABELS}" font-family="Arial,sans-serif" fill="#222" transform="rotate(-90 {axis_end_x:.1f} {axis_end_y})">MHz</text>',
            f'  <text transform="rotate(-90 {y_label_x} {y_label_y:.1f})" x="{y_label_x}" y="{y_label_y:.1f}" text-anchor="middle" font-size="{FONT_SIZE_LABELS}" font-family="Arial,sans-serif" fill="#222">η (Wirkungsgrad)</text>',
        ]

    def _draw_series(self, pts: list[tuple[float, float]], color: str) -> list[str]:
        lines = []
        coords = " ".join(f"{self._px(f):.2f},{self._py(e):.2f}" for f, e in pts)
        lines.append(
            f'  <polyline points="{coords}" fill="none" stroke="{color}" stroke-width="{LINE_WIDTH_SERIES}" clip-path="url(#plotarea)"/>'
        )
        for f, e in pts:
            x, y = self._px(f), self._py(e)
            lines.append(
                f'  <circle cx="{x:.2f}" cy="{y:.2f}" r="4" fill="{color}" stroke="white" stroke-width="{LINE_WIDTH_LEGEND_DOT}" clip-path="url(#plotarea)"/>'
            )
        return lines

    def _draw_legend(self, entries: list[tuple[str, str]]) -> list[str]:
        lines = []
        lx = SVG_MARGIN_LEFT + self._pw + 5
        ly = SVG_MARGIN_TOP + 0
        for i, (name, color) in enumerate(entries):
            y = ly + i * 14
            lines.append(
                f'  <line x1="{lx}" y1="{y + 7}" x2="{lx + 25}" y2="{y + 7}" stroke="{color}" stroke-width="{LINE_WIDTH_LEGEND}"/>'
            )
            lines.append(
                f'  <circle cx="{lx + 12}" cy="{y + 7}" r="4" fill="{color}" stroke="white" stroke-width="{LINE_WIDTH_LEGEND_DOT}"/>'
            )
            lines.append(
                f'  <text x="{lx + 32}" y="{y + 11}" font-size="{FONT_SIZE_LEGEND}" font-family="Arial,sans-serif" fill="#333">{html.escape(name)}</text>'
            )
        return lines


class Diagramm_eta_D_lambda_svg:
    _W = 860
    _H = 520
    _ML = 85
    _MR = 230
    _MT = 40
    _MB = 65

    _ETA_MIN = 1.0e-5

    def __init__(self) -> None:
        self._pw = self._W - self._ML - self._MR
        self._ph = self._H - self._MT - self._MB
        self._ETA_MAX = 1.0
        self._X_MIN = 0.0
        self._X_MAX = 1.0

    def _px(self, x_value: float) -> float:
        return (
            self._ML + (x_value - self._X_MIN) / (self._X_MAX - self._X_MIN) * self._pw
        )

    def _py(self, eta: float) -> float:
        if eta <= 0:
            return self._MT + self._ph
        le = math.log10(eta)
        lmin = math.log10(self._ETA_MIN)
        lmax = math.log10(self._ETA_MAX)
        return self._MT + (1.0 - (le - lmin) / (lmax - lmin)) * self._ph

    def _collect_data(
        self, antennas: list[Antenna]
    ) -> list[tuple[Antenna, list[tuple[float, float]]]]:
        result = []
        for antenna in antennas:
            if antenna.D_m.value is None:
                continue
            pts: list[tuple[float, float]] = []
            for bd in antenna.bands:
                if bd.f_Hz.value is None or bd.bw262_Hz.value is None:
                    continue
                calc = _make_calc(antenna, bd)
                if calc.eta > 0:
                    wavelength_m = C_LIGHT_MS / bd.f_Hz.value
                    x_value = antenna.D_m.value / wavelength_m
                    pts.append((x_value, calc.eta))
            pts.sort()
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
        xs = [x for _, pts in data for x, _ in pts]
        if all_etas:
            self._ETA_MAX = 10.0 ** math.ceil(math.log10(max(all_etas)))
        if xs:
            self._X_MIN = min(xs) * 0.95 if min(xs) > 0 else 0.0
            self._X_MAX = max(xs) * 1.05 if max(xs) > self._X_MIN else self._X_MIN + 1.0
        buf: list[str] = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self._W}" height="{self._H}" viewBox="0 0 {self._W} {self._H}">',
            f'  <rect width="{self._W}" height="{self._H}" fill="white"/>',
            f'  <clipPath id="plotarea"><rect x="{self._ML}" y="{self._MT}" width="{self._pw}" height="{self._ph}"/></clipPath>',
        ]
        buf += self._draw_grid(xs)
        buf += self._draw_frame()
        buf += self._draw_x_ticks(xs)
        buf += self._draw_y_ticks()
        buf += self._draw_axis_labels()
        for antenna, pts in data:
            buf += self._draw_series(pts, antenna.color)
        buf += self._draw_legend(
            [(antenna.antenna_label, antenna.color) for antenna, _ in data]
        )
        buf.append("</svg>")
        return "\n".join(buf)

    def _draw_grid(self, xs: list[float]) -> list[str]:
        lines = []
        x0, x1 = SVG_MARGIN_LEFT, SVG_MARGIN_LEFT + self._pw
        y0, y1 = SVG_MARGIN_TOP, SVG_MARGIN_TOP + self._ph
        if xs:
            for tick in range(6):
                x_value = self._X_MIN + (self._X_MAX - self._X_MIN) * tick / 5.0
                x = self._px(x_value)
                lines.append(
                    f'  <line x1="{x:.1f}" y1="{y0}" x2="{x:.1f}" y2="{y1}" stroke="#e0e0e0" stroke-width="{LINE_WIDTH_GRID}"/>'
                )
        exp_max = round(math.log10(self._ETA_MAX))
        for exp in range(-5, exp_max + 1):
            y = self._py(10.0**exp)
            lines.append(
                f'  <line x1="{x0}" y1="{y:.1f}" x2="{x1}" y2="{y:.1f}" stroke="#e0e0e0" stroke-width="{LINE_WIDTH_GRID}"/>'
            )
        return lines

    def _draw_frame(self) -> list[str]:
        return [
            f'  <rect x="{self._ML}" y="{self._MT}" width="{self._pw}" height="{self._ph}" fill="none" stroke="#888" stroke-width="{LINE_WIDTH_FRAME}"/>'
        ]

    def _draw_x_ticks(self, xs: list[float]) -> list[str]:
        lines = []
        y_base = self._MT + self._ph
        if xs:
            for tick in range(6):
                x_value = self._X_MIN + (self._X_MAX - self._X_MIN) * tick / 5.0
                x = self._px(x_value)
                lines.append(
                    f'  <line x1="{x:.1f}" y1="{y_base}" x2="{x:.1f}" y2="{y_base + 5}" stroke="#888" stroke-width="{LINE_WIDTH_TICK}"/>'
                )
                label = (
                    f"{x_value:.2f}".rstrip("0").rstrip(".") if x_value != 0 else "0"
                )
                label_y = y_base + 18
                lines.append(
                    f'  <text x="{x:.1f}" y="{label_y}" text-anchor="middle" font-size="{FONT_SIZE_NUMBERS}" font-family="Arial,sans-serif" fill="#333" transform="rotate(-90 {x:.1f} {label_y})">{label}</text>'
                )
        return lines

    def _draw_y_ticks(self) -> list[str]:
        lines = []
        all_tick_labels = {
            -5: "0.001%",
            -4: "0.01%",
            -3: "0.1%",
            -2: "1%",
            -1: "10%",
            0: "100%",
        }
        exp_max = round(math.log10(self._ETA_MAX))
        tick_labels = {k: v for k, v in all_tick_labels.items() if k <= exp_max}
        for exp, label in tick_labels.items():
            y = self._py(10.0**exp)
            lines.append(
                f'  <line x1="{SVG_MARGIN_LEFT - 5}" y1="{y:.1f}" x2="{SVG_MARGIN_LEFT}" y2="{y:.1f}" stroke="#888" stroke-width="{LINE_WIDTH_TICK}"/>'
            )
            lines.append(
                f'  <text x="{SVG_MARGIN_LEFT - 8}" y="{y + 4:.1f}" text-anchor="end" font-size="{FONT_SIZE_NUMBERS}" font-family="Arial,sans-serif" fill="#333">{label}</text>'
            )
        return lines

    def _draw_axis_labels(self) -> list[str]:
        cx = SVG_MARGIN_LEFT + self._pw / 2
        cy = SVG_MARGIN_TOP + self._ph / 2
        return [
            f'  <text x="{cx:.1f}" y="{SVG_MARGIN_TOP + self._ph + 50}" text-anchor="middle" font-size="{FONT_SIZE_LABELS}" font-family="Arial,sans-serif" fill="#222">D / λ</text>',
            f'  <text transform="rotate(-90 25 {cy:.1f})" x="25" y="{cy:.1f}" text-anchor="middle" font-size="{FONT_SIZE_LABELS}" font-family="Arial,sans-serif" fill="#222">η (Wirkungsgrad)</text>',
        ]

    def _draw_series(self, pts: list[tuple[float, float]], color: str) -> list[str]:
        lines = []
        coords = " ".join(f"{self._px(x):.2f},{self._py(e):.2f}" for x, e in pts)
        lines.append(
            f'  <polyline points="{coords}" fill="none" stroke="{color}" stroke-width="{LINE_WIDTH_SERIES}" clip-path="url(#plotarea)"/>'
        )
        for x, e in pts:
            x_pos, y_pos = self._px(x), self._py(e)
            lines.append(
                f'  <circle cx="{x_pos:.2f}" cy="{y_pos:.2f}" r="4" fill="{color}" stroke="white" stroke-width="{LINE_WIDTH_LEGEND_DOT}" clip-path="url(#plotarea)"/>'
            )
        return lines

    def _draw_legend(self, entries: list[tuple[str, str]]) -> list[str]:
        lines = []
        lx = SVG_MARGIN_LEFT + self._pw + 18
        ly = SVG_MARGIN_TOP + 10
        for i, (name, color) in enumerate(entries):
            y = ly + i * 22
            lines.append(
                f'  <line x1="{lx}" y1="{y + 7}" x2="{lx + 25}" y2="{y + 7}" stroke="{color}" stroke-width="{LINE_WIDTH_LEGEND}"/>'
            )
            lines.append(
                f'  <circle cx="{lx + 12}" cy="{y + 7}" r="4" fill="{color}" stroke="white" stroke-width="{LINE_WIDTH_LEGEND_DOT}"/>'
            )
            lines.append(
                f'  <text x="{lx + 32}" y="{y + 11}" font-size="{FONT_SIZE_LEGEND}" font-family="Arial,sans-serif" fill="#333">{html.escape(name)}</text>'
            )
        return lines
