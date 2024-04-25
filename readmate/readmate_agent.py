import os
import sys
import json
import shutil
import asyncio


from readmate.toolkit import (
    top_level_analysis,
    search_engines,
    low_level_analysis,
)

from readmate.utils.logger import set_logger
from readmate.utils.utils_tools import load_json_from_path

from readmate.generators.markdown import ReadmeGenerator

_logger = set_logger()

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


# TODO: V2: CALLBACK Track the states of the process and stream to frontend


def find_main_folder(extraction_path):
    """
    Find the main folder in the given extraction path. Assumes the main folder is the one
    directly under the specified extraction path, especially useful for zipped projects
    where the structure might duplicate folder names.

    Parameters:
    - extraction_path: The path where the zip file was extracted.

    Returns:
    - The path to the main folder, if found; otherwise, returns None.
    """

    # List all items directly under the extraction path
    items = os.listdir(extraction_path)

    # Filter directories
    directories = [
        item for item in items if os.path.isdir(os.path.join(extraction_path, item))
    ]

    # Extract last part of the extraction path
    extraction_path_last_part = os.path.basename(os.path.normpath(extraction_path))

    if len(directories) == 1:
        if directories[0] == extraction_path_last_part:
            _logger.info(
                "The input folder {} is not the main directory. Main directory set to: {}".format(
                    extraction_path, os.path.join(extraction_path, directories[0])
                )
            )
            return os.path.join(extraction_path, directories[0])

    elif len(directories) > 1:
        _logger.info("The input folder is the main directory")
        return extraction_path
    else:
        _logger.info(
            "The input folder could not be asserted as the main directory. Continuing with: {}".format(
                extraction_path
            )
        )
    return extraction_path


