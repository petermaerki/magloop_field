import base64
import math

from js import document, window
from pyodide.ffi import JsNull, create_proxy
from pyscript import when
from pyscript.web import page

from antennenvergleich import renderer_diagram_svg, webui_filter
from webui import util_compare

try:
    DEVELOPMENT_NUMPY = False
    import numpy

    DEVELOPMENT_NUMPY = True
    from magloop_field import calculations, diagram
except ModuleNotFoundError:
    pass


def load_params_from_url():
    """Load calculator parameters from URL query string and populate form fields."""
    try:
        # Get URL search params
        search_params = str(window.location.search)
        print(f"URL search params: {search_params}")

        if not search_params or search_params == "":
            print("No URL parameters found")
            return

        # Parse query string manually (remove leading '?')
        if search_params.startswith("?"):
            search_params = search_params[1:]

        # Parse key=value pairs
        params = {}
        for pair in search_params.split("&"):
            if "=" in pair:
                key, value = pair.split("=", 1)
                params[key] = value

        print(f"Parsed parameters: {params}")

        # Set values from URL parameters
        params_set = 0

        # Simple direct mapping (no conversion needed)
        direct_mapping = {
            "D_m": "antenna_D_m",
            "d_m": "d_m",
            "n": "n",
            "p_m": "p_m",
            "Pfwd_W": "Pfwd_W",
            "swr_min": "swr_min",
        }

        for param_name, field_id in direct_mapping.items():
            if param_name in params:
                input_element = document.getElementById(field_id)
                if input_element is not None:
                    input_element.value = params[param_name]
                    params_set += 1
                    print(f"Set {field_id} = {params[param_name]}")
                else:
                    print(f"Field {field_id} not found")

        # Frequency conversion: f_Hz -> MHz (for form field)
        if "f_Hz" in params:
            try:
                f_hz = float(params["f_Hz"])
                f_mhz = f_hz / 1_000_000
                input_element = document.getElementById("f_L_MHz")
                if input_element is not None:
                    input_element.value = str(f_mhz)
                    params_set += 1
                    print(f"Set f_L_MHz = {f_mhz} (converted from {f_hz} Hz)")
            except (ValueError, TypeError) as e:
                print(f"Error converting f_Hz: {e}")

        # Bandwidth conversion: bw_Hz -> kHz (for form field)
        if "bw_Hz" in params:
            try:
                bw_hz = float(params["bw_Hz"])
                bw_khz = bw_hz / 1_000
                input_element = document.getElementById("bw_kHz")
                if input_element is not None:
                    input_element.value = str(bw_khz)
                    params_set += 1
                    print(f"Set bw_kHz = {bw_khz} (converted from {bw_hz} Hz)")
            except (ValueError, TypeError) as e:
                print(f"Error converting bw_Hz: {e}")

        print(f"Set {params_set} parameters from URL")
        # Note: calculation will be triggered by the initialization code below

    except Exception as e:
        print(f"Error loading URL parameters: {e}")


