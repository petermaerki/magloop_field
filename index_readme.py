import pathlib

from js import MathJax
from pyscript.web import page

try:
    import markdown

    readme_text = pathlib.Path("README.md").read_text()

    page["div#readme"].innerHTML = markdown.markdown(readme_text)
except ImportError:
    page["div#readme"].innerHTML = "Error: 'import markdown' failed"


MathJax.typesetPromise()