class ReadMateAgent:
    """_summary_"""

    # Class-level variables for file names
    INFO_MODULES_JSON = "info_modules.json"
    INFO_FILES_JSON = "info_files.json"
    INFO_FILES_EXTENDED_JSON = "info_files_extended.json"
    INFO_MODULES_EXTENDED_JSON = "info_modules_extended.json"
    README = "readme.md"

    def __init__(self, input_path: str, workspace_path: str, output_path: str):
        """_summary_

        Args:
            input_path (str): _description_
            workspace_path (str): _description_
            output_path (str): _description_
        """
        self.workspace_path = workspace_path
        self.output_path = output_path
        self.input_path = find_main_folder(input_path)

        self.project_name = os.path.basename(os.path.normpath(self.input_path))

        # Construct full paths with class-level filenames
        self.info_modules = os.path.join(self.workspace_path, self.INFO_MODULES_JSON)
        self.info_files = os.path.join(self.workspace_path, self.INFO_FILES_JSON)
        self.info_files_extended = os.path.join(
            self.workspace_path, self.INFO_FILES_EXTENDED_JSON
        )
        self.info_modules_extended = os.path.join(
            self.workspace_path, self.INFO_MODULES_EXTENDED_JSON
        )

        self.readme_md = os.path.join(self.output_path, self.README)

    # TESTING FUNCTION TO AVOID RUNNING THE FULL LOOP
    def copy_info_files_to_new_workspace(self, test_folder: str):
        """
        Copies the info files from the main workspace folder to the new workspace folder.
        """

        # List of files to be copied
        info_files_to_copy = [
            self.INFO_MODULES_JSON,
            self.INFO_FILES_JSON,
            self.INFO_FILES_EXTENDED_JSON,
            self.INFO_MODULES_EXTENDED_JSON,
        ]

        # Copy each file
        for info_file in info_files_to_copy:
            src_file_path = os.path.join(test_folder, info_file)
            dst_file_path = os.path.join(self.workspace_path, info_file)
            if os.path.exists(src_file_path):
                shutil.copy(src_file_path, dst_file_path)
                _logger.info(f"Copied {info_file} to {self.workspace_path}")
            else:
                _logger.warning(
                    f"File {info_file} does not exist in the main workspace folder."
                )

    def _write_json_doc(self, output_path: str, data: dict):
        with open(output_path, "w") as json_file:
            json.dump(data, json_file, indent=4, sort_keys=True)
        _logger.info("Modules files & folders processed into: {}".format(output_path))

    def _write_md_doc(self, output_path: str, data: str):
        with open(output_path, "w", encoding="utf-8") as file:
            file.write(data)

        _logger.info("Readme saved to {}".format(output_path))

    def top_level_analysis_modules(self):
        _logger.info("Top-Level analysis for modules started")
        result_recursive_folder_search = search_engines.recursive_directory_search(
            directory=self.input_path
        )
        info_modules = asyncio.run(
            top_level_analysis.generate_module_descriptions_and_ratings(
                result_recursive_folder_search
            )
        )
        self._write_json_doc(output_path=self.info_modules, data=info_modules)

    def main_folder_file_analysis(self):
        _logger.info("Main folder search for files started")
        result_outside_folder_search = search_engines.list_files_outside_folders(
            directory=self.input_path
        )

        info_off_modules = asyncio.run(
            top_level_analysis.generate_file_descriptions_and_ratings(
                result_outside_folder_search
            )
        )
        self._write_json_doc(output_path=self.info_files, data=info_off_modules)

    def low_level_analysis_files(self):
        _logger.info("Low-level analysis for files started")

        info_off_modules = asyncio.run(
            low_level_analysis.analyze_internal_files(self.info_files, self.input_path)
        )
        self._write_json_doc(
            output_path=self.info_files_extended, data=info_off_modules
        )

    def low_level_analysis_modules(self):
        _logger.info("Low-level analysis for modules started")
        info_modules_dict = load_json_from_path(file_path=self.info_modules)

        final_json_dict = asyncio.run(
            low_level_analysis.recursive_json_search_agent(
                info_modules_dict, self.input_path
            )
        )

        self._write_json_doc(
            output_path=self.info_modules_extended, data=final_json_dict
        )

    def save_readme_gen(self, generated_readme):
        self._write_md_doc(
            os.path.join(self.workspace_path, "readme.md"), generated_readme
        )

    def readme_generator(self):
        _logger.info("Generating readme...")
        readme_generator = ReadmeGenerator(
            project_name=self.project_name,
            introduction="Filled with the project description.",
            off_module_path=self.info_files_extended,
            in_module_path=self.info_modules_extended,
            input_project_path=self.input_path,
        )

        # Generate the README file
        generated_readme = asyncio.run(readme_generator.gen_readme())
        # Save the README file
        self.save_readme_gen(generated_readme)

    def copy_extended_info_to_logs(self):
        """
        Copies the extended info JSON files to the logs directory.
        """
        try:
            self.files_logs = os.path.join(
                self.output_path, "logs", self.INFO_FILES_EXTENDED_JSON
            )
            self.modules_logs = os.path.join(
                self.output_path, "logs", self.INFO_MODULES_EXTENDED_JSON
            )

            # Copy info_files_extended to files_logs
            shutil.copy(self.info_files_extended, self.files_logs)
            _logger.info(f"Copied {self.INFO_FILES_EXTENDED_JSON} to logs directory")

            # Copy info_modules_extended to modules_logs
            shutil.copy(self.info_modules_extended, self.modules_logs)
            _logger.info(f"Copied {self.INFO_MODULES_EXTENDED_JSON} to logs directory")

        except Exception as e:
            _logger.error(
                f"An error occurred while copying extended info files to logs: {e}"
            )

    def run_readme_test(self, test_folder: str):
        self.copy_info_files_to_new_workspace(test_folder=test_folder)
        self.readme_generator()

    def run(self):
        self.main_folder_file_analysis()
        self.top_level_analysis_modules()
        self.low_level_analysis_files()
        self.low_level_analysis_modules()

        self.copy_extended_info_to_logs()
        self.readme_generator()

        return self.readme_md


# TODO: Modular token limit by func and class
# TODO V2: Detect Runnable Code with Flag (viability prompt) >> INTO LLM >> EXAMPLE AGENT
