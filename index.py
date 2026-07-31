import base64
import io
import math

import matplotlib.pyplot as plt
from js import document
from pyscript import when
from pyscript.web import page

from calculations import AntennaCalculator, Calculator


@when("click", "#btn_calculate_antenna")
def do_calculate_inductance(e=None):
    (D_m_text,) = page["input#D_m"].value
    (d_m_text,) = page["input#d_m"].value
    (f_L_MHz_text,) = page["input#f_L_MHz"].value
    (bw_kHz_text,) = page["input#bw_kHz"].value
    (P_W_text,) = page["input#P_W"].value

    D_m = float(D_m_text)
    d_m = float(d_m_text)
    f_Hz = float(f_L_MHz_text) * 1e6
    bw_Hz = float(bw_kHz_text) * 1e3
    P_W = float(P_W_text)

    ac = AntennaCalculator(D_m=D_m, d_m=d_m, f_Hz=f_Hz, bw_Hz=bw_Hz, P_W=P_W)

    page["b#out_L_uH"].innerHTML = f"{ac.L_H:.3g}"
    page["b#out_C_pF"].innerHTML = f"{ac.C_F:.3g}"
    page["b#out_Q0"].innerHTML = f"{ac.Q0:.3g}"
    page["b#out_RT_mOhm"].innerHTML = f"{ac.RT_Ohm:.3g}"
    page["b#out_RLoss_Ohm"].innerHTML = f"{(ac.RT_Ohm - ac.RR_Ohm):.3g}"
    page["b#out_RR_mOhm"].innerHTML = f"{ac.RR_Ohm:.3g}"
    page["b#out_eta_percent"].innerHTML = f"{(ac.RR_Ohm / ac.RT_Ohm):.3g}"
    page["b#out_I_main_loop_A"].innerHTML = f"{ac.I_main_loop_A:.3g}"
    page["b#out_U_loop_V"].innerHTML = f"{ac.U_loop_V:.3g}"
    page["b#out_m_Am2"].innerHTML = f"{ac.m_Am2:.3g}"


@when("click", "#btn_copy_above")
def copy_values_from_above(e=None):
    document.getElementById("m_Am2").value = page["b#out_m_Am2"].innerHTML[0]
    document.getElementById("f_MHz").value = page["input#f_L_MHz"].value[0]


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
    levels = [float(token) for token in line_tokens] if line_tokens else None

    D_m = 1.0
    calculator = Calculator(
        D_m=D_m,
        R_m=D_m / 2,
        m_Am2=m_Am2,
        f_Hz=f_Hz,
    )

    c = 299792458.0
    k = 2.0 * math.pi * f_Hz / c
    r = math.sqrt(x_m**2 + y_m**2 + z_m**2)
    r = max(r, 1e-9)
    rho_m = math.sqrt(y_m**2 + z_m**2)
    phi = math.atan2(rho_m, x_m)
    fac = m_Am2 / (4.0 * math.pi)
    h_r_sq = fac**2 * 4.0 * math.cos(phi) ** 2 * (1.0 / r**6 + k**2 / r**4)
    h_theta_sq = fac**2 * math.sin(phi) ** 2 * (1.0 / r**6 - k**2 / r**4 + k**4 / r**2)
    h_field_at_point = math.sqrt(h_r_sq + h_theta_sq)
    page["b#h_abs"].innerHTML = f"{h_field_at_point:.4g}"

    figure_h_field_plot = calculator.figure_h_field_plot(
        lim_x_m=lim_x_m,
        lim_y_m=lim_y_m,
        x_step=1.0,
        y_step=1.0,
        levels=levels,
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


# Render initial values on page load: first antenna, then H-field.
try:
    do_calculate_inductance(None)
    do_calculate(None)
except Exception as e:
    print(f"Initial render failed: {e}")
