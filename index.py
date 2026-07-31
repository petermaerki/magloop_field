from pyscript.web import page
import base64
import io
import math
import matplotlib.pyplot as plt

from magnetic_field_strength import Calculator


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
    page["b#h_abs"].innerHTML = f"{h_field_at_point:.4g} A/m"

    figure_h_field_plot = calculator.figure_h_field_plot(
        lim_x_m=lim_x_m,
        lim_y_m=lim_y_m,
        x_step=1.0,
        y_step=1.0,
        levels=levels,
    )

    png_buffer = io.BytesIO()
    figure_h_field_plot.savefig(png_buffer, format="png", bbox_inches="tight", pad_inches=0.01)
    plt.close(figure_h_field_plot)
    png_data = base64.b64encode(png_buffer.getvalue()).decode("ascii")

    page["div#figure_h_field_plot"].innerHTML = ""
    page["div#figure_h_field_plot"].innerHTML = (
        f'<img src="data:image/png;base64,{png_data}" alt="Magnetic field plot">'
    )
