import ast
import json


def load_notebook(path):
    """
    Load a Jupyter Notebook from a specified path and return it as a dictionary.

    Args:
    path (str): The file path to the Jupyter Notebook (.ipynb).

    Returns:
    dict: The notebook content as a Python dictionary.
    """
    with open(path, "r", encoding="utf-8") as file:
        notebook = json.load(file)

    notebook_code = []
    notebook_markdowns = []

    for cell in notebook["cells"]:
        if cell["cell_type"] == "markdown":
            notebook_markdowns.append(cell["source"])
        elif cell["cell_type"] == "code":
            notebook_code.append(cell["source"])

    return notebook_code, notebook_markdowns


def parser_into_code(notebook):
    ast_objects = []
    for cell_extract in notebook:
        code = "".join(cell_extract)
        try:
            ast_obj = ast.parse(code)
            ast_objects.append(ast_obj)
        except SyntaxError as e:
            print(f"Syntax error in code cell: {e}")
    return ast_objects


if __name__ == "__main__":
    notebook_code, notebook_markdowns = load_notebook(path="")
    ast_objects = parser_into_code(notebook_code)