#
# CALCULATOR
#
@when("click", "#btn_calculate_antenna")
def do_calculate_antenna_efficiency(e=None):
    if not DEVELOPMENT_NUMPY:
        return

    calc_button = document.getElementById("btn_calculate_antenna")
    if calc_button is not None:
        calc_button.style.backgroundColor = ""
        calc_button.style.color = ""
        calc_button.style.borderColor = ""

    (antenna_D_m_text,) = page["input#antenna_D_m"].value
    (d_m_text,) = page["input#d_m"].value
    (n_text,) = page["input#n"].value
    (p_m_text,) = page["input#p_m"].value
    (f_L_MHz_text,) = page["input#f_L_MHz"].value
    (bw_kHz_text,) = page["input#bw_kHz"].value
    (p_fwd_w_text,) = page["input#Pfwd_W"].value
    (swr_min_text,) = page["input#swr_min"].value

    try:
        antenna_D_m = float(antenna_D_m_text)
        d_m = float(d_m_text)
        n = int(n_text)
        p_m = float(p_m_text)
        f_Hz = float(f_L_MHz_text) * 1e6
        bw_Hz = float(bw_kHz_text) * 1e3
        p_fwd_w = float(p_fwd_w_text)
        swr_min = float(swr_min_text)

        ac = calculations.AntennaCalculator(
            D_m=antenna_D_m,
            d_m=d_m,
            n=n,
            swr_min=swr_min,
            f_Hz=f_Hz,
            bw262_Hz=bw_Hz,
            powerPfwd_W=p_fwd_w,
            p_m=p_m,
        )
    except calculations.InvalidAntennaInput as e:
        if calc_button is not None:
            calc_button.textContent = f"Calculate Antenna: {e}"
            calc_button.style.backgroundColor = "#ffdddd"
            calc_button.style.color = "#b00020"
            calc_button.style.borderColor = "#b00020"
        print(f"Invalid antenna input: {e}")
        return
    except ValueError as e:
        if calc_button is not None:
            calc_button.textContent = f"Calculate Antenna: {e}"
            calc_button.style.backgroundColor = "#ffdddd"
            calc_button.style.color = "#b00020"
            calc_button.style.borderColor = "#b00020"
        print(f"Invalid numeric input: {e}")
        return

    if calc_button is not None:
        calc_button.textContent = "Calculate Antenna"

    page["b#out_L_uH"].innerHTML = f"{ac.L_H:.3g}"
    page["b#out_C_pF"].innerHTML = f"{ac.C_F:.3g}"
    page["b#out_Q0"].innerHTML = f"{ac.Q0:.3g}"
    page["b#out_RT_mOhm"].innerHTML = f"{ac.RT_Ohm:.3g}"
    page["b#out_RLoss_Ohm"].innerHTML = f"{(ac.RT_Ohm - ac.RR_Ohm):.3g}"
    page["b#out_RR_mOhm"].innerHTML = f"{ac.RR_Ohm:.3g}"
    page["b#out_eta_swr_ant_percent"].innerHTML = f"{(100.0 * ac.eta_SWR_ant):.3g}"
    page["b#out_powerPload_W"].innerHTML = f"{ac.powerPload_W:.3g}"
    page["b#out_eta_percent"].innerHTML = f"{(100.0 * ac.eta):.3g}"
    page["b#out_I_main_loop_A"].innerHTML = f"{ac.I_main_loop_A:.3g}"
    page["b#out_U_loop_V"].innerHTML = f"{ac.U_loop_V:.0f}"
    page["b#out_m_Am2"].innerHTML = f"{ac.m_Am2:.3g}"


@when("click", "#btn_copy_above")
def copy_values_from_above(e=None):
    document.getElementById("m_Am2").value = page["b#out_m_Am2"].innerHTML[0]
    document.getElementById("f_MHz").value = page["input#f_L_MHz"].value[0]
    document.getElementById("field_D_m").value = page["input#antenna_D_m"].value[0]


