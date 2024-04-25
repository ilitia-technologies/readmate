SYSTEM_MESSAGE_AGENT = """
You are a useful chatbot expert in analyzing files and modules for python projects.
"""


MODULE_WITH_SUBMODULES = """

With this info:
- Current Module: {current_module}
- Number of files: {num_files}
- File extensions: {extensions}
- Total lines of code: {num_lines}
- Submodules included: {submodules},

Obtain the following:
- Description
- Technologies
- Rating


"""

MODULE_WITHOUT_SUBMODULES = """

With this info:
- Current Module: {current_module}
- Number of files: {num_files}
- File extensions: {extensions}
- Total lines of code: {num_lines},

Obtain the following:
- Description
- Technologies
- Rating


"""

OUT_FILES = """
With this info:
- File extension: {file_extension}
- Filename: {filename}
- Total lines of code: {num_lines},

Obtain the following:
- Description
- Technologies
- Rating

"""
