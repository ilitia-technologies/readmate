import sys
import asyncio
import toml


from typing import Optional

from readmate.utils.logger import set_logger
from readmate.utils.utils_tools import (
    model_initialization,
    filter_keys_recursively,
    load_json_from_path,
)
from readmate.utils.basemodel_modules import BadgesGeneration

from readmate.prompts.md import (
    SYSTEM_MESSAGE_AGENT_V2,
    INTRODUCTION_PROMPT,
    PROJECT_TREE_PROMPT,
    FEATURES_PROMPT,
    BADGES_PROMPT_V2,
    SYSTEM_MESSAGE_AGENT_CUSTOM,
    MAIN_MODULES_PROMPT,
    RECOMMENDED_MODULES_PROMPT,
    INSTALLATION_PROMPT,
    CONFIGURATION_PROMPT,
)
from readmate.chains.chat_message_chain import ChatMessageChain
from readmate.modules.project_inspector import ProjectInspector


if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


_logger = set_logger()
log_msg = "Generating {} - {}"


# TODO: V2: Count lines or tokens in total by language/tech


# Function to dynamically convert string names to variable values
def convert_to_variable(name):
    # First try to get the variable from globals
    if name in globals():
        return globals()[name]
    # Then try to get the variable from locals
    elif name in locals():
        return locals()[name]
    # Default to a "not found" message if the variable doesn't exist in both scopes
    else:
        return f"{name} not found"


def json_to_minimal_text(data, indent=0):
    text = ""
    indent_str = " " * indent

    if isinstance(data, dict):
        for key, value in data.items():
            text += f"{indent_str}{key}: "  # No newline after key
            if isinstance(value, (dict, list)):
                text += "\n" + json_to_minimal_text(value, indent + 2)
            else:
                text += f"{value}\n"
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                text += json_to_minimal_text(item, indent)
            else:
                text += f"{indent_str}{item}\n"
    else:
        text += f"{indent_str}{data}\n"

    return text.strip()


class BaseReadmeGenerator:
    def __init__(
        self,
        project_name: str,
        introduction: str,
        off_module_path,
        in_module_path,
        input_project_path,
    ):
        """
        Initializes the BaseReadmeGenerator with project details and analysis.

        Args:
            project_name (str): The name of the project.
            introduction (str): Introduction or description of the project.
            off_module_path: Path to the JSON file for off-module analysis.
            in_module_path: Path to the JSON file for in-module analysis.
            input_project_path: Path to the input project for which the README is generated.
        """
        # self.project_name = project_name.capitalize()
        self.project_name = "Project Readme"
        self.introduction = introduction
        self.off_module_path = off_module_path
        self.in_module_path = in_module_path
        self.input_project_path = input_project_path

        # Initialize placeholders for sections

        config = toml.load("readmate/configs/readme_structure.toml")
        self.json_structure_markdown = "readmate/configs/readme_section_completion.json"
        self.sections = config["sections"]
        self.section_emojis = config["section_emojis"]
        self.license_badges = config["license_badges"]
        self.features_table = "| Feature | Description |\n|---------|-------------|\n"
        self.badges = []
        self.crucial_keys = ["CodeExtractions", "Functions", "Classes"]

        self.content_md = None
        self.content_md_ai_extended = None

        self._load_json_files()

        self.llm_selection = model_initialization()

    def _load_json_files(self):
        """
        Loads JSON configuration files from specified paths and processes section details.
        This method populates off-module and in-module data and updates json_structure with dynamic content based on the current context.
        """

        self.off_module = load_json_from_path(file_path=self.off_module_path)

        self.in_module = load_json_from_path(file_path=self.in_module_path)

        self.json_structure = load_json_from_path(
            file_path=self.json_structure_markdown
        )

        # Iterate over the selected_sections to replace strings with actual variable values
        for _, details in self.json_structure.items():
            for key in ["prompt", "log_msg"]:
                if key in details:
                    # Replace the string name with its corresponding variable value
                    details[key] = convert_to_variable(details[key])

    async def chain_invoker(
        self,
        input_variables: list,
        selected_prompt: str,
        msg_values: list,
        system_prompt: str,
        base_model=None,
    ):
        """
        Invokes a chain of operations to generate content based on dynamic prompts and input variables.

        Args:
            input_variables (list): List of variables to pass to the chain.
            selected_prompt (str): Human-readable prompt for generating messages.
            msg_values (list): Values corresponding to the input variables.
            system_prompt (str): System-specific prompt for processing.
            base_model (optional): The base model for additional processing, can be None.

        Returns:
            str or dict: The processed response from the message chain, which could be a string or dictionary depending on the base model.
        """
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


