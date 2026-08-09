import math
import pathlib

import matplotlib
import matplotlib.figure
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D

from magloop_field.calculations import Calculator

def _suggest_tick_step(limit_m: float) -> float:
    """Choose a visually reasonable tick step for a plot range."""
    if not np.isfinite(limit_m) or limit_m <= 0.0:
        return 1.0

    rough_step = max(float(limit_m) / 8.0, 0.1)
    magnitude = 10.0 ** math.floor(math.log10(rough_step))
    normalized = rough_step / magnitude

    if normalized <= 1.5:
        nice = 1.0
    elif normalized <= 3.5:
        nice = 2.0
    else:
        nice = 10.0

    return float(nice * magnitude)


def figure_h_field_plot(
    calculator: Calculator,
    lim_x_m,
    lim_y_m,
    x_step=None,
    y_step=None,
    levels=None,
    icnirp_limit_a_per_m=None,
    show_icnirp_blue=False,
    d_min_abstand_m=0.01,
) -> matplotlib.figure.Figure:
    _save_h_field_plot(
        calculator=calculator,
        lim_x_m=lim_x_m,
        lim_y_m=lim_y_m,
        x_step=x_step,
        y_step=y_step,
        levels=levels,
        icnirp_limit_a_per_m=icnirp_limit_a_per_m,
        show_icnirp_blue=show_icnirp_blue,
        d_min_abstand_m=d_min_abstand_m,
    )
    return plt.gcf()


def save_h_field_plot(
    calculator: Calculator,
    lim_x_m,
    lim_y_m,
    filename: pathlib.Path,
    x_step=None,
    y_step=None,
    levels=None,
    icnirp_limit_a_per_m=None,
    show_icnirp_blue=False,
    d_min_abstand_m=0.01,
) -> None:
    assert isinstance(calculator, Calculator)
    assert isinstance(filename, pathlib.Path)

    _save_h_field_plot(
        calculator=calculator,
        lim_x_m=lim_x_m,
        lim_y_m=lim_y_m,
        x_step=x_step,
        y_step=y_step,
        levels=levels,
        icnirp_limit_a_per_m=icnirp_limit_a_per_m,
        show_icnirp_blue=show_icnirp_blue,
        d_min_abstand_m=d_min_abstand_m,
    )
    plt.savefig(filename, bbox_inches="tight", pad_inches=0.02)
    plt.close()


