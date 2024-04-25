import os
import toml
import json
import tiktoken
from langchain_openai import AzureChatOpenAI, ChatOpenAI

from readmate.utils.logger import set_logger
from readmate.utils.general_utils import num_tokens_from_string
from readmate.modules.python_analyzer import PythonFileAnalyzer

from typing import Optional

_logger = set_logger()


def load_json_from_path(file_path, **kwargs):
    """
    Load JSON data from a specified file path.

    :param file_path: The path to the JSON file.
    :return: The loaded JSON data as a dictionary.
    """
    with open(file_path, "r", **kwargs) as file:
        data = json.load(file)

    _logger.info("JSON File loaded: {}".format(file_path))
    return data


def load_toml(file_path):
    """
    Load toml data from a specified file path.

    :param file_path: The path to the TOML file.
    :return: The loaded TOML data as a dictionary.
    """

    with open(file_path, "r") as toml_file:
        toml_data = toml.load(toml_file)
    return toml_data


# Define a condition for retry: return True (retry) if result is None
def is_none(result):
    return result is None


# Define a condition for retry: return True (retry) if result is None or an empty dictionary
def is_none_or_empty_dict(result):
    return result is None or (isinstance(result, dict) and not result)


def log_retry(retry_state):
    _logger.warning(
        "Retrying %s: attempt #%s ended with: %s",
        retry_state.fn,
        retry_state.attempt_number,
        retry_state.outcome,
    )


def model_initialization():
    if os.environ["SERVICE_ENTRYPOINT"] == "ChatOpenAI":
        llm_model = ChatOpenAI(
            model=os.environ["MODEL"],
            api_key=os.environ["OPENAI_API_KEY"],
            api_version=os.environ["OPENAI_API_VERSION"],
            temperature=float(os.environ["OPENAI_MODEL_TEMPERATURE"]),
        )
    else:
        llm_model = AzureChatOpenAI(
            model=os.environ["MODEL"],
            api_key=os.environ["OPENAI_API_KEY"],
            azure_endpoint=os.environ["AZURE_ENDPOINT"],
            api_version=os.environ["OPENAI_API_VERSION"],
            temperature=float(os.environ["OPENAI_MODEL_TEMPERATURE"]),
        )

    _logger.info(f"MODEL AT USE: {os.environ['MODEL']}")

    return llm_model


def json_decoder(directory_info):
    if isinstance(directory_info, str):
        directory_info = directory_info.replace("'", '"')
        try:
            directory_info = json.loads(directory_info)
        except json.JSONDecodeError as e:
            error_msg = str(e)
            if "Expecting property name enclosed in double quotes" in error_msg:
                directory_info += "}"
                directory_info = json.loads(directory_info)
            elif "Extra data" in error_msg:
                directory_info = directory_info[:-1]
                directory_info = json.loads(directory_info)
            else:
                raise
    return directory_info


def read_text_file(file_path: str, token_limit: int = 200) -> (str, bool):
    """
    Reads a text file and returns its content as a string.

    Args:
        file_path (str): The path to the text file to be read.

    Returns:
        str: The content of the file.
    """

    # Check if the file is a Python file and call another function if needed
    if file_path.endswith(".py"):
        return PythonFileAnalyzer(file_path).analyze(), True

    # TODO: V2: Launch GeneralFileAnalyzer
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            read_file = file.read()
            token_counter = num_tokens_from_string(read_file, "cl100k_base")

            if token_counter > token_limit:
                encoding = tiktoken.get_encoding("cl100k_base")
                return encoding.decode(encoding.encode(read_file)[:token_limit]), False
            return read_file, False
    except FileNotFoundError:
        _logger.error(f"File not found: {file_path}")
        raise
    except IOError as e:
        _logger.error(f"IOError while reading file {file_path}: {e}")
        raise


def extension_support_analysis(folder_dict: dict):
    extension_support = load_toml("readmate/configs/include_extensions.toml")

    supported_files = [
        f
        for f in folder_dict["files"]
        if os.path.splitext(f)[1].lstrip(".")
        in list(extension_support["extensions"].keys())
        or os.path.basename(f) in list(extension_support["filenames"].keys())
    ]
    unsupported_files = [
        f
        for f in folder_dict["files"]
        if os.path.splitext(f)[1].lstrip(".")
        not in list(extension_support["extensions"].keys())
    ]

    return supported_files, unsupported_files, extension_support


def extension_support_analysis_for_main_folder(folder_dict: dict):
    """Analyze support for files based on their extension or filename."""
    extension_support = load_toml("readmate/configs/include_extensions.toml")

    # Prepare lists for supported and unsupported files based on the folder_dict structure
    supported_files = []
    unsupported_files = []

    for filename, details in folder_dict.items():
        extension = details["file_extension"].lstrip(".")
        if extension in extension_support.get(
            "extensions", {}
        ) or filename in extension_support.get("filenames", {}):
            supported_files.append(filename)
        else:
            unsupported_files.append(filename)

    return supported_files, unsupported_files, extension_support


def filter_keys_recursively(data, keys, crucial_keys):
    """
    Filter a nested dictionary recursively, retaining only the specified keys.
    If a key with a dictionary value is specified to be retained, the entire dictionary is copied as is, without further filtering.

    Args:
    data (dict): The dictionary to filter.
    keys (list): The keys to retain in the resulting dictionary.

    Returns:
    dict: A new dictionary with only the specified keys retained, and dictionaries copied directly if their key is specified.
    """
    if isinstance(data, dict):
        # Create a new dictionary, only including specified keys or recursing as necessary
        new_dict = {}
        for key, value in data.items():
            if key in keys:
                if key in crucial_keys:
                    new_dict[key] = value
                elif isinstance(value, dict):
                    # Recurse for nested dictionaries
                    new_dict[key] = filter_keys_recursively(value, keys, crucial_keys)
                else:
                    # Directly copy the value if the current key is one of the specified keys
                    new_dict[key] = value

            elif isinstance(value, dict):
                # Even if the current key isn't one to retain, we still need to explore
                # its value for nested keys to retain
                potentially_filtered_value = filter_keys_recursively(
                    value, keys, crucial_keys
                )
                if potentially_filtered_value:
                    new_dict[key] = potentially_filtered_value
        return new_dict
    elif isinstance(data, list):
        # Apply the function to each dictionary in the list, assuming the list contains dictionaries
        return [
            filter_keys_recursively(item, keys, crucial_keys)
            for item in data
            if isinstance(item, dict)
        ]
    else:
        # Non-dictionary and non-list items get returned as is
        return data