class ReadmeGenerator(BaseReadmeGenerator):
    def generate_table_of_contents(self):
        # Override to exclude badges and table_of_contents
        toc = f"## {self.section_emojis['table_of_contents']}Table of Contents\n\n"
        excluded_sections = ["badges", "table_of_contents"]
        for section_name in self.sections.keys():
            if section_name not in excluded_sections:
                readable_name = section_name.replace("_", " ").capitalize()
                # BUG: Fix anchor links not working
                anchor_link = section_name.lower().replace("_", "-")
                toc += f"- [{readable_name}](#{anchor_link})\n"
        self.sections["table_of_contents"] = toc

    def fill_section(self, section_name, content):
        emoji = self.section_emojis.get(section_name, "")
        # Find the position right after the markdown header (if any)
        header_end_pos = content.find("##")

        if header_end_pos != -1 and content.startswith("##"):
            # Insert the emoji right after the header and before the actual content
            content = (
                content[: header_end_pos + 2]
                + " "
                + emoji
                + content[header_end_pos + 2 :]
            )
        else:
            # If no header is found, prepend the emoji to the content
            content = emoji + " " + content

        if section_name in self.sections:
            self.sections[section_name] = content
        else:
            raise ValueError("Invalid section name provided")

    async def completion_llm_section(
        self,
        description_keys_file: list,
        description_keys_module: list,
        log_generation: str,
        prompt: str,
        extra_variables: Optional[list] = None,
        extra_msg_values: Optional[list] = None,
        base_model=None,
    ):
        file_descriptions = filter_keys_recursively(
            self.off_module, description_keys_file, crucial_keys=self.crucial_keys
        )
        module_descriptions = filter_keys_recursively(
            self.in_module, description_keys_module, crucial_keys=self.crucial_keys
        )

        def remove_empty_values(data):
            """
            Recursively remove key-value pairs from a dictionary where the value is empty.
            An empty value is defined as None, an empty string, list, or dictionary.
            """
            if isinstance(data, dict):
                return {
                    key: remove_empty_values(value)
                    for key, value in data.items()
                    if value or isinstance(value, (int, float))
                }
            elif isinstance(data, list):
                return [
                    remove_empty_values(item)
                    for item in data
                    if item or isinstance(item, (int, float))
                ]
            else:
                return data

        file_descriptions = remove_empty_values(data=file_descriptions)
        module_descriptions = remove_empty_values(data=module_descriptions)

        _logger.info(log_generation)
        text_gen = await self.chain_invoker(
            input_variables=["file_descriptions", "module_descriptions"]
            + (extra_variables if extra_variables else []),
            selected_prompt=prompt,
            msg_values=[file_descriptions, module_descriptions]
            + (extra_msg_values if extra_msg_values else []),
            system_prompt=SYSTEM_MESSAGE_AGENT_V2,
            base_model=base_model,
        )
        return text_gen

    def join_readme(self):
        # Ensure that the table of contents is up to date
        self.generate_table_of_contents()
        # Compile all sections into a single string

        readme_structure = (
            f"# :newspaper: {self.project_name}\n\n{self.introduction}\n\n"
        )
        for section_content in self.sections.values():
            readme_structure += f"{section_content}\n\n"
        return readme_structure

    async def completion_llm_badges(self, content):
        self.badges = await self.chain_invoker(
            input_variables=["file_info"],
            selected_prompt=BADGES_PROMPT_V2,
            msg_values=[content],
            system_prompt=SYSTEM_MESSAGE_AGENT_V2,
            base_model=BadgesGeneration,
        )

        badges_addition = ""
        badges_addition += (
            "\n".join(
                badge if badge.endswith(".svg)") else badge.replace(")", ".svg)")
                for badge in self.badges["Badges"]
            )
            + "\n\n"
        )

        self.fill_section("badges", badges_addition)

    async def completion_llm_overview(self):
        keys_shared = ["Description"]
        self.introduction = await self.completion_llm_section(
            description_keys_file=keys_shared,
            description_keys_module=keys_shared,
            log_generation="Generating I - Project Overview",
            prompt=INTRODUCTION_PROMPT,
        )

    async def completion_project_tree(self):
        keys_shared = ["current_folder"]
        self.project_tree = await self.completion_llm_section(
            description_keys_file=keys_shared,
            description_keys_module=keys_shared,
            log_generation="Generating III - Project Tree",
            prompt=PROJECT_TREE_PROMPT,
        )

        self.fill_section("project_tree", f"## Project Tree\n\n {self.project_tree}")

    async def completion_llm_features(self):
        keys_shared = ["Description"]
        self.features_table = await self.completion_llm_section(
            description_keys_file=keys_shared,
            description_keys_module=keys_shared,
            log_generation="Generating II - Features Table",
            extra_variables=["project_overview"],
            extra_msg_values=[self.introduction],
            prompt=FEATURES_PROMPT,
        )

        self.fill_section("features", f"## Features\n\n {self.features_table}")

    async def complete_llm_section(
        self, section: str, section_params: dict, iter_n: int
    ):
        section_params["log_msg"] = section_params["log_msg"].format(iter_n, section)
        self.llm_text = await self.completion_llm_section(
            description_keys_file=section_params["desc_keys_files"],
            description_keys_module=section_params["desc_keys_modules"],
            log_generation=section_params["log_msg"],
            extra_variables=section_params.get("extra_variables"),
            extra_msg_values=section_params.get("extra_msg"),
            prompt=section_params["prompt"],
        )

        self.fill_section(
            section,
            f"## {section.capitalize()}\n\n> {self.llm_text}",
        )

    def complete_generic_section(self, section: str, llm_text: Optional[str] = None):
        GENERIC_MSG = "Details for this sections are WIP (work in progress)"
        llm_text = GENERIC_MSG if llm_text is None else llm_text

        self.fill_section(
            section,
            f"## {section.capitalize()}\n\n> {llm_text}",
        )

    async def generate_llm_sections(self):
        await self.completion_llm_overview()
        await self.completion_project_tree()
        await self.completion_llm_features()

    async def complete_template_sections(self, template_sections):
        tasks = [
            self.complete_llm_section(ss, details, iteration_count)
            for iteration_count, (ss, details) in enumerate(
                self.json_structure.items(), 1
            )
        ]
        await asyncio.gather(*tasks)

        for ss in template_sections:
            self.complete_generic_section(ss)

    async def inspect_and_complete_project(self):
        # INSPECTOR
        inspector = ProjectInspector(directory_path=self.input_project_path)
        extended_sections = await inspector.run()
        LLM_EXCEPTION_TEXT = "No details were found relating {}"
        sections = ["requirements", "deployment", "license"]

        for section in sections:
            text = (
                extended_sections[section]
                if extended_sections[section]
                else LLM_EXCEPTION_TEXT.format(section)
            )
            self.complete_generic_section(section=section, llm_text=text)

        # BUG: Badges should be seen in lines, not vertically
        await self.completion_llm_badges(content=extended_sections["requirements"])

    async def gen_readme(self):
        # Adding dynamic code percentage badges

        template_sections = {
            "troubleshooting_faq": "",
            "maintainers": "",
            "contributions": "",
            "examples": "",
            "testing": "",
        }
        # Generate dynamic sections based on LLM analysis
        await self.generate_llm_sections()

        # Complete template sections based on JSON structure
        await self.complete_template_sections(template_sections)

        # Inspect project and complete sections like requirements, deployment, license
        await self.inspect_and_complete_project()

        self.content_md = self.join_readme()

        return self.content_md
