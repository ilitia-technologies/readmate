import asyncio
import sys
from typing import Dict, List, Union, Any
from readmate.prompts.input_prompt import (
    MODULE_WITH_SUBMODULES,
    MODULE_WITHOUT_SUBMODULES,
    OUT_FILES,
    SYSTEM_MESSAGE_AGENT,
)

from readmate.utils.logger import set_logger
from readmate.utils.utils_tools import model_initialization, json_decoder
from readmate.utils.basemodel_modules import (
    ModuleAnalysis,
    FileAnalysis,
)

from readmate.chains.chat_message_chain import ChatMessageChain

_logger = set_logger()

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


async def process_module(
    folder_info: Dict[str, Any],
    input_vars: list,
    msg_vals: list,
    h_prompt: str,
    llm_selection,
) -> None:
    # CMC new instance to avoid case of shared mutable object in async enviroment
    cmc = ChatMessageChain(
        input_variables=input_vars,
        base_model=ModuleAnalysis,
        human_prompt=h_prompt,
        system_prompt=SYSTEM_MESSAGE_AGENT,
        llm_selection=llm_selection,
        msg_values=msg_vals,
    )

    cmc.setup_chain()

    response = await cmc.run_chain_json_retry()

    _logger.info(f"Off-module file processed: {folder_info['current_folder']}")

    return response


async def generate_module_descriptions_and_ratings(
    directory_info: str,
) -> Dict[str, Union[Dict, int, str]]:
    """
    INPUT: Dictionary
    INPUT TYPE: dict
    Generate descriptions of what each module does
    and a rating of its usefulness for a README file, but only for directories without subdirectories.
    """
    # Initialize the language model
    directory_info = json_decoder(directory_info=directory_info)
    llm_selection = model_initialization()

    async def process_subfolder(
        subfolder_info: Dict[str, Union[Dict, int, List[str]]], path: List[str]
    ):
        tasks = []
        # Run a prompt for the main folder before processing subfolders
        subfolder_names = list(subfolder_info["subfolders"].keys())

        input_variables = [
            "current_module",
            "num_files",
            "extensions",
            "num_lines",
            "submodules",
        ]

        msg_values = [
            subfolder_info["current_folder"],
            subfolder_info["num_files"],
            subfolder_info["file_extensions"],
            subfolder_info["num_lines"],
            subfolder_names,
        ]

        task = asyncio.create_task(
            process_module(
                folder_info=subfolder_info,
                input_vars=input_variables,
                msg_vals=msg_values,
                h_prompt=MODULE_WITH_SUBMODULES,
                llm_selection=llm_selection,
            )
        )
        tasks.append(task)

        # Wait for the main folder task and update info
        main_folder_response = await tasks[0]
        subfolder_info.update(main_folder_response)

        for subfolder, details in subfolder_info.get("subfolders", {}).items():
            # Initialize prompt and response outside the if-else scope
            subfolder_names = list(details["subfolders"].keys())
            if subfolder_names:
                input_variables = [
                    "current_module",
                    "num_files",
                    "extensions",
                    "num_lines",
                    "submodules",
                ]
                human_prompt = MODULE_WITH_SUBMODULES
            else:
                input_variables = [
                    "current_module",
                    "num_files",
                    "extensions",
                    "num_lines",
                ]
                human_prompt = MODULE_WITHOUT_SUBMODULES

            msg_values = [
                details["current_folder"],
                details["num_files"],
                details["file_extensions"],
                details["num_lines"],
                subfolder_names if subfolder_names else [],
            ]

            # Ensure prompt is not empty before invoking the model

            tasks.append(
                asyncio.create_task(
                    process_module(
                        folder_info=details,
                        input_vars=input_variables,
                        msg_vals=msg_values,
                        h_prompt=human_prompt,
                        llm_selection=llm_selection,
                    )
                )
            )
        responses = await asyncio.gather(
            *tasks[1:]
        )  # Skip the first task which is already awaited

        for task, subfolder in zip(responses, subfolder_info["subfolders"]):
            subfolder_info["subfolders"][subfolder].update(task)
        # Recurse into subfolders if they exist
        if subfolder_names:
            await process_subfolder(details, path + [subfolder])

    await process_subfolder(directory_info, [])
    return directory_info


async def generate_file_descriptions_and_ratings(
    directory_info: dict,
) -> Dict[str, Union[Dict, int, str]]:
    llm_selection = model_initialization()

    output_dict = {}
    tasks = []

    for non_module_file in directory_info["files"]:
        task = asyncio.create_task(
            process_file(non_module_file, output_dict, llm_selection)
        )
        tasks.append(task)

    # Wait for all tasks to complete
    await asyncio.gather(*tasks)

    return output_dict


async def process_file(
    non_module_file: Dict[str, Any], output_dict: Dict[str, Any], llm_selection
) -> None:
    # CMC new instance to avoid case of shared mutable object in async enviroment
    cmc = ChatMessageChain(
        input_variables=[
            "file_extension",
            "filename",
            "num_lines",
        ],
        base_model=FileAnalysis,
        human_prompt=OUT_FILES,
        system_prompt=SYSTEM_MESSAGE_AGENT,
        llm_selection=llm_selection,
        msg_values=[
            non_module_file["file_extension"],
            non_module_file["filename"],
            non_module_file["num_lines"],
        ],
    )
    cmc.setup_chain()

    response = await cmc.run_chain_json_retry()

    # Since dictionaries are mutable, this modification will reflect in the output_dict in the caller function
    output_dict[non_module_file["filename"]] = non_module_file
    output_dict[non_module_file["filename"]].update(response)

    _logger.info(f"Off-module file processed: {non_module_file['filename']}")
