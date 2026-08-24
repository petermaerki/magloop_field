import pathlib

from js import MathJax
from pyscript.web import page


def load(selector: str, filename: str) -> None:
    try:
        html = pathlib.Path(filename).read_text()
        page[selector].innerHTML = html
        print(f"Loaded {filename} into {selector}")
    except Exception as e:
        print(f"Error: Failed to load {filename}: {e}!")


def load_md(selector: str, filename: str) -> None:
    try:
        import markdown
    except ImportError:
        msg = "Error: 'import markdown' failed"
        page[selector].innerHTML = msg
        print(f"Error: Failed to load {filename}: {msg}!")

    try:
        readme_text = pathlib.Path(filename).read_text()
        page[selector].innerHTML = markdown.markdown(readme_text)
        print(f"Loaded {filename} into {selector}")
    except Exception as e:
        print(f"Error: Failed to load {filename}: {e}!")


load(
    "div#page_vergleich", "./resources/index_page_vergleich.html"
)
load(
    "div#page_calculator", "./resources/index_page_calculator.html"
)

# Must be loaded after 'page_calcuator'!
load_md("div#readme", "./README.md")


MathJax.typesetPromise()