@when("click", "#btn_calculate_h_field")
def do_calculate_h_field(e=None):
    if not DEVELOPMENT_NUMPY:
        return

    calc_button = None
    if e is not None:
        try:
            calc_button = e.currentTarget
        except Exception:
            calc_button = None

    if calc_button is not None:
        calc_button.style.backgroundColor = ""
        calc_button.style.color = ""
        calc_button.style.borderColor = ""

    try:
        (m_Am2_text,) = page["input#m_Am2"].value
        (f_MHz_text,) = page["input#f_MHz"].value
        (x_m_text,) = page["input#x_m"].value
        (y_m_text,) = page["input#y_m"].value
        (z_m_text,) = page["input#z_m"].value
        (lim_x_m_text,) = page["input#lim_x_m"].value
        (lim_y_m_text,) = page["input#lim_y_m"].value
        (line_at_field_text,) = page["input#line_at_field"].value
        (antenna_D_m_text,) = page["input#field_D_m"].value

        m_Am2 = float(m_Am2_text)
        f_Hz = float(f_MHz_text) * 1e6
        x_m = float(x_m_text)
        y_m = float(y_m_text)
        z_m = float(z_m_text)
        lim_x_m = float(lim_x_m_text)
        lim_y_m = float(lim_y_m_text)
        antenna_D_m = float(antenna_D_m_text)

        if lim_x_m < 0:
            raise calculations.InvalidAntennaInput(
                f"lim_x_m must be non-negative, got {lim_x_m}"
            )
        if lim_y_m < 0:
            raise calculations.InvalidAntennaInput(
                f"lim_y_m must be non-negative, got {lim_y_m}"
            )

        line_tokens = line_at_field_text.replace(",", " ").split()
        levels = None
        if line_tokens:
            parsed_levels = []
            for token in line_tokens:
                level = float(token)
                if not math.isfinite(level):
                    raise calculations.InvalidAntennaInput(
                        f"line_at_field contains non-finite value: {token}"
                    )
                if level <= 0:
                    raise calculations.InvalidAntennaInput(
                        f"line_at_field values must be positive, got {level}"
                    )
                parsed_levels.append(level)
            levels = sorted(set(parsed_levels))

        show_icnirp_blue = True
        show_icnirp_node = document.getElementById("show_icnirp_blue")
        if show_icnirp_node is not None:
            show_icnirp_blue = bool(show_icnirp_node.checked)

        calculator = calculations.CalculatorHField(
            antenna_D_m=antenna_D_m,
            R_m=antenna_D_m / 2,
            m_Am2=m_Am2,
            f_Hz=f_Hz,
        )
    except calculations.InvalidAntennaInput as e:
        if calc_button is not None:
            calc_button.textContent = f"Calculate H-Field: {e}"
            calc_button.style.backgroundColor = "#ffdddd"
            calc_button.style.color = "#b00020"
            calc_button.style.borderColor = "#b00020"
        print(f"Invalid H-field input: {e}")
        return
    except ValueError as e:
        if calc_button is not None:
            calc_button.textContent = f"Calculate H-Field: {e}"
            calc_button.style.backgroundColor = "#ffdddd"
            calc_button.style.color = "#b00020"
            calc_button.style.borderColor = "#b00020"
        print(f"Invalid numeric input for H-field: {e}")
        return

    if calc_button is not None:
        calc_button.textContent = "Calculate H-Field"

    d_min_abstand_m = 0.01

    rho_m = math.sqrt(y_m**2 + z_m**2)
    r_loop_m = antenna_D_m / 2.0
    d_abstand_zu_wire = math.sqrt((rho_m - r_loop_m) ** 2 + x_m**2)

    warning_node = document.getElementById("h_warning")
    if d_abstand_zu_wire < d_min_abstand_m:
        if warning_node is not None:
            warning_node.innerHTML = f"Warning: too close to conductor (d&lt;{d_min_abstand_m:g} m), value not shown."
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

    icnirp_limit_a_per_m = calculations.icnirp_1998_h_limit_a_per_m(f_Hz)
    page["b#out_icnirp_limit"].innerHTML = f"{icnirp_limit_a_per_m:.3g}"
    page[
        "small#out_icnirp_section"
    ].innerHTML = calculations.icnirp_1998_h_limit_section_text(f_Hz)

    plot = diagram.HFieldPlot(
        calculator=calculator,
        lim_x_m=lim_x_m,
        lim_y_m=lim_y_m,
        levels=levels,
        icnirp_limit_a_per_m=icnirp_limit_a_per_m,
        show_icnirp_blue=show_icnirp_blue,
        d_min_abstand_m=d_min_abstand_m,
    )

    svg_text = plot.svg_text()

    page["div#figure_h_field_plot"].innerHTML = svg_text

    svg_data = base64.b64encode(svg_text.encode("utf-8")).decode("ascii")
    document.getElementById("download_svg").setAttribute(
        "href", f"data:image/svg+xml;base64,{svg_data}"
    )


@when("change", "#show_icnirp_blue")
def on_show_icnirp_blue_change(e=None):
    do_calculate_h_field(e)


def close_splash_dialog() -> None:
    """
    Everything is loaded and rendered now: reveal the page and dismiss the splash screen.
    """
    loading = document.getElementById("loading")
    if loading is not None:
        loading.close()

    app_content = document.getElementById("app_content")
    if app_content is not None:
        app_content.style.display = "block"


