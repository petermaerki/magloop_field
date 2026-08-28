"""Generates compare.html — comparison table for magnetic loop antennas."""

import html
import math

from .antenna_calculations import (
    _make_calc,
)
from .constants import C_LIGHT_MS
from .datatypes import Antenna

FILENAME_SVG_ETA_F = "generated_magnetic_loops_compare_eta_f.svg"
ID_SVG_ETA_F = "id_svg_eta_f"
FILENAME_SVG_ETA_DL = "generated_magnetic_loops_compare_eta_DL.svg"

class Diagramm_eta_f_svg:
    _BAND_CENTERS_MHZ = [
        1.85,
        3.65,
        5.35,
        7.1,
        10.1,
        14.2,
        21.2,
        28.5,
    ]  # ITU amateur band centers

    _W = 860
    _H = 520
    _ML = 85  # margin left
    _MR = 230  # margin right (legend)
    _MT = 40  # margin top
    _MB = 65  # margin bottom

    _F_MIN_HZ = 1.5e6
    _F_MAX_HZ = 35.0e6
    _ETA_MIN = 1.0e-5  # 0.001 %

    def __init__(self) -> None:
        self._pw = self._W - self._ML - self._MR
        self._ph = self._H - self._MT - self._MB
        self._ETA_MAX = 1.0  # overwritten in render() from data

    def _px(self, f_Hz: float) -> float:
        lf = math.log10(f_Hz)
        lmin = math.log10(self._F_MIN_HZ)
        lmax = math.log10(self._F_MAX_HZ)
        return self._ML + (lf - lmin) / (lmax - lmin) * self._pw

    def _visible_band_centers_mhz(self) -> list[float]:
        return [
            f_mhz
            for f_mhz in self._BAND_CENTERS_MHZ
            if self._F_MIN_HZ <= f_mhz * 1e6 <= self._F_MAX_HZ
        ]

    def _py(self, eta: float) -> float:
        if eta <= 0:
            return self._MT + self._ph
        le = math.log10(eta)
        lmin = math.log10(self._ETA_MIN)
        lmax = math.log10(self._ETA_MAX)
        return self._MT + (1.0 - (le - lmin) / (lmax - lmin)) * self._ph

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
            self._ETA_MAX = 10.0 ** math.ceil(math.log10(max(all_etas)))
        buf: list[str] = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self._W}" height="{self._H}" viewBox="0 0 {self._W} {self._H}">',
            f'  <rect width="{self._W}" height="{self._H}" fill="white"/>',
            f'  <clipPath id="plotarea"><rect x="{self._ML}" y="{self._MT}" width="{self._pw}" height="{self._ph}"/></clipPath>',
        ]
        buf += self._draw_grid()
        buf += self._draw_frame()
        buf += self._draw_x_ticks()
        buf += self._draw_y_ticks()
        buf += self._draw_axis_labels()
        for antenna, pts in data:
            buf += self._draw_series(pts, antenna.color)
        buf += self._draw_legend(
            [(antenna.antenna_label, antenna.color) for antenna, _ in data]
        )
        buf.append("</svg>")
        return "\n".join(buf)

    def _draw_grid(self) -> list[str]:
        lines = []
        x0, x1 = self._ML, self._ML + self._pw
        y0, y1 = self._MT, self._MT + self._ph
        for f_mhz in self._visible_band_centers_mhz():
            x = self._px(f_mhz * 1e6)
            lines.append(
                f'  <line x1="{x:.1f}" y1="{y0}" x2="{x:.1f}" y2="{y1}" stroke="#e0e0e0" stroke-width="1"/>'
            )
        exp_max = round(math.log10(self._ETA_MAX))
        for exp in range(-5, exp_max + 1):
            y = self._py(10.0**exp)
            lines.append(
                f'  <line x1="{x0}" y1="{y:.1f}" x2="{x1}" y2="{y:.1f}" stroke="#e0e0e0" stroke-width="1"/>'
            )
        return lines

    def _draw_frame(self) -> list[str]:
        return [
            f'  <rect x="{self._ML}" y="{self._MT}" width="{self._pw}" height="{self._ph}" fill="none" stroke="#888" stroke-width="1.5"/>',
        ]

    def _draw_x_ticks(self) -> list[str]:
        lines = []
        y_base = self._MT + self._ph
        for f_mhz in self._visible_band_centers_mhz():
            x = self._px(f_mhz * 1e6)
            lines.append(
                f'  <line x1="{x:.1f}" y1="{y_base}" x2="{x:.1f}" y2="{y_base + 5}" stroke="#888" stroke-width="1.5"/>'
            )
            lines.append(
                f'  <text x="{x:.1f}" y="{y_base + 18}" text-anchor="middle" font-size="11" font-family="Arial,sans-serif" fill="#333">{f_mhz:.1f}</text>'
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
                f'  <line x1="{self._ML - 5}" y1="{y:.1f}" x2="{self._ML}" y2="{y:.1f}" stroke="#888" stroke-width="1.5"/>'
            )
            lines.append(
                f'  <text x="{self._ML - 8}" y="{y + 4:.1f}" text-anchor="end" font-size="11" font-family="Arial,sans-serif" fill="#333">{label}</text>'
            )
        return lines

    def _draw_axis_labels(self) -> list[str]:
        cx = self._ML + self._pw / 2
        cy = self._MT + self._ph / 2
        return [
            f'  <text x="{cx:.1f}" y="{self._MT + self._ph + 50}" text-anchor="middle" font-size="13" font-family="Arial,sans-serif" fill="#222">f (MHz)</text>',
            f'  <text transform="rotate(-90 25 {cy:.1f})" x="25" y="{cy:.1f}" text-anchor="middle" font-size="13" font-family="Arial,sans-serif" fill="#222">η (Wirkungsgrad)</text>',
        ]

    def _draw_series(self, pts: list[tuple[float, float]], color: str) -> list[str]:
        lines = []
        coords = " ".join(f"{self._px(f):.2f},{self._py(e):.2f}" for f, e in pts)
        lines.append(
            f'  <polyline points="{coords}" fill="none" stroke="{color}" stroke-width="1.8" clip-path="url(#plotarea)"/>'
        )
        for f, e in pts:
            x, y = self._px(f), self._py(e)
            lines.append(
                f'  <circle cx="{x:.2f}" cy="{y:.2f}" r="4" fill="{color}" stroke="white" stroke-width="1" clip-path="url(#plotarea)"/>'
            )
        return lines

    def _draw_legend(self, entries: list[tuple[str, str]]) -> list[str]:
        lines = []
        lx = self._ML + self._pw + 18
        ly = self._MT + 10
        for i, (name, color) in enumerate(entries):
            y = ly + i * 22
            lines.append(
                f'  <line x1="{lx}" y1="{y + 7}" x2="{lx + 25}" y2="{y + 7}" stroke="{color}" stroke-width="2"/>'
            )
            lines.append(
                f'  <circle cx="{lx + 12}" cy="{y + 7}" r="4" fill="{color}" stroke="white" stroke-width="1"/>'
            )
            lines.append(
                f'  <text x="{lx + 32}" y="{y + 11}" font-size="11" font-family="Arial,sans-serif" fill="#333">{html.escape(name)}</text>'
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
        x0, x1 = self._ML, self._ML + self._pw
        y0, y1 = self._MT, self._MT + self._ph
        if xs:
            for tick in range(6):
                x_value = self._X_MIN + (self._X_MAX - self._X_MIN) * tick / 5.0
                x = self._px(x_value)
                lines.append(
                    f'  <line x1="{x:.1f}" y1="{y0}" x2="{x:.1f}" y2="{y1}" stroke="#e0e0e0" stroke-width="1"/>'
                )
        exp_max = round(math.log10(self._ETA_MAX))
        for exp in range(-5, exp_max + 1):
            y = self._py(10.0**exp)
            lines.append(
                f'  <line x1="{x0}" y1="{y:.1f}" x2="{x1}" y2="{y:.1f}" stroke="#e0e0e0" stroke-width="1"/>'
            )
        return lines

    def _draw_frame(self) -> list[str]:
        return [
            f'  <rect x="{self._ML}" y="{self._MT}" width="{self._pw}" height="{self._ph}" fill="none" stroke="#888" stroke-width="1.5"/>'
        ]

    def _draw_x_ticks(self, xs: list[float]) -> list[str]:
        lines = []
        y_base = self._MT + self._ph
        if xs:
            for tick in range(6):
                x_value = self._X_MIN + (self._X_MAX - self._X_MIN) * tick / 5.0
                x = self._px(x_value)
                lines.append(
                    f'  <line x1="{x:.1f}" y1="{y_base}" x2="{x:.1f}" y2="{y_base + 5}" stroke="#888" stroke-width="1.5"/>'
                )
                label = (
                    f"{x_value:.2f}".rstrip("0").rstrip(".") if x_value != 0 else "0"
                )
                lines.append(
                    f'  <text x="{x:.1f}" y="{y_base + 18}" text-anchor="middle" font-size="11" font-family="Arial,sans-serif" fill="#333">{label}</text>'
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
                f'  <line x1="{self._ML - 5}" y1="{y:.1f}" x2="{self._ML}" y2="{y:.1f}" stroke="#888" stroke-width="1.5"/>'
            )
            lines.append(
                f'  <text x="{self._ML - 8}" y="{y + 4:.1f}" text-anchor="end" font-size="11" font-family="Arial,sans-serif" fill="#333">{label}</text>'
            )
        return lines

    def _draw_axis_labels(self) -> list[str]:
        cx = self._ML + self._pw / 2
        cy = self._MT + self._ph / 2
        return [
            f'  <text x="{cx:.1f}" y="{self._MT + self._ph + 50}" text-anchor="middle" font-size="13" font-family="Arial,sans-serif" fill="#222">D / λ</text>',
            f'  <text transform="rotate(-90 25 {cy:.1f})" x="25" y="{cy:.1f}" text-anchor="middle" font-size="13" font-family="Arial,sans-serif" fill="#222">η (Wirkungsgrad)</text>',
        ]

    def _draw_series(self, pts: list[tuple[float, float]], color: str) -> list[str]:
        lines = []
        coords = " ".join(f"{self._px(x):.2f},{self._py(e):.2f}" for x, e in pts)
        lines.append(
            f'  <polyline points="{coords}" fill="none" stroke="{color}" stroke-width="1.8" clip-path="url(#plotarea)"/>'
        )
        for x, e in pts:
            x_pos, y_pos = self._px(x), self._py(e)
            lines.append(
                f'  <circle cx="{x_pos:.2f}" cy="{y_pos:.2f}" r="4" fill="{color}" stroke="white" stroke-width="1" clip-path="url(#plotarea)"/>'
            )
        return lines

    def _draw_legend(self, entries: list[tuple[str, str]]) -> list[str]:
        lines = []
        lx = self._ML + self._pw + 18
        ly = self._MT + 10
        for i, (name, color) in enumerate(entries):
            y = ly + i * 22
            lines.append(
                f'  <line x1="{lx}" y1="{y + 7}" x2="{lx + 25}" y2="{y + 7}" stroke="{color}" stroke-width="2"/>'
            )
            lines.append(
                f'  <circle cx="{lx + 12}" cy="{y + 7}" r="4" fill="{color}" stroke="white" stroke-width="1"/>'
            )
            lines.append(
                f'  <text x="{lx + 32}" y="{y + 11}" font-size="11" font-family="Arial,sans-serif" fill="#333">{html.escape(name)}</text>'
            )
        return lines
