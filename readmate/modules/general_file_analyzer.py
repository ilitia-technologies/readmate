import os
import json
import yaml
import re
import toml
import configparser


class FileAnalyzer:
    def __init__(self, file_path):
        self.file_path = file_path
        self.content = self.read_file()

    def read_file(self):
        with open(self.file_path, "r", encoding="utf-8") as file:
            return file.read()

    def analyze(self):
        raise NotImplementedError("Subclass must implement abstract method")


class MarkdownAnalyzer(FileAnalyzer):
    def analyze(self):
        headings = re.findall(r"^#+\s.*$", self.content, re.MULTILINE)
        links = re.findall(r"\[.*?\]\((.*?)\)", self.content)
        images = re.findall(r"!\[.*?\]\((.*?)\)", self.content)
        return {"headings": headings, "links": links, "images": images}


class IPYNBAnalyzer(FileAnalyzer):
    def read_file(self):
        # Overriding to load JSON directly
        with open(self.file_path, "r", encoding="utf-8") as file:
            return json.load(file)

    def analyze(self):
        code_cells = sum(
            1 for cell in self.content["cells"] if cell["cell_type"] == "code"
        )
        markdown_cells = sum(
            1 for cell in self.content["cells"] if cell["cell_type"] == "markdown"
        )
        return {"code_cells": code_cells, "markdown_cells": markdown_cells}


class YAMLAnalyzer(FileAnalyzer):
    def read_file(self):
        # Overriding to parse YAML directly
        with open(self.file_path, "r", encoding="utf-8") as file:
            return yaml.safe_load(file)

    def analyze(self):
        return list(self.content.keys())


class INIAnalyzer(FileAnalyzer):
    def read_file(self):
        # Overriding to parse INI directly
        config = configparser.ConfigParser()
        config.read_string(self.content)
        return config

    def analyze(self):
        return {
            "sections": len(self.content.sections()),
            "options": sum(
                len(self.content[section]) for section in self.content.sections()
            ),
        }


class TOMLAnalyzer(FileAnalyzer):
    def read_file(self):
        # Overriding to parse TOML directly
        with open(self.file_path, "r", encoding="utf-8") as file:
            return toml.load(file)

    def analyze(self):
        return list(self.content.keys())


class DockerfileAnalyzer(FileAnalyzer):
    def analyze(self):
        instructions = self.content.split("\n")
        analysis_result = {"FROM": [], "RUN": []}
        for instruction in instructions:
            if instruction.startswith("FROM"):
                analysis_result["FROM"].append(instruction)
            elif instruction.startswith("RUN"):
                analysis_result["RUN"].append(instruction)
        return analysis_result


class ENVAnalyzer(FileAnalyzer):
    def analyze(self):
        variables = [
            line
            for line in self.content.split("\n")
            if line and not line.startswith("#")
        ]
        return {"variables": len(variables)}


class TextFileAnalyzer(FileAnalyzer):
    def analyze(self):
        lines = self.content.split("\n")
        word_count = sum(len(line.split()) for line in lines)
        return {"lines": len(lines), "words": word_count}


class JSONFileAnalyzer(FileAnalyzer):
    def analyze(self):
        data = json.loads(self.content)
        # Example: Return the keys at the top level of the JSON structure
        return list(data.keys())


def get_file_analyzer(file_path):
    extension_to_analyzer = {
        ".md": MarkdownAnalyzer,
        ".ipynb": IPYNBAnalyzer,
        ".yaml": YAMLAnalyzer,
        ".yml": YAMLAnalyzer,
        ".ini": INIAnalyzer,
        ".toml": TOMLAnalyzer,
        ".env": ENVAnalyzer,
    }
    _, extension = os.path.splitext(file_path)
    analyzer_class = extension_to_analyzer.get(extension.lower())
    if analyzer_class:
        return analyzer_class(file_path)
    else:
        raise ValueError(f"No analyzer found for the file type: {extension}")
