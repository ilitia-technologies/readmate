SYSTEM_MESSAGE_AGENT_V2 = """
You are a Python Project README Section Generator AI, expertly tailored for generating specific Markdown sections for README files of Python projects.
"""

SYSTEM_MESSAGE_AGENT_CUSTOM = """You are an expert on generating this section: {} of a markdown document for a python project."""

BADGES_PROMPT_V2 = """
For this requirement file, Generate GitHub badges based on the given data: {file_info}

Create:
- For each technology identified that is a programming language, generate a badge with its version, if possible.
- For each technology that you consider essential or crucial, add another badge too.
- Always try to randomize the color generated for each badge.

"""
BADGES_PROMPT = """
Generate GitHub badges based on the given data: file extensions, technologies used, and the number of lines per file : {file_descriptions}
and file extensions, technologies, number of lines, number of files and the list of files of the submodules: {module_descriptions}.

Create:
For each technology identified that is a programming language, generate a badge with its version, if possible.
Percentages of File Types calculating the distribution percentages of different file types and produce corresponding badges.

Please randomize the colors generated for each badge.
"""


INTRODUCTION_PROMPT = """
Given a JSON input detailing the names and descriptions of files, modules, and submodules within a Python project:

- **Files Described**: {file_descriptions}
- **Modules Covered**: {module_descriptions}

Your task is to distill this detailed information into a succinct, high-level abstract. This abstract should capture the overarching
purpose and vision of the project, focusing on what the project aims to achieve rather than how it does so. 
Aim for a clear and concise GitHub project description, typically 3-5 lines, that would inform potential users
or contributors about the essence of the project at a glance.
"""

PROJECT_TREE_PROMPT = """
Given a JSON input detailing the names and descriptions of files, modules, and submodules within a Python project:

- **Files Described**: {file_descriptions}
- **Modules Covered**: {module_descriptions}

Create a visual representation of the project's directory structure.
This should include all files and subdirectories, providing a clear overview of the project's organizational layout.

**Instructions:**
1. **List Main Directories**: Start by listing the main directories under the root directory.
2. **Subdirectories and Files**:
   - For each directory, recursively list its subdirectories and files.
   - Indicate the level of each directory and file using indentation or a visual marker (e.g., `├─` for directories and `└─` for files).

**Example Output Format**:

```
├─ deployment.yml
├─ module
│  ├─ extensions.json
│  ├─ launch.json
│  ├─ task.py
│  └─ run.py
├─ setup.py
├─ requirements.txt
```

Remember to use the indentation and the visual markers.

"""
FEATURES_PROMPT = """ 
Input details include:
- Project Abstract: {project_overview}
- Descriptions of files: {file_descriptions}
- Modules: {module_descriptions}

Outline the project's key features.

Format:
 | Feature | Description |
|---------|-------------|
| [Feature Name] | [Feature Description] |"
"""

# BUG: Reduce how much code is generated
MAIN_MODULES_PROMPT = """
Input details include:
- Descriptions of files: {file_descriptions}
- Modules: {module_descriptions}

Start by identifying the main modules from the list provided. Explicitly list these main modules first.

For each main module selected, provide a detailed overview that includes:
- The purpose of the module and its critical role in the overall project.
- Key interactions with other modules and how they integrate within the application.

Include relevant and concise code snippets that showcase essential functionalities of each module. Accompany these snippets with comments that clarify their purpose and usage within the module.
Example of the concise code:
```python
# Example code snippet from the module
def example_function():
    # Relevant code demonstrating key functionality
    pass
   
"""

RECOMMENDED_MODULES_PROMPT = """
Input details include:
- Descriptions of files: {file_descriptions}
- Modules: {module_descriptions}

List and explain any additional modules or libraries that enhance the functionality of 
the Python project but are not mandatory. Discuss how these recommended modules can improve performance, 
add features, or facilitate development.
"""
INSTALLATION_PROMPT = """
Input details include:
- Descriptions of files: {file_descriptions}
- Modules: {module_descriptions}

Detail the steps needed to install the Python project,
including any commands to run in the terminal or scripts to execute. 
Clarify whether the installation process differs across operating systems or environments.
"""
CONFIGURATION_PROMPT = """
Input details include:
- Descriptions of files: {file_descriptions}
- Modules: {module_descriptions}

Explain how to configure the Python project for first-time use.
This includes setting environment variables, editing configuration files, 
or any initial setup procedures required to customize the project for the user's needs.
"""
