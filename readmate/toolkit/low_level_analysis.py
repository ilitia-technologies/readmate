import os
import sys
import asyncio

from typing import Dict, Union

from readmate.utils.logger import set_logger
from readmate.utils.basemodel_modules import (
    FileAnalyzer,
    PythonAnalysis,
    PythonAnalysisTopLevelCode,
)
from readmate.prompts.module_readers import (
    SYSTEM_MESSAGE_FILE_AGENT,
    FILE_ANALYZER,
)

from readmate.prompts.file_readers import (
    FILE_ANALYZER as FILE_ANALYZER_FILE_LEVEL,
    README_SECTIONS,
    SYSTEM_MESSAGE_FILE_AGENT as SYSTEM_MESSAGE_FILE_AGENT_FILE_LEVEL,
)

from readmate.prompts.python_module import (
    PY_FUNCTIONS,
    PY_CLASSES,
    PY_TOP_LEVEL_CODE,
    SYSTEM_PYTHON_MESSAGE,
)

from readmate.utils.utils_tools import (
    model_initialization,
    extension_support_analysis,
    read_text_file,
    extension_support_analysis_for_main_folder,
    load_json_from_path,
)


from readmate.chains.chat_message_chain import ChatMessageChain


_logger = set_logger()

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# TODO: This "agent" should be a class
# TODO: Obtain lines of code and more data from the files


def analyze_reading_viability(
    folder_dict: dict, supported_files: list, unsupported_files: list
) -> (bool, str):
    STATUS_FOLDER = ""
    INIT_MODULE = False
    read_flag = False

    _logger.info("Analyzing which files are supported: {}".format(folder_dict["files"]))

    if folder_dict.get("main_project_folder") is True:
        STATUS_FOLDER = (
            "Main folder is not analyzed with the Module Agent, moving on..."
        )
        read_flag = False
        _logger.info(STATUS_FOLDER)
        return read_flag, STATUS_FOLDER, INIT_MODULE

    if "__init__.py" in supported_files:
        INIT_MODULE = True
        _logger.info("We have detected an init_file, Assuming this is a module")

    if len(supported_files) != 0 and len(unsupported_files) == 0:
        STATUS_FOLDER = "All files are supported"
        read_flag = True
    elif len(supported_files) != 0 and len(unsupported_files) != 0:
        STATUS_FOLDER = "Some files are supported: {}".format(supported_files)
        read_flag = True
    elif len(supported_files) == 0 and len(unsupported_files) != 0:
        read_flag = False
        STATUS_FOLDER = "No files are supported"

    _logger.info(STATUS_FOLDER)
    return read_flag, STATUS_FOLDER, INIT_MODULE


# Recursive search - Agent
async def recursive_json_search_agent(json_module_dict, workspace_path):
    """
    Recursive function to get all the information of the subfolders
    """
    _logger.info(f"Current Folder: {json_module_dict['current_folder']}")
    await analyze_utility(json_module_dict, workspace_path)

    if "subfolders" in json_module_dict:
        tasks = [
            asyncio.create_task(
                recursive_json_search_agent(subfolder_dict, workspace_path)
            )
            for _, subfolder_dict in json_module_dict["subfolders"].items()
        ]
        await asyncio.gather(*tasks)
    # Return the modified json_module_dict after completing all recursive calls
    return json_module_dict


async def analyze_utility(folder_dict, workspace_path):
    """
    Tool 1: Analyze the utility of the files we see
    """

    read_flag = False

    if len(folder_dict["files"]) == 0:
        _logger.warning("Empty list of files, moving on...")
    else:
        # Invoke the chain here

        supported_files, unsupported_files, extension_support = (
            extension_support_analysis(folder_dict=folder_dict)
        )

        read_flag, _, _ = analyze_reading_viability(
            folder_dict, supported_files, unsupported_files
        )

        # read_flag: if True, folder should be read
        if read_flag:
            # NOTE: The chain present here was destroyed because of low usefulness. In the future we can use a Semantic/KMeans method to select the files

            folder_dict_copy = folder_dict.copy()
            keys_to_pop = [
                "total_classes_token_count",
                "total_funcs_token_count",
                "Description",
                "Rating",
            ]
            [folder_dict_copy.pop(key, None) for key in keys_to_pop]
            if not folder_dict_copy["subfolders"]:  # Check if the list is empty
                folder_dict_copy["subfolders"] = "No submodules under this folder"
            else:
                folder_dict_copy["subfolders"] = (
                    "There are submodules under this folder"
                )

            folder_dict["files"] = await read_viable_files(
                supported_files, extension_support, folder_dict_copy, workspace_path
            )
        else:
            return
        if unsupported_files and len(supported_files) == 0:
            _logger.warning(
                f"All files are unsupported file types, custom workflow for this folder: {folder_dict['current_folder']}"
            )


