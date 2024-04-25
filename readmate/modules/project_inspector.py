import os
import sys
import uuid
import tiktoken
import asyncio
from typing import Optional
from datetime import datetime
from readmate.chains.chat_message_chain import ChatMessageChain
from readmate.utils.logger import set_logger
from readmate.utils.utils_tools import (
    model_initialization,
)
from readmate.prompts.inspector import (
    SYSTEM_MESSAGE_INSPECTOR,
    REQUIREMENTS_PROMPT,
    DEPLOYMENT_PROMPT,
    LICENSE_PROMPT,
    README_PROMPT,
)


if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


# BUG: V2: can we do with the current readme?
# BUG: V2: Examples/Testing Module


class ProjectInspector:
    SYSTEM_MESSAGE_INSPECTOR = SYSTEM_MESSAGE_INSPECTOR
    REQUIREMENT_PROMPT = REQUIREMENTS_PROMPT
    DEPLOYMENT_PROMPT = DEPLOYMENT_PROMPT
    LICENSE_PROMPT = LICENSE_PROMPT
    README_PROMPT = README_PROMPT

    def __init__(self, directory_path):
        """
        Initialize the ProjectInspector with a path to the directory to inspect.
        :param directory_path: String representing the path to the project directory.
        """
        self.file_paths = self._gather_file_paths(directory_path)
        self._logger = set_logger()
        self.llm_selection = model_initialization()

        self.requirements_text: str = ""
        self.deployment_text: str = ""
        self.readme_text: str = ""
        self.license_text: str = ""

        self.max_category_tokens: int = 1500
        self.max_category_files: int = 3

    def dict_to_markdown_text(self, data_dict, level=0):
        """
        Converts a nested dictionary into a Markdown formatted text string with hierarchical headings.

        Args:
        data_dict (dict): The dictionary to convert.
        level (int): Current depth in the dictionary to manage heading levels.

        Returns:
        str: A Markdown formatted text string representing the dictionary.
        """
        if isinstance(data_dict, str):
            return data_dict

        plain_text = ""
        for key, value in data_dict.items():
            # Apply Markdown headings based on the depth
            heading = (
                "###" * (level + 1)
            )  # Start at '##' for top level (level 0) and increase by one for each depth
            if isinstance(value, dict):
                # If the value is a dictionary, recursively format it with increased depth
                plain_text += f"{heading} {key.capitalize()}\n\n{self.dict_to_markdown_text(value, level + 1)}"
            elif isinstance(value, list):
                # Handle list: format each item in the list under the key
                plain_text += f"{heading} {key.capitalize()}\n\n"
                for item in value:
                    if isinstance(item, dict):
                        # If item is a dictionary, recursively format it
                        plain_text += self.dict_to_markdown_text(
                            item, level + 1
                        )  # Increase level for nested dicts
                    else:
                        # Otherwise, format it as regular text
                        plain_text += f"{item}\n\n"
            else:
                # For normal key-value pairs, treat them as text under their key heading
                formatted_value = str(value)  # Ensure value is treated as a string
                plain_text += f"{heading} {key.capitalize()}\n\n{formatted_value}\n\n"
        return plain_text

    def content_truncation(self, content, encoding_name="cl100k_base"):
        encoding = tiktoken.get_encoding(encoding_name=encoding_name)

        def truncate_string(s):
            tokens = encoding.encode(s)
            truncated_tokens = tokens[: self.max_category_tokens]
            return encoding.decode(truncated_tokens)

        return truncate_string(content)

    def generate_readme_with_uuid(self, save_path):
        """
        Generate a README file content with a random UUID and the current date to track it,
        and save it to the specified path with the unique_id and current_date as the filename.
        :param save_path: String representing the directory where the README should be saved.
        """
        unique_id = uuid.uuid4()
        current_date = datetime.now().strftime("%Y-%m-%d")
        readme_filename = f"README_{unique_id.hex[:6]}_{current_date}.md"
        full_save_path = os.path.join(save_path, readme_filename)

        readme_content = "## Requirements \n{requirements} \n## Deployment \n{deployment} \n## Main readme \n{readme} \n## License \n{license}"

        readme_content = readme_content.format(
            requirements=self.dict_to_markdown_text(self.requirements_text),
            deployment=self.dict_to_markdown_text(self.deployment_text),
            readme=self.dict_to_markdown_text(self.readme_text),
            license=self.dict_to_markdown_text(self.license_text),
        )
        with open(full_save_path, "w") as readme_file:
            readme_file.write(readme_content)
        return readme_content

    async def chain_invoker(
        self,
        input_variables: list,
        selected_prompt: str,
        msg_values: list,
        system_prompt: str,
        base_model=None,
    ):
        cmc = ChatMessageChain(
            input_variables=input_variables,
            human_prompt=selected_prompt,
            system_prompt=system_prompt,
            llm_selection=self.llm_selection,
            msg_values=msg_values,
            base_model=base_model,
        )
        cmc.setup_chain()
        response = await cmc.run_chain_json_retry()

        if base_model or isinstance(response, str):
            return response
        return response.content

    async def complete_information(
        self,
        file_info,
        prompt: str,
        expert_mode: str,
        extra_variables: Optional[list] = None,
        extra_msg_values: Optional[list] = None,
        base_model=None,
    ):
        text_gen = await self.chain_invoker(
            input_variables=["file_info"]
            + (extra_variables if extra_variables else []),
            selected_prompt=prompt,
            msg_values=[file_info] + (extra_msg_values if extra_msg_values else []),
            system_prompt=self.SYSTEM_MESSAGE_INSPECTOR.format(
                type_of_file=expert_mode
            ),
            base_model=base_model,
        )
        return text_gen

    def _gather_file_paths(self, directory_path):
        """
        Traverse the directory to collect file paths.
        :param directory_path: Path to the directory to traverse.
        :return: A list of file paths found within the directory.
        """
        file_paths = []
        for root, _, files in os.walk(directory_path):
            for file in files:
                file_path = os.path.join(root, file)
                file_paths.append(file_path)
        return file_paths

    async def process_dict_of_files(self, file_dict: dict, prompt: str):
        """
        Processes a dictionary where each key is a file category and the value is a list of file paths.

        Args:
        file_dict (dict): A dictionary where the keys are categories and the values are lists of file paths.

        Returns:
        None: Outputs are printed.
        """
        truncation: bool = False
        text_gen_dict = {}
        for category, file_paths in file_dict.items():
            self._logger.info(f"Category: {category}")
            if len(file_paths) >= self.max_category_files:
                file_paths = file_paths[: self.max_category_files]
                truncation = True

            for file_path in file_paths:
                self._logger.info(f"File Path: {file_path}")
                with open(file_path, "r", encoding="utf-8") as file:
                    content = file.read()
                    if truncation:
                        content = self.content_truncation(content=content)
                    text_gen = await self.complete_information(
                        file_info=content,
                        prompt=prompt,
                        expert_mode=f"files that come from {category}",
                    )

                    if category not in text_gen_dict:
                        text_gen_dict[
                            category
                        ] = []  # Ensure the entry for this category is a list
                    text_gen_dict[category].append(
                        {os.path.basename(file_path).lower(): text_gen}
                    )

                    self._logger.info(
                        f"Information obtained succesfully for {file_path} of category {category}"
                    )

        return text_gen_dict

    def detect_requirements_files(self):
        """
        Detects requirement files in the project and categorizes them by their dependency manager.
        :return: A dictionary where keys are types of dependency managers and values are lists of file paths.
        """
        requirement_files = {
            "requirements": [],  # For requirements.txt
            "pipenv": [],  # For Pipfile
            "poetry": [],  # For pyproject.toml managed by poetry
            "conda": [],  # For conda environment files, e.g., environment.yml
        }

        # Map file identifiers to the correct category in requirement_files
        file_to_manager = {
            "requirements.txt": "requirements",
            "Pipfile": "pipenv",
            "pyproject.toml": "poetry",  # Assuming poetry uses pyproject.toml
            "environment.yml": "conda",  # Assuming conda uses environment.yml
        }

        for file_path in self.file_paths:
            file_name = os.path.basename(
                file_path
            ).lower()  # Get the basename of the file and make it case-insensitive

            for identifier, manager in file_to_manager.items():
                if file_name == identifier.lower():  # Match files case-insensitively
                    requirement_files[manager].append(file_path)
                    break  # Stop checking once the file is identified and added

        # Filter out empty entries if there are no files of that type
        self.requirements = {
            manager: files for manager, files in requirement_files.items() if files
        }

        return self.requirements

    def detect_deployment_files(self):
        """
        Detects deployment-related files in the project and categorizes them by their deployment technology.
        :return: A dictionary where keys are types of deployment technologies and values are lists of file paths.
        """
        self.deployments = {
            "docker": [],  # For Dockerfiles and docker-compose files
            "kubernetes": [],  # For Kubernetes config files
            "azure_pipelines": [],  # For Azure Pipelines CICD
        }

        # Map file identifiers to the correct category in self.deployments
        # TODO: Access to setup.py for Docker
        file_to_manager = {
            "Dockerfile": "docker",
            "docker-compose.yml": "docker",
            "Deployment.yaml": "kubernetes",
            "Service.yaml": "kubernetes",
            "Ingress.yaml": "kubernetes",
            # TODO: Implement something to analyze PIPELINES
            # "azure-pipelines.yml": "azure_pipelines",
        }

        for file_path in self.file_paths:
            file_name = os.path.basename(
                file_path
            ).lower()  # Get the basename of the file and make it case-insensitive

            # Check for specific docker files
            for identifier, manager in file_to_manager.items():
                if file_name == identifier.lower():
                    self.deployments[manager].append(file_path)

        # Filter out empty entries if there are no files of that type
        self.deployments = {
            manager: files for manager, files in self.deployments.items() if files
        }

        return self.deployments

    def detect_license_file(self):
        """
        Detects the license file in the project based on common naming conventions.
        :return: Dict with Path to the license file if found, otherwise EmptyDict.
        """

        self.license_file = {"project_license": []}
        license_patterns = ["license", "license.md", "license.txt", "copying"]
        for file_path in self.file_paths:
            file_name = os.path.basename(
                file_path
            ).lower()  # Extract filename and convert to lowercase
            if any(file_name.startswith(pattern) for pattern in license_patterns):
                self.license_file["project_license"].append(file_path)
                return self.license_file

        return self.license_file

    def detect_readme_file(self):
        """
        Detects the README.md file in the main project folder.
        :return: Dict with Path to the README.md file if found, otherwise EmptyDict.
        """
        self.readme_file = {"main_readme": []}
        for file_path in self.file_paths:
            file_name = os.path.basename(
                file_path
            ).lower()  # Extract filename and convert to lowercase
            if file_name == "readme.md":
                self.readme_file["main_readme"].append(file_path)
                return self.readme_file
        return self.readme_file

    def detect_other_markdown_files(self):
        """
        Detects other markdown files (*.md) in the project, allowing for a recursive search.
        :return: A list of paths to detected markdown files other than README.md.
        """
        self.readme_files = {"other_readme_files": []}
        for file_path in self.file_paths:
            file_name = os.path.basename(
                file_path
            ).lower()  # Extract filename and convert to lowercase
            if file_name.endswith(".md") and file_name != "readme.md":
                self.readme_files["other_readme_files"].append(file_path)
        return self.readme_files

    def detect_testing_files(self):
        """
        Detects Python test files in the project based on common naming conventions, and groups them by folder.
        :return: A dictionary where keys are folder names and values are counts of testing files within those folders.
        """
        test_file_counts = {}
        for file_path in self.file_paths:
            file_name = os.path.basename(file_path)  # Extract just the file name
            # Check if the file name follows common Python test file patterns
            if file_name.startswith("test_") or file_name.endswith("_test.py"):
                folder_name = os.path.dirname(file_path)  # Extract the folder path
                if folder_name in test_file_counts:
                    test_file_counts[folder_name] += 1
                else:
                    test_file_counts[folder_name] = 1

        return test_file_counts

    async def detection_phase(self):
        requirement_files = await asyncio.to_thread(self.detect_requirements_files)
        self._logger.info(f"Requirement Files: {requirement_files}")

        deployment_files = await asyncio.to_thread(self.detect_deployment_files)
        self._logger.info(f"Deployment Files: {deployment_files}")

        license_files = await asyncio.to_thread(self.detect_license_file)
        self._logger.info(f"License Files: {license_files}")

        readme_file = await asyncio.to_thread(self.detect_readme_file)
        self._logger.info(f"Main readme file: {readme_file}")

    async def workflow_generation_phase(self):
        # Launch asynchronous tasks to process each category of files simultaneously.
        self.readme_text = ""
        tasks = [
            self.process_dict_of_files(self.requirements, self.REQUIREMENT_PROMPT),
            self.process_dict_of_files(self.deployments, self.DEPLOYMENT_PROMPT),
            self.process_dict_of_files(self.license_file, self.LICENSE_PROMPT),
            # self.process_dict_of_files(self.readme_file, self.README_PROMPT) if self.readme_file else asyncio.sleep(0)
        ]
        results = await asyncio.gather(*tasks)

        # Assign results to instance variables
        self.requirements_text, self.deployment_text, self.license_text = results[:3]
        self.readme_text = results[3] if len(results) > 3 else ""

    async def run(self):
        # testing_files = self.detect_testing_files()
        # self._logger.info(f"Testing Files: {testing_files}")

        await self.detection_phase()
        await self.workflow_generation_phase()

        # self.generate_readme_with_uuid(save_path="tests")

        return {
            "requirements": self.dict_to_markdown_text(self.requirements_text),
            "deployment": self.dict_to_markdown_text(self.deployment_text),
            "readme": self.dict_to_markdown_text(self.readme_text),
            "license": self.dict_to_markdown_text(self.license_text),
        }
