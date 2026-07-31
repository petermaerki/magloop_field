from pyscript.web import page
import base64
import io
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

    rho_m = (y_m**2 + z_m**2) ** 0.5
    h_field_at_point = calculator.h_field_retarded(rho_m, x_m, m_Am2, f_Hz)
    page["b#h_field"].innerHTML = f"{h_field_at_point:9.5f} A/m"

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
