from pyscript.web import page
import base64
import io
import matplotlib.pyplot as plt

from magnetic_field_strength import Calculator


def do_calculate(e):
    (I_A_text,) = page["input#I_A"].value
    I_A = float(I_A_text)

    D_m = 1.0
    calculator = Calculator(
        D_m=D_m,
        R_m=D_m / 2,
        I_A=I_A,
        f_Hz=14.1e6,
    )

    page["b#h_field"].innerHTML = f"{calculator.h_field:9.5f} field..."

    figure_h_field_plot = calculator.figure_h_field_plot(
        lim_x_m=4,
        lim_y_m=3,
        x_step=1.0,
        y_step=1.0,
    )

    png_buffer = io.BytesIO()
    figure_h_field_plot.savefig(png_buffer, format="png", bbox_inches="tight", pad_inches=0.01)
    plt.close(figure_h_field_plot)
    png_data = base64.b64encode(png_buffer.getvalue()).decode("ascii")

    page["div#figure_h_field_plot"].innerHTML = ""
    page["div#figure_h_field_plot"].innerHTML = (
        f'<img src="data:image/png;base64,{png_data}" alt="Magnetic field plot">'
    )
