import base64
import io
import math

import matplotlib.pyplot as plt
from js import document
from pyscript import when
from pyscript.web import page

from calculations import AntennaCalculator, Calculator


def icnirp_1998_h_limit_a_per_m(f_hz: float) -> float:
    """ICNIRP 1998 reference level for magnetic field strength H [A/m] (general public), RF range."""
    f_mhz = f_hz / 1e6
    if f_mhz < 10.0:
        return 0.73 / max(f_mhz, 1e-9)
    if f_mhz <= 400.0:
        return 0.073
    if f_mhz <= 2000.0:
        return 0.0037 * math.sqrt(f_mhz)
    return 0.16


def icnirp_1998_h_limit_section_text(f_hz: float) -> str:
    """Human-readable ICNIRP 1998 note focused on HF range only."""
    return (
        "Using ICNIRP 1998 general public: "
        "0.1-10 MHz: H = 0.73/f_MHz A/m; "
        "10-30 MHz: H = 0.073 A/m."
    )


@when("click", "#btn_calculate_antenna")
def do_calculate_inductance(e=None):
    (antenna_D_m_text,) = page["input#antenna_D_m"].value
    (d_m_text,) = page["input#d_m"].value
    (f_L_MHz_text,) = page["input#f_L_MHz"].value
    (bw_kHz_text,) = page["input#bw_kHz"].value
    (P_W_text,) = page["input#P_W"].value

    antenna_D_m = float(antenna_D_m_text)
    d_m = float(d_m_text)
    f_Hz = float(f_L_MHz_text) * 1e6
    bw_Hz = float(bw_kHz_text) * 1e3
    P_W = float(P_W_text)

    ac = AntennaCalculator(
        antenna_D_m=antenna_D_m,
        d_m=d_m,
        f_Hz=f_Hz,
        bw_Hz=bw_Hz,
        P_W=P_W,
    )

    page["b#out_L_uH"].innerHTML = f"{ac.L_H:.3g}"
    page["b#out_C_pF"].innerHTML = f"{ac.C_F:.3g}"
    page["b#out_Q0"].innerHTML = f"{ac.Q0:.3g}"
    page["b#out_RT_mOhm"].innerHTML = f"{ac.RT_Ohm:.3g}"
    page["b#out_RLoss_Ohm"].innerHTML = f"{(ac.RT_Ohm - ac.RR_Ohm):.3g}"
    page["b#out_RR_mOhm"].innerHTML = f"{ac.RR_Ohm:.3g}"
    page["b#out_eta_percent"].innerHTML = f"{(100.0 * ac.RR_Ohm / ac.RT_Ohm):.3g}"
    page["b#out_I_main_loop_A"].innerHTML = f"{ac.I_main_loop_A:.3g}"
    page["b#out_U_loop_V"].innerHTML = f"{ac.U_loop_V:.0f}"
    page["b#out_m_Am2"].innerHTML = f"{ac.m_Am2:.3g}"


@when("click", "#btn_copy_above")
def copy_values_from_above(e=None):
    document.getElementById("m_Am2").value = page["b#out_m_Am2"].innerHTML[0]
    document.getElementById("f_MHz").value = page["input#f_L_MHz"].value[0]
    document.getElementById("field_D_m").value = page["input#antenna_D_m"].value[0]


def do_calculate(e):
    (m_Am2_text,) = page["input#m_Am2"].value
    (f_MHz_text,) = page["input#f_MHz"].value
    (x_m_text,) = page["input#x_m"].value
    (y_m_text,) = page["input#y_m"].value
    (z_m_text,) = page["input#z_m"].value
    (lim_x_m_text,) = page["input#lim_x_m"].value
    (lim_y_m_text,) = page["input#lim_y_m"].value
    (line_at_field_text,) = page["input#line_at_field"].value
    m_Am2 = float(m_Am2_text)
    f_Hz = float(f_MHz_text) * 1e6
    x_m = float(x_m_text)
    y_m = float(y_m_text)
    z_m = float(z_m_text)
    lim_x_m = float(lim_x_m_text)
    lim_y_m = float(lim_y_m_text)
    line_tokens = line_at_field_text.replace(",", " ").split()
    levels = sorted({float(token) for token in line_tokens}) if line_tokens else None
    show_icnirp_blue = True
    show_icnirp_node = document.getElementById("show_icnirp_blue")
    if show_icnirp_node is not None:
        show_icnirp_blue = bool(show_icnirp_node.checked)

    d_min_abstand_m = 0.01
    try:
        (antenna_D_m_text,) = page["input#field_D_m"].value
        antenna_D_m = float(antenna_D_m_text)
    except Exception:
        antenna_D_m = 1.0

    calculator = Calculator(
        antenna_D_m=antenna_D_m,
        R_m=antenna_D_m / 2,
        m_Am2=m_Am2,
        f_Hz=f_Hz,
    )

    rho_m = math.sqrt(y_m**2 + z_m**2)
    r_loop_m = antenna_D_m / 2.0
    d_abstand_zu_wire = math.sqrt((rho_m - r_loop_m) ** 2 + x_m**2)

    warning_node = document.getElementById("h_warning")
    if d_abstand_zu_wire < d_min_abstand_m:
        if warning_node is not None:
            warning_node.innerHTML = (
                f"Warning: too close to conductor (d&lt;{d_min_abstand_m:g} m), value not shown."
            )
        page["b#h_abs"].innerHTML = "NaN"
    else:
        if warning_node is not None:
            warning_node.innerHTML = ""

        h_field_at_point = float(
            calculator.h_field_abs_xyz(
                x_m=x_m,
                y_m=y_m,
                z_m=z_m,
                m_Am2=m_Am2,
                antenna_D_m=antenna_D_m,
                f_Hz=f_Hz,
            )
        )
        page["b#h_abs"].innerHTML = f"{h_field_at_point:.4g}"

    icnirp_limit_a_per_m = icnirp_1998_h_limit_a_per_m(f_Hz)
    page["b#out_icnirp_limit"].innerHTML = f"{icnirp_limit_a_per_m:.3g}"
    page["small#out_icnirp_section"].innerHTML = icnirp_1998_h_limit_section_text(f_Hz)

    figure_h_field_plot = calculator.figure_h_field_plot(
        lim_x_m=lim_x_m,
        lim_y_m=lim_y_m,
        levels=levels,
        icnirp_limit_a_per_m=icnirp_limit_a_per_m,
        show_icnirp_blue=show_icnirp_blue,
        d_min_abstand_m=d_min_abstand_m,
    )

    svg_buffer = io.BytesIO()
    figure_h_field_plot.savefig(svg_buffer, format="svg", bbox_inches="tight", pad_inches=0.01)
    plt.close(figure_h_field_plot)
    svg_text = svg_buffer.getvalue().decode("utf-8")
    svg_data = base64.b64encode(svg_text.encode("utf-8")).decode("ascii")

    page["div#figure_h_field_plot"].innerHTML = ""
    page["div#figure_h_field_plot"].innerHTML = svg_text
    document.getElementById("download_svg").setAttribute(
        "href", f"data:image/svg+xml;base64,{svg_data}"
    )


@when("change", "#show_icnirp_blue")
def on_show_icnirp_blue_change(e=None):
    do_calculate(e)


# Render initial values on page load:
# 1) calculate antenna
# 2) copy from above
# 3) calculate H-field
try:
    do_calculate_inductance(None)
    copy_values_from_above(None)
    do_calculate(None)
except Exception as e:
    print(f"Initial render failed: {e}")
