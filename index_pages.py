import pathlib

from pyscript.web import page


def load(selector: str, filename: str) -> None:
    try:
        html = pathlib.Path(filename).read_text()
        page[selector].innerHTML = html
        print(f"Loaded {filename} into {selector}")
    except Exception as e:
        print(f"Error: Failed to load {filename}: {e}!")


load("div#page_calculator", "index_page_calculator.html")
