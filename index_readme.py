import pathlib
import markdown

from pyscript.web import page
from js import MathJax

readme_text = pathlib.Path("README.md").read_text()

page["div#readme"].innerHTML = markdown.markdown(readme_text)

MathJax.typesetPromise()
