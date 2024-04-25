SYSTEM_MESSAGE_INSPECTOR = """
You are an expert at analyzing {type_of_file} from Python projects. Your analysis provides detailed and 
structured content suitable for inclusion in a section of a Python project's README file.
"""
REQUIREMENTS_PROMPT = """
### Instructions

For this requirement file: {file_info}:


**Detailed Instructions:**
- **Prerequisites**: List any necessary system or software prerequisites needed before installing the Python project.
- **Python Version**: Specify the Python version(s) compatible with the project. Include minimum or specific versions if applicable.
- **Libraries and Dependencies**:
  Detail the essential libraries and dependencies required for the project. For each item, include the version if known, and highlight why it is crucial for the project.

"""


DEPLOYMENT_PROMPT = """

For this input file: {file_info}:

### Instructions Based on the input file

- If the file is Docker-related (e.g., `Dockerfile`, `.dockerignore`): Provide step-by-step instructions on how to build and run a Docker container using this file.
- If the file is Kubernetes configuration files (e.g., `deployment.yaml`, `service.yaml`): Describe the steps to deploy the project in a cluster using this file.

"""
# - **Azure DevOps pipeline files (e.g., `azure-pipelines.yml`)**:
#   Outline the critical components of the pipeline configuration, focusing on triggers, branch specifications, and environment settings, without going into detailed steps.


LICENSE_PROMPT = """

For this license file: {file_info}:

State the type of license under which the Python project is released.
Provide a brief explanation of the license, including any permissions,
limitations, and conditions it entails for users of the project.

If the license input information is empty, state that no license
was provided for this project"""


README_PROMPT = """

For this main readme file: {file_info}:

Instructions:

1. Identify Visual Content:

    - Extract any links or markdown tags that point to images or GIFs.
    - Include descriptions or alt text provided for these visuals, if available.

2. Extract Complex Code Examples:

    - Search for code blocks that are annotated with comments that suggest complexity or notable functionality.
    - Include any embedded comments within the code that explain the logic or usage of the code snippets.

3. Format Output:

Provide the results in a structured format:
    - Visuals: List the image or GIF URLs along with their descriptions.
    - Code Examples: Provide the code snippets with accompanying explanations or comments.

Additional Notes:

    - Prioritize elements that are less straightforward and require contextual understanding to appreciate their relevance or complexity.
    - Ensure the extracted information is presented clearly to be directly usable or understandable without needing to refer back to the original README.

"""