def _save_h_field_plot(
    calculator:Calculator,
    lim_x_m,
    lim_y_m,
    x_step=None,
    y_step=None,
    levels=None,
    icnirp_limit_a_per_m=None,
    show_icnirp_blue=False,
    d_min_abstand_m=0.01,
) -> None:
    assert isinstance(calculator,Calculator)
    x = np.linspace(-lim_x_m, lim_x_m, 1000)
    y = np.linspace(-lim_y_m, lim_y_m, 1000)
    X, Y = np.meshgrid(x, y)
    H_total = calculator.h_field_abs_xyz(
        X,
        Y,
        0.0,
        calculator.m_Am2,
        calculator.antenna_D_m,
        calculator.f_Hz,
    )

    # Split contours into far/near region by distance to the conductor axis.
    # Loop axis is x, loop lies in y-z plane, and this plot slice uses z=0.
    rho_m = np.sqrt(Y**2)
    d_abstand_zu_wire = np.sqrt((rho_m - calculator.R_m) ** 2 + X**2)
    near_region = d_abstand_zu_wire < float(d_min_abstand_m)
    H_total_far = np.ma.masked_where(near_region, H_total)

    aspect_ratio = lim_x_m / lim_y_m if lim_y_m else 1.0
    fig_height = 8.0
    fig_width = fig_height * aspect_ratio
    plt.figure(figsize=(fig_width, fig_height))

    # Isolinien < 1 A/m
    if levels is None:
        levels = [0.05, 0.1, 0.2]
    else:
        levels = np.unique(np.asarray(levels, dtype=float))
        if levels.size == 0:
            levels = np.array([0.05, 0.1, 0.2], dtype=float)
    cp = plt.contour(
        X,
        Y,
        H_total_far,
        levels=levels,
        colors="black",
        linewidths=1.0,
        corner_mask=False,
    )
    clabels = plt.clabel(
        cp, inline=True, fmt=lambda v: f"{v:g} A/m", fontsize=10, rightside_up=True
    )
    for label in clabels:
        label.set_bbox({"facecolor": "white", "edgecolor": "none", "pad": 3})

    show_blue_limit_line = False
    if (
        show_icnirp_blue
        and icnirp_limit_a_per_m is not None
        and np.isfinite(icnirp_limit_a_per_m)
    ):
        h_min = float(np.ma.min(H_total_far))
        h_max = float(np.ma.max(H_total_far))
        if h_min <= float(icnirp_limit_a_per_m) <= h_max:
            cp_limit = plt.contour(
                X,
                Y,
                H_total_far,
                levels=[float(icnirp_limit_a_per_m)],
                colors="blue",
                linewidths=1.6,
                corner_mask=False,
            )
            limit_labels = plt.clabel(
                cp_limit,
                inline=True,
                fmt=lambda v: f"ICNIRP {v:g} A/m",
                fontsize=10,
                colors="blue",
                rightside_up=True,
            )
            for label in limit_labels:
                label.set_bbox({"facecolor": "white", "edgecolor": "none", "pad": 3})

    antennenfarbe = "red"
    # Draw conductor with end caps using centerline diameter convention.
    # D refers to the centerline (cap centers at y=±R), so outer length is D + d_leiter.
    d_leiter_m = 0.1
    r_leiter_m = d_leiter_m / 2
    rectangle = plt.Rectangle(
        (-r_leiter_m, -calculator.R_m),
        d_leiter_m,
        2 * calculator.R_m,
        color=antennenfarbe,
        fill=True,
        zorder=3.0,
    )
    plt.gca().add_artist(rectangle)

    circle1 = plt.Circle(
        (0, calculator.R_m), r_leiter_m, color=antennenfarbe, fill=True, zorder=3.0
    )
    circle2 = plt.Circle(
        (0, -calculator.R_m), r_leiter_m, color=antennenfarbe, fill=True, zorder=3.0
    )
    plt.gca().add_artist(circle1)
    plt.gca().add_artist(circle2)

    # Raster & Achsen
    x_tick_step = x_step if x_step is not None else _suggest_tick_step(lim_x_m)
    y_tick_step = y_step if y_step is not None else _suggest_tick_step(lim_y_m)
    plt.xticks(np.arange(-lim_x_m, lim_x_m + x_tick_step, x_tick_step))
    plt.yticks(np.arange(-lim_y_m, lim_y_m + y_tick_step, y_tick_step))
    plt.grid(True, which="major", linestyle="-", color="gray", alpha=0.3)
    plt.axhline(0, color="black", lw=1.2)
    plt.axvline(0, color="black", lw=1.2)

    plt.title("Magnetic Field Strength $|H|$", fontsize=12, pad=6, y=1.02)
    plt.xlabel("x [m]")
    plt.ylabel("y [m]")
    plt.gca().set_aspect("equal")
    plt.xlim(-lim_x_m, lim_x_m)
    plt.ylim(-lim_y_m, lim_y_m)

    # Contour lines are shown only outside the near-conductor exclusion zone.

    # Legende
    legend_elements = [
        Line2D([0], [0], color=antennenfarbe, lw=4, label="Antenna"),
        Line2D(
            [0],
            [0],
            marker="None",
            color="None",
            label=f"D = {calculator.antenna_D_m:.3g} m",
        ),
        Line2D(
            [0],
            [0],
            marker="None",
            color="None",
            label=f"m = {calculator.m_Am2:.2f} A m²",
        ),
        Line2D(
            [0],
            [0],
            marker="None",
            color="None",
            label=f"f = {calculator.f_Hz / 1e6:.1f} MHz",
        ),
    ]
    plt.legend(handles=legend_elements, loc="upper right", frameon=True)

    # Keep figure margins minimal and deterministic for web rendering.
    plt.subplots_adjust(left=0.06, right=0.995, bottom=0.06, top=0.96)


def main() -> None:
    antenna_D_m = 1.0
    I_A = 10.5
    m_Am2 = I_A * np.pi * (antenna_D_m / 2) ** 2
    calculator = Calculator(
        antenna_D_m=antenna_D_m,
        R_m=antenna_D_m / 2,
        m_Am2=m_Am2,
        f_Hz=14.1e6,
    )

    DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent
    output_dir = DIRECTORY_OF_THIS_FILE / "generated_images"
    output_dir.mkdir(exist_ok=True, parents=True)

    save_h_field_plot(
        calculator=calculator,
        lim_x_m=4,
        lim_y_m=3,
        filename=output_dir / "calculations.svg",
        x_step=1.0,
        y_step=1.0,
    )
    save_h_field_plot(
        calculator=calculator,
        lim_x_m=30,
        lim_y_m=60,
        filename=output_dir / "calculations_big.svg",
        x_step=10.0,
        y_step=10.0,
        levels=[0.001, 0.002, 0.005, 0.05],
    )


if __name__ == "__main__":
    main()
