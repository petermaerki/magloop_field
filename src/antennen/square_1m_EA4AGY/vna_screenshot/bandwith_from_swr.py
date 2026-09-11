"""Reusable SWR overlay: fit parallel RLC to two measurement points and plot.
AI generated."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image


@dataclass(frozen=True)
class SWRInfos:
    image_path: str  # absolute path to the NanoVNA screenshot JPG
    left_0_1: (
        float  # plot area boundaries as fractions 0..1 (x: left→right, y: top→bottom)
    )
    right_0_1: float
    top_0_1: float
    bottom_0_1: float
    freq_min_hz: float  # x-axis range in Hz
    freq_max_hz: float
    swr_min_axis: float  # y-axis range
    swr_max_axis: float
    point_min_hz: float  # resonance: SWR minimum (delta=0)
    point_min_swr: float
    point_arb_hz: float  # arbitrary off-resonance point
    point_arb_swr: float


def solve_Q(
    Rpar: float, f0: float, f_free: float, swr_free: float, Z0: float = 50.0
) -> float:
    gam = (swr_free - 1) / (swr_free + 1)
    delta_sq = (gam**2 * (Rpar + Z0) ** 2 - (Rpar - Z0) ** 2) / (Z0**2 * (1 - gam**2))
    x = f_free / f0 - f0 / f_free
    return np.sqrt(delta_sq) / abs(x)


def swr_parallel_rlc(
    freqs: np.ndarray, Rpar: float, f0: float, Q: float, Z0: float = 50.0
) -> np.ndarray:
    delta = Q * (freqs / f0 - f0 / freqs)
    gam_sq = ((Rpar - Z0) ** 2 + Z0**2 * delta**2) / (
        (Rpar + Z0) ** 2 + Z0**2 * delta**2
    )
    return (1 + np.sqrt(gam_sq)) / (1 - np.sqrt(gam_sq))


def plot_swr_overlay(infos: SWRInfos, Z0: float = 50.0, DPI: int = 100) -> None:
    output_svg = os.path.splitext(infos.image_path)[0] + ".svg"
    img = Image.open(infos.image_path)
    W, H = img.size

    fig = plt.figure(figsize=(W / DPI, H / DPI), dpi=DPI)

    ax_bg = fig.add_axes((0, 0, 1, 1))
    ax_bg.imshow(
        np.array(img),
        aspect="auto",
        origin="upper",
        extent=(0.0, float(W), float(H), 0.0),
    )
    ax_bg.set_xlim(0, W)
    ax_bg.set_ylim(H, 0)
    ax_bg.axis("off")

    left = infos.left_0_1
    bottom = 1.0 - infos.bottom_0_1  # matplotlib origin is bottom-left
    width = infos.right_0_1 - infos.left_0_1
    height = infos.bottom_0_1 - infos.top_0_1

    ax = fig.add_axes((left, bottom, width, height))
    ax.set_xlim(infos.freq_min_hz, infos.freq_max_hz)
    ax.set_ylim(infos.swr_min_axis, infos.swr_max_axis)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.patch.set_alpha(0)
    for spine in ax.spines.values():
        spine.set_edgecolor("red")
        spine.set_linewidth(2)

    f0 = infos.point_min_hz
    swr_min = infos.point_min_swr
    f_free = infos.point_arb_hz
    swr_free = infos.point_arb_swr

    Rpar_small = Z0 / swr_min  # undercoupled: Rpar < Z0  (blue)
    Rpar_large = Z0 * swr_min  # overcoupled:  Rpar > Z0  (red)

    freqs = np.linspace(infos.freq_min_hz, infos.freq_max_hz, 1000)
    results = []
    for Rpar, color, lw, ls in [
        (Rpar_large, "red", 8, "-"),
        (Rpar_small, "blue", 8, ":"),
    ]:
        Q = solve_Q(Rpar, f0, f_free, swr_free)
        L_val = Rpar / (2 * np.pi * f0 * Q)
        C_val = Q / (2 * np.pi * f0 * Rpar)
        B = f0 / Q
        results.append({"Rpar": Rpar, "B": B})
        print(
            f"Rpar={Rpar:.2f} Ω  Q={Q:.1f}  L={L_val * 1e6:.3f} µH  C={C_val * 1e12:.1f} pF  B={B:.0f} Hz"
        )
        ax.plot(
            freqs,
            swr_parallel_rlc(freqs, Rpar, f0, Q),
            color=color,
            linewidth=lw,
            linestyle=ls,
            alpha=0.7,
            dashes=(1, 6) if color == "blue" else (None, None),
        )

    x0 = infos.freq_min_hz + 10_000
    swr0 = infos.swr_min_axis + 0.05
    swr_step = (infos.swr_max_axis - infos.swr_min_axis) * 0.085
    fontsize = round(24 * W / 1553)
    kw: dict[str, Any] = {
        "fontsize": fontsize,
        "verticalalignment": "bottom",
        "bbox": {"facecolor": "white", "alpha": 0.6, "edgecolor": "none"},
    }
    ax.text(
        x0,
        swr0,
        f"swr min: {infos.point_min_swr:.2f} @ {infos.point_min_hz / 1e6:.3f} MHz",
        color="black",
        **kw,
    )
    ax.text(
        x0,
        swr0 + swr_step,
        f"Rpar_2={results[0]['Rpar']:.0f} Ohm\nB_unloaded_2={results[0]['B']:.0f} Hz",
        color="red",
        **kw,
    )
    ax.text(
        x0,
        swr0 + 2 * swr_step,
        f"Rpar_1={results[1]['Rpar']:.0f} Ohm\nB_unloaded_1={results[1]['B']:.0f} Hz",
        color="blue",
        **kw,
    )

    fig.savefig(output_svg, dpi=DPI, bbox_inches=None, format="svg", transparent=True)
    plt.close(fig)
    print(f"Saved {output_svg}")
