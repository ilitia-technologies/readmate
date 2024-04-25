import ast
import tiktoken
from readmate.utils.logger import set_logger
from readmate.utils.general_utils import num_tokens_from_string

_logger = set_logger()


# TODO: V2: Examples Module
# TODO: V2: Testing Module
# TODO: V2: Link Search Agent (Import related)

# TODO: V3: Python analyzer , token count, times, read or not


class PythonFileAnalyzer(ast.NodeVisitor):
    def __init__(self, file_path):
        self.file_path = file_path
        with open(file_path, "r", encoding="utf-8-sig") as file:
            self.content = file.read()
            try:
                self.node = ast.parse(self.content, file_path)
            except SyntaxError as e:
                _logger.error(f"Syntax error while parsing {file_path}: {e}")
                # BUG: Change it to run the normal mode ( general file analyzer)
                self.node = ast.Module(body=[], type_ignores=[])
        self.analysis = {
            "imports": [],
            "functions": {},
            "classes": {},
            "top_level_script": [],
            "total_classes_token_count": 0,
            "total_funcs_token_count": 0,
        }

        # BUG: Snapshot of code/text could not be enough (In Python files we get more info)
        self.token_limit: int = 100

    def analyze(self):
        for item in self.node.body:
            if isinstance(item, (ast.Import, ast.ImportFrom)):
                self._process_import(item)
            elif isinstance(item, ast.FunctionDef):
                self.analysis["functions"][item.name] = self._get_function_info(item)
            elif isinstance(item, ast.ClassDef):
                self.analysis["classes"][item.name] = self._get_class_info(item)
            else:
                self._process_top_level_statement(item)

        self._calculate_totals()
        return self.analysis

    def _process_import(self, item):
        if isinstance(item, ast.Import):
            for alias in item.names:
                # Treat all direct imports as package imports
                self.analysis["imports"].append(alias.name)
        elif isinstance(item, ast.ImportFrom):
            # Build the full import path
            for alias in item.names:
                full_import_path = (
                    f"{item.module}.{alias.name}" if item.module else alias.name
                )

                self.analysis["imports"].append(full_import_path)

    # Remember to implement the visit_Import and visit_ImportFrom methods to call _process_import
    def visit_Import(self, node):
        self._process_import(node)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        # overwride to function the same as visit_import
        self._process_import(node)
        self.generic_visit(node)

    def _get_function_info(self, func_node):
        self.token_limit = 100
        args = [arg.arg for arg in func_node.args.args]
        # Check for return type annotation
        return_type = ast.unparse(func_node.returns) if func_node.returns else "Unknown"

        read_segment = ast.get_source_segment(self.content, func_node)

        token_counter = num_tokens_from_string(read_segment, "cl100k_base")
        if token_counter > self.token_limit:
            encoding = tiktoken.get_encoding("cl100k_base")
            read_segment = encoding.decode(
                encoding.encode(read_segment)[: self.token_limit]
            )
            token_counter = self.token_limit

        return {
            "type": "function",
            "inputs": args,
            "output": return_type or "Unknown",  # Use type hints if available
            "code": read_segment,
            "token_count": token_counter,
        }

    def _get_class_info(self, class_node):
        bases = [base.id for base in class_node.bases if isinstance(base, ast.Name)]
        methods = {}
        attributes = []
        for elem in class_node.body:
            if isinstance(elem, ast.FunctionDef):
                methods[elem.name] = self._get_function_info(elem)
            elif isinstance(elem, ast.Assign):
                for target in elem.targets:
                    if isinstance(target, ast.Name):
                        attributes.append(target.id)

        class_token_count = sum(info["token_count"] for info in methods.values())
        return {
            "type": "class",
            "bases": bases,
            "attributes": attributes,
            "methods": methods,
            "token_count": class_token_count,
        }

    def _process_top_level_statement(self, item):
        self.analysis["top_level_script"].append(
            ast.get_source_segment(self.content, item)
        )

    def _calculate_totals(self):
        self.analysis["total_classes_token_count"] = sum(
            info["token_count"] for info in self.analysis["classes"].values()
        )
        self.analysis["total_funcs_token_count"] = sum(
            info["token_count"] for info in self.analysis["functions"].values()
        )
