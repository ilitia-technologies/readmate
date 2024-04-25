SYSTEM_PYTHON_MESSAGE = """
You are a useful expert in Python.
"""

V2_PYTHON_MSG = """
You are a Python File Analyzer AI, specializing in meticulously reviewing Python scripts to identify classes,
functions, and top-level executable code. Your expertise lies in extracting and elucidating critical segments of code,
providing insights into their functionality and significance. Guide users through understanding the structure and logic 
of their Python files, from parsing classes and functions to highlighting essential lines of code. Offer detailed explanations 
of syntax, best practices, and the roles of various components within a script. Provide actionable advice on optimizing and refactoring code,
ensuring users can enhance their codebase effectively. Offer resources and suggestions for deeper analysis, enabling users to improve their 
proficiency in Python development and code analysis.

"""


PY_FUNCTIONS = """
Given input: A dictionary of functions from a Python file, structured as {ast_analysis}.

Objective:
1. 'Description': Generate a concise description for each key function in the dictionary. This should succinctly explain the purpose and functionality of each function.
2. 'CodeExtractions': For each function, extract crucial code segments and provide comments explaining their significance and operation. The aim is to highlight and clarify how the function achieves its primary tasks.

Instructions:
- Ensure each function description is clear, brief, and informative, offering insight into the function's role within the Python file.
- When extracting code, focus on segments essential for understanding the function's logic and operation. Include explanatory comments that demystify the code's purpose and execution steps.
"""


PY_CLASSES = """
Given input: A dictionary of Python classes and their associated code, structured as {ast_analysis}.

Objective:
1. 'Description': Provide a comprehensive description for each class. This description should cover the class's purpose, its main functionalities, and how it interacts with other components of the code.
2. 'CodeExtractions': Identify and extract key code segments within each class. For each segment, include comments that explain its significance, focusing on how it contributes to the class's overall functionality.

Instructions:
- Ensure the class descriptions are informative, offering insight into the class's role and capabilities within the Python file.
- When extracting and commenting on code, select pieces that are crucial for understanding the class's behavior and structure. Your comments should clarify the operation and purpose of these code segments.
"""

PY_TOP_LEVEL_CODE = """
Given input: The top-level, or runnable, code located outside any function or class. Structured as {ast_analysis}.

Objective:
1. 'Description': Generate a detailed description of the top-level code, including its role in the application, how it initiates the program, and its interactions with classes or functions.
2. 'CodeExtractions': Extract and provide comments for essential segments of the top-level code. Focus on portions that are key to understanding how the program starts, its main operations, and any critical function calls or class instantiations.

Instructions:
- The description should clearly convey the purpose and functionality of the top-level code, highlighting its significance in the overall application.
- For code extractions, choose segments that offer insight into the program's flow and operational logic. Accompany these extractions with comments explaining their role and how they contribute to the program's execution.
"""

# Deprecated
PYTHON_ANALYZER = """

Readme Sections: {readme_section}

1st Input dict: {non_module_file} & 2nd Input dict: {file_info}

This first dict contains information about the folder module (not the files) where the python file you are analyzing is located and the second one
was obtained using the python library ast and contains: [imports, functions, classes, top_level_script]. Taking this into account obtain the following information:

Information to obtain: 

'ReadmeSection': "In what section would you consider putting this file",
'Description': "A description of what this python file does."
'CodeExtractions': "Gather key Python code if it is runnable code. If the code contains only class, function, or utility definitions, say just that."
'Technologies' "Technologies or languages this file uses"
'Classes':"short overview of what each of the classes of the modules do, if any"
'Functions':"short overview of what each of the functions of the modules do, if any. Consider also the functions inside the classes."
'Imports': "From the list of imports of the 2nd dict, filter the ones that are local imports and discard the ones that come from external package managers."

Take into account that this information will be displayed in a markdown readme file so take into account the writing convention of python readme files
and write it as similar as possible.
"""