#
# COMPARE
#
def query(selector: str):
    element = document.querySelector(selector)
    if element is None or isinstance(element, JsNull):
        raise ValueError(f"Error: '{selector}' not found!")
        return
    return element


def update_svg(selector: str, svg: str) -> None:
    img = query(selector=selector)
    svg_data = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    img.src = f"data:image/svg+xml;base64,{svg_data}"


def setup_compare_scrollbars() -> None:
    containers = document.querySelectorAll("#compare_results .compare-scroll-dual")
    for container in containers:
        top = container.querySelector(".compare-table-scroll-top")
        top_inner = container.querySelector(".compare-table-scroll-top-inner")
        bottom = container.querySelector(".compare-table-wrap")
        table = container.querySelector("table")
        if top is None or top_inner is None or bottom is None or table is None:
            continue

        top_inner.style.width = f"{table.scrollWidth}px"

        sync = {"active": False}

        def on_top_scroll(_event=None):
            if sync["active"]:
                return
            sync["active"] = True
            bottom.scrollLeft = top.scrollLeft
            sync["active"] = False

        def on_bottom_scroll(_event=None):
            if sync["active"]:
                return
            sync["active"] = True
            top.scrollLeft = bottom.scrollLeft
            sync["active"] = False

        proxy_top = create_proxy(on_top_scroll)
        proxy_bottom = create_proxy(on_bottom_scroll)

        top.addEventListener("scroll", proxy_top)
        bottom.addEventListener("scroll", proxy_bottom)

        # Keep proxy references alive while this DOM node exists.
        container._scroll_proxy_top = proxy_top
        container._scroll_proxy_bottom = proxy_bottom


def load_compare() -> None:
    fw = util_compare.FilterWrapper()

    def redraw():
        page["div#compare_results"].innerHTML = fw.render_results_html()
        setup_compare_scrollbars()
        svg = fw.render_eta_f_svg()
        update_svg(selector=f"img#{renderer_diagram_svg.ID_SVG_ETA_F}", svg=svg)

    redraw()

    def on_checkbox_change(checkbox: webui_filter.Checkbox, elem_input) -> None:
        try:
            print("checked_brands", checkbox, elem_input.checked)
            checkbox.set_checked(checked=elem_input.checked)
            fw.apply_filter()
            fw.filter.update_grey_states()
            redraw()

            fw.filter.dump()
        except Exception as e:
            print(f"Error in on_checkbox_change(): {e!r}")

    elem_tbody = query("tbody#compare_table_tbody")
    for category_stat in fw.filter.category_stats:
        tr = document.createElement("tr")
        elem_tbody.appendChild(tr)
        td_label = document.createElement("td")
        tr.appendChild(td_label)
        td_label.textContent = category_stat.category.value
        td_checkboxes = document.createElement("td")
        tr.appendChild(td_checkboxes)

        for checkbox in category_stat.checkboxes:
            label = document.createElement("label")
            td_checkboxes.appendChild(label)
            elem_input = document.createElement("input")
            elem_input.type = "checkbox"
            elem_input.name = checkbox.name
            elem_input.value = elem_input.name
            elem_input.checked = checkbox.checked

            def make_handler(checkbox, elem_input):
                def handler(e):
                    on_checkbox_change(checkbox, elem_input)

                return handler

            elem_input.onchange = create_proxy(make_handler(checkbox, elem_input))
            label.appendChild(elem_input)
            label.appendChild(document.createTextNode(elem_input.name))
            checkbox.bind_dom(element_label=label, element_input=elem_input)

    fw.filter.update_grey_states()


#
# COMMON
#

print("A")

if True:
    load_compare()

if True:
    # Render initial values on page load:
    # 0) load URL parameters if provided
    # 1) calculate antenna
    # 2) copy from above
    # 3) calculate H-field
    try:
        load_params_from_url()
        do_calculate_antenna_efficiency(None)
        copy_values_from_above(None)
        do_calculate_h_field(None)
    except Exception as e:
        print(f"Initial render failed: {e}")

print("B")


close_splash_dialog()

print("C")