async def read_viable_files(
    file_selection: list,
    extension_support: dict,
    extra_info_folder: dict,
    workspace_path: str,
) -> Dict:
    output_dict = {}

    token_count = 200
    llm_selection = model_initialization()
    tasks = []
    for item_l in file_selection:
        # TODO: V2: (MMMAC): Move extension logic into General_File_Reader + Adapt the prompt to each file
        extension_current_file = os.path.splitext(item_l)[1].lstrip(".")
        extension_include = extension_support["extensions"][extension_current_file][
            "include"
        ]

        if extension_include:
            _logger.info(f"LLM READER - Processing the full file: {item_l}")
        else:
            _logger.info(
                f"LLM READER - Processing {token_count} tokens of the file: {item_l}"
            )

        analysis_of_file, python_flag = read_text_file(
            os.path.join(workspace_path, extra_info_folder["current_folder"], item_l)
        )

        if python_flag:
            task = asyncio.create_task(
                python_llm_ast_analyzer(analysis_of_file, llm_selection)
            )
            tasks.append((task, item_l, analysis_of_file["imports"]))

        else:
            cmc = ChatMessageChain(
                input_variables=[
                    "readme_section",
                    "non_module_file",
                    "file_info",
                ],
                base_model=FileAnalyzer,
                human_prompt=FILE_ANALYZER,
                system_prompt=SYSTEM_MESSAGE_FILE_AGENT,
                llm_selection=llm_selection,
                msg_values=[
                    README_SECTIONS,
                    extra_info_folder,
                    analysis_of_file,
                ],
            )

            cmc.setup_chain()
            task = asyncio.create_task(cmc.run_chain_json_retry())
            tasks.append((task, item_l, None))
            response = cmc.run_chain_json_retry()

    responses = await asyncio.gather(*[t[0] for t in tasks])

    for response, task_tuple in zip(responses, tasks):
        _, item_l, imports = (
            task_tuple  # Unpack each tuple to get the filename and imports
        )
        if imports:
            response["Imports"] = imports
        output_dict[item_l] = response
    return output_dict
    # TODO: (V2) Update descriptions and examples according to files while running or at the end


async def process_python_chain(cmc):
    cmc.setup_chain()

    response = await cmc.run_chain_json_retry()

    return response


# Define a function to check for empty dictionaries or non-empty lists in the provided dictionary
async def python_llm_ast_analyzer(file_info, llm_selection):
    tasks = []
    responses = {}
    for key, value in file_info.items():
        if key == "imports":
            continue
        # Check if the value is a dictionary/list and if it's not empty
        if (isinstance(value, dict) or isinstance(value, list)) and value:
            correlation = {
                "functions": {
                    "base_model": PythonAnalysis,
                    "human_prompt": PY_FUNCTIONS,
                },
                "classes": {"base_model": PythonAnalysis, "human_prompt": PY_CLASSES},
                "top_level_script": {
                    "base_model": PythonAnalysisTopLevelCode,
                    "human_prompt": PY_TOP_LEVEL_CODE,
                },
            }
            cmc = ChatMessageChain(
                input_variables=[
                    "ast_analysis",
                ],
                base_model=correlation[key]["base_model"],
                human_prompt=correlation[key]["human_prompt"],
                system_prompt=SYSTEM_PYTHON_MESSAGE,
                llm_selection=llm_selection,
                msg_values=[value],
            )

            tasks.append(asyncio.create_task(process_python_chain(cmc=cmc)))

    responses = await asyncio.gather(*tasks)

    if not responses:
        responses = [PythonAnalysis.default_dict()]
    return responses[0]


async def analyze_internal_files(
    directory_info: str, workspace_path: str
) -> Dict[str, Union[Dict, int, str]]:
    output_dict = {}
    llm_selection = model_initialization()

    directory_info = load_json_from_path(file_path=directory_info)

    supported_files, _, _ = extension_support_analysis_for_main_folder(
        folder_dict=directory_info
    )
    tasks = []  # Create a list to hold all the tasks
    for filename_key, non_module_file in directory_info.items():
        if filename_key in supported_files:
            file_info, file_ext_py = read_text_file(
                file_path=os.path.join(
                    workspace_path,
                    non_module_file["current_folder"],
                    non_module_file["filename"],
                )
            )

            if file_ext_py:
                task = asyncio.create_task(
                    python_llm_ast_analyzer(file_info, llm_selection)
                )
                tasks.append(
                    (task, non_module_file)
                )  # Append the task with its associated file info

                # response["top_level_script"] = file_info["top_level_script"]
            else:
                cmc = ChatMessageChain(
                    input_variables=[
                        "readme_section",
                        "non_module_file",
                        "file_info",
                    ],
                    base_model=FileAnalyzer,
                    human_prompt=FILE_ANALYZER_FILE_LEVEL,
                    system_prompt=SYSTEM_MESSAGE_FILE_AGENT_FILE_LEVEL.format(
                        non_module_file["Technologies"]
                    ),
                    llm_selection=llm_selection,
                    msg_values=[
                        README_SECTIONS,
                        non_module_file,
                        file_info,
                    ],
                )

                cmc.setup_chain()
                task = asyncio.create_task(cmc.run_chain_json_retry())
                tasks.append(
                    (task, non_module_file)
                )  # Append the task with its associated file info

    # Wait for all tasks to complete
    for task, non_module_file in tasks:
        response = await task
        if "Imports" in file_info:
            response["Imports"] = file_info["imports"]
        output_dict[non_module_file["filename"]] = non_module_file
        output_dict[non_module_file["filename"]].update(response)
        _logger.info("{} processed correctly".format(non_module_file["filename"]))

    return output_dict
