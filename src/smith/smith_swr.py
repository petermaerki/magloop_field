#!/usr/bin/env python3
"""Draw a Smith chart using only NumPy and Matplotlib.

The implementation intentionally avoids specialized Smith-chart libraries.
All curves are generated from the Smith transform

    gamma(z) = (z - 1) / (z + 1)

with normalized impedance z = r + jx.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib as mpl

mpl.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# Output files are written next to this script.
OUTPUT_BASENAME = Path(__file__).resolve().with_name("smith_swr_empty")

# Figure rendering constants.
FIGURE_SIZE_INCHES = (8.0, 8.0)
LINE_WIDTH = 0.6
GRID_COLOR = "#c7c7c7"
RESISTANCE_COLOR = "#000000"
REACTANCE_COLOR = "#000000"
TEXT_COLOR = "#000000"
LABEL_COLOR = "#000000"
BACKGROUND_COLOR = "white"
X_LIMIT = 1.05
Y_LIMIT = 1.05
RESISTANCE_SAMPLES = 4096
REACTANCE_SAMPLES = 4096
RESISTANCE_VALUES = (0, 0.2, 0.5, 1, 2, 5)
REACTANCE_VALUES = (0.25, 0.5, 1, 2)
INFINITY_REFERENCE_RESISTANCE = 1_000_000.0
TITLE_TEXT = "SMITH"
TITLE_POSITION = (-0.1, 1.06)
BOTTOM_LEFT_TEXT = r"$Z_0=50\ \Omega$"
BOTTOM_LEFT_POSITION = (-0.1, -0.06)
CENTER_MARKER_COLOR = "#39ff14"
CENTER_MARKER_SIZE = 250.0
CENTER_MARKER_LINE_WIDTH = 2.0
RESISTANCE_AXIS_LABEL_SIZE = 30.0
INFINITY_LABEL_SIZE = 35.0
REACTANCE_LABEL_SIZE = 30.0
SWR_COLOR = "#e63946"
MODEL_COLOR = "#bef4cc"

def gamma(z: np.ndarray | complex) -> np.ndarray | complex:
    """Return the Smith-transform reflection coefficient for a normalized impedance.

    Parameters
    ----------
    z:
        Normalized impedance, either as a scalar complex value or as a NumPy array.

    Returns
    -------
    complex or ndarray
        Reflection coefficient Gamma = (z - 1) / (z + 1).
    """

    return (z - 1) / (z + 1)


def _plot_curve(ax: plt.Axes, points: np.ndarray, *, color: str, linewidth: float) -> None:
    """Plot a transformed Smith-chart curve."""

    ax.plot(points.real, points.imag, color=color, linewidth=linewidth)


def _label_rotation(point: complex) -> float:
    """Return a readable text angle derived from the label position."""

    angle = np.degrees(np.arctan2(float(np.imag(point)), float(np.real(point)))) - 90.0
    while angle > 90.0:
        angle -= 180.0
    while angle < -90.0:
        angle += 180.0
    return angle


def _reactance_label_point(reactance: float, *, positive: bool, offset: float = 0.10) -> complex:
    """Return a label anchor near the outer unit circle for a reactance value."""

    boundary_point = gamma((1j if positive else -1j) * reactance)
    scale = 1.0 + offset
    return complex(float(np.real(boundary_point)) * scale, float(np.imag(boundary_point)) * scale)


def plot_resistance_circle(ax: plt.Axes, r: float) -> np.ndarray:
    """Draw a constant-resistance circle by varying reactance only.

    Parameters
    ----------
    ax:
        Target Matplotlib axes.
    r:
        Normalized resistance value.

    Returns
    -------
    ndarray
        Complex points of the plotted curve in Gamma-plane coordinates.
    """

    x = np.linspace(-100.0, 100.0, RESISTANCE_SAMPLES)
    z = r + 1j * x
    points = np.asarray(gamma(z))
    _plot_curve(ax, points, color=RESISTANCE_COLOR, linewidth=LINE_WIDTH)
    return points


def plot_reactance_circle(ax: plt.Axes, x: float) -> np.ndarray:
    """Draw a constant-reactance arc by varying resistance only.

    Parameters
    ----------
    ax:
        Target Matplotlib axes.
    x:
        Normalized reactance value.

    Returns
    -------
    ndarray
        Complex points of the plotted curve in Gamma-plane coordinates.
    """

    r = np.linspace(0.0, 100.0, REACTANCE_SAMPLES)
    z = r + 1j * x
    points = np.asarray(gamma(z))
    _plot_curve(ax, points, color=REACTANCE_COLOR, linewidth=LINE_WIDTH)
    return points


def _add_text(ax: plt.Axes, x: float, y: float, text: str, *, ha: str = "center", va: str = "center", size: float = 25.0) -> None:
    """Add a label to the chart using the common text style."""

    ax.text(
        x,
        y,
        text,
        ha=ha,
        va=va,
        color=LABEL_COLOR,
        fontsize=size,
        bbox={"facecolor": "white", "edgecolor": "none", "pad": 0.2},
    )


def _configure_axes(ax: plt.Axes) -> None:
    """Apply the Smith-chart canvas styling."""

    ax.set_aspect("equal", adjustable="box")
    ax.set_xlim(-X_LIMIT, X_LIMIT)
    ax.set_ylim(-Y_LIMIT, Y_LIMIT)
    ax.set_facecolor(BACKGROUND_COLOR)
    ax.axis("off")


def _add_title(ax: plt.Axes, *, size: float) -> None:
    """Add the chart title in the upper-left corner."""

    ax.text(
        TITLE_POSITION[0],
        TITLE_POSITION[1],
        TITLE_TEXT,
        transform=ax.transAxes,
        ha="left",
        va="top",
        color=TEXT_COLOR,
        fontsize=size,
    )


def _add_bottom_left_text(ax: plt.Axes, *, size: float) -> None:
    """Add the Z0 annotation in the lower-left corner."""

    ax.text(
        BOTTOM_LEFT_POSITION[0],
        BOTTOM_LEFT_POSITION[1],
        BOTTOM_LEFT_TEXT,
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        color=TEXT_COLOR,
        fontsize=size,
    )


def draw_smith_chart(
    ax: plt.Axes,
    *,
    title_size: float = 30.0,
    footer_size: float = 30.0,
    resistance_label_size: float = RESISTANCE_AXIS_LABEL_SIZE,
    infinity_label_size: float = INFINITY_LABEL_SIZE,
    reactance_label_size: float = REACTANCE_LABEL_SIZE,
) -> None:
    """Draw a complete Smith chart on the provided axes."""

    _configure_axes(ax)

    # The outer unit circle is the r = 0 locus.
    for resistance in RESISTANCE_VALUES:
        plot_resistance_circle(ax, resistance)

    for reactance in REACTANCE_VALUES:
        plot_reactance_circle(ax, reactance)
        plot_reactance_circle(ax, -reactance)

    # Re-introduce the horizontal reference axis through the center.
    ax.plot([-1.0, 1.0], [0.0, 0.0], color=GRID_COLOR, linewidth=0.8)

    # Permanent center marker used in all Smith panels.
    ax.scatter(
        [0.0],
        [0.0],
        s=CENTER_MARKER_SIZE,
        facecolors=CENTER_MARKER_COLOR,
        edgecolors=CENTER_MARKER_COLOR,
        linewidths=CENTER_MARKER_LINE_WIDTH,
        zorder=-5,
    )

    # Add the title only; label placement follows the outer curves and not
    # auxiliary headings.
    _add_title(ax, size=title_size)
    _add_bottom_left_text(ax, size=footer_size)

    # Horizontal labels from the actual trace intercepts.
    for resistance in RESISTANCE_VALUES:
        label = f"{resistance:g}" if resistance != 0 else "0"
        if resistance == 0:
            x_pos = -1.045
        else:
            x_pos = (resistance - 1.0) / (resistance + 1.0)
        _add_text(ax, x_pos, 0.03, label, va="bottom", size=resistance_label_size)

    infinity_point = gamma(INFINITY_REFERENCE_RESISTANCE + 0j)
    _add_text(ax, float(np.real(infinity_point)), 0.03, "∞", va="bottom", size=infinity_label_size)

    # Reactance labels from the curve peaks.
    for reactance in REACTANCE_VALUES:
        positive_point = _reactance_label_point(reactance, positive=True)
        negative_point = _reactance_label_point(reactance, positive=False)
        positive_angle = _label_rotation(positive_point)
        negative_angle = _label_rotation(negative_point)

        ax.text(
            positive_point.real,
            positive_point.imag,
            f"+j{reactance:g}",
            ha="center",
            va="center",
            color=LABEL_COLOR,
            fontsize=reactance_label_size,
            rotation=positive_angle,
            rotation_mode="anchor",
        )
        ax.text(
            negative_point.real,
            negative_point.imag,
            f"-j{reactance:g}",
            ha="center",
            va="center",
            color=LABEL_COLOR,
            fontsize=reactance_label_size,
            rotation=negative_angle,
            rotation_mode="anchor",
        )


def draw_swr_chart(
    ax: plt.Axes,
    freqs_hz: np.ndarray,
    gamma: np.ndarray,
    gamma_model: np.ndarray | None = None,
) -> None:
    """Draw SWR vs. frequency on ax, styled like the Smith chart."""
    _mag = np.clip(np.abs(gamma), 0.0, 1.0 - 1e-12)
    swr = (1.0 + _mag) / (1.0 - _mag)
    freqs_mhz = freqs_hz / 1e6
    if gamma_model is not None:
        swr_model = (1.0 + np.abs(gamma_model)) / (1.0 - np.abs(gamma_model))

        ax.plot(
            freqs_mhz,
            swr_model,
            color=MODEL_COLOR,
            linewidth=8,
            zorder=2,
        )
    ax.set_facecolor(BACKGROUND_COLOR)
    if len(freqs_hz):
        ax.scatter(freqs_mhz, swr, s=20, color=SWR_COLOR, linewidths=0, zorder=5)

    for level in (1.0, 2.0, 3.0, 4.0, 5.0, 6.0):
        ax.axhline(level, color=GRID_COLOR, linewidth=0.8)

    ax.set_ylim(1.0, 6.0)
    ax.set_yticks([1.0, 2.0, 3.0, 4.0, 5.0, 6.0])

    # Restrict x-axis to the contiguous region around the SWR minimum where SWR ≤ 6
    if len(freqs_mhz) >= 2:
        i_min = int(np.argmin(swr))
        lo = i_min
        while lo > 0 and swr[lo - 1] <= 6.0:
            lo -= 1
        hi = i_min
        while hi < len(swr) - 1 and swr[hi + 1] <= 6.0:
            hi += 1
        if lo < hi:
            ax.set_xlim(freqs_mhz[lo], freqs_mhz[hi])
    fontsize = 30
    ax.set_xlabel("Frequenz (MHz)", color=TEXT_COLOR, fontsize=fontsize)
    ax.set_ylabel("SWR", color=TEXT_COLOR, fontsize=fontsize)
    ax.text(0.99, 0.98, r"$Z_0=50\ \Omega$", transform=ax.transAxes,
            ha="right", va="top", color=TEXT_COLOR, fontsize=fontsize)
    ax.tick_params(colors=TEXT_COLOR, labelsize=fontsize, pad=10)
    ax.grid(axis="x", color=GRID_COLOR, linewidth=0.8)
    for spine in ax.spines.values():
        spine.set_edgecolor(GRID_COLOR)


def _save_outputs(fig: plt.Figure) -> None:
    """Save the chart in SVG format."""

    fig.savefig(OUTPUT_BASENAME.with_suffix(".svg"), format="svg", bbox_inches="tight")


def main() -> None:
    """Create the Smith chart, display it, and save all output formats."""

    base = Path(__file__).resolve().parent

    fig, ax = plt.subplots(figsize=FIGURE_SIZE_INCHES)
    fig.patch.set_facecolor(BACKGROUND_COLOR)
    draw_smith_chart(ax)
    fig.savefig(base / "smith_empty.svg", format="svg", bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=FIGURE_SIZE_INCHES)
    fig.patch.set_facecolor(BACKGROUND_COLOR)
    draw_swr_chart(ax, np.array([]), np.array([]))
    fig.savefig(base / "swr_empty.svg", format="svg", bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()
