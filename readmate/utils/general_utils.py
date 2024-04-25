import os
import tiktoken
import shutil
import zipfile


def num_tokens_from_string(string: str, encoding_name: str) -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens


def copy_project_folder(src, dst, _logger, move=False):
    """
    Copy the contents of the source directory to the destination directory.

    Args:
        src (str): The path to the source directory.
        dst (str): The path to the destination directory where the source directory will be copied into.
        move (bool): If True, move the folder. If False, copy the folder.
    """
    try:
        # Create a new destination path inside the existing destination directory with the same name as the source
        final_dst = os.path.join(dst, os.path.basename(src))
        # Either copy or move the entire contents of the source directory to the new destination path
        if move:
            shutil.move(src, final_dst)
            _logger.info(f"Successfully moved {src} to {final_dst}")
        else:
            shutil.copytree(src, final_dst)
            _logger.info(f"Successfully copied {src} to {final_dst}")
        return final_dst
    except FileExistsError:
        _logger.info(
            f"The directory {final_dst} already exists inside the destination path. Please check the destination path."
        )
    except Exception as e:
        _logger.info(f"An error occurred while copying the directory: {e}")


def unzip_project_folder(zip_path, output_dir, _logger):
    """
    Unzip a zip file to a specified output directory.

    Args:
        zip_path (str): The path to the zip file.
        output_dir (str): The output directory where the zip contents will be extracted.
        _logger (logging.Logger): Logger for logging information about the process.
    Returns:
        str: The full path to the extracted folder.
    """
    try:
        # Extract the base name of the zip file without the extension
        zip_name = os.path.splitext(os.path.basename(zip_path))[0]
        # Create a new directory path using the zip file's name
        new_dir_path = os.path.join(output_dir, zip_name)

        # Ensure the new directory exists
        os.makedirs(new_dir_path, exist_ok=True)

        # Open the zip file
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(new_dir_path)
            _logger.info(f"Successfully unzipped {zip_path} to {new_dir_path}")

        return new_dir_path
    except Exception as e:
        _logger.error(f"An error occurred while unzipping the file: {e}")


def is_zip_file(input_dir: str) -> bool:
    """
    Check if the input directory is a zip file.

    Args:
        input_dir (str): The path to the input directory or zip file.

    Returns:
        bool: True if the input directory is a zip file, False otherwise.
    """
    return os.path.isfile(input_dir) and input_dir.endswith(".zip")


def check_required_files(input_folder: str, readmateagent) -> bool:
    """
    Check if the input_folder contains the four required files.

    Args:
        input_folder (str): The path to the input folder.

    Returns:
        bool: True if all required files are found, False otherwise.
    """
    required_files = [
        readmateagent.INFO_MODULES_JSON,
        readmateagent.INFO_FILES_JSON,
        readmateagent.INFO_FILES_EXTENDED_JSON,
        readmateagent.INFO_MODULES_EXTENDED_JSON,
    ]

    # Check if all required files exist in the input_folder
    return all(
        os.path.isfile(os.path.join(input_folder, file)) for file in required_files
    )


def clean_project(directory, logger):
    """
    Recursively delete '__pycache__' directories, '.git' folders, and '.md' files in the specified directory.

    Args:
    directory (str): The root directory to start the cleanup process.
    """
    for root, dirs, files in os.walk(directory, topdown=False):
        # Remove .md files
        for file in files:
            if file.endswith(".md"):
                file_path = os.path.join(root, file)
                os.remove(file_path)
                logger.warning(f"Deleted file: {file_path}")

        # Remove __pycache__ directories and .git folders
        for dir in dirs:
            if dir == "__pycache__" or dir == ".git":
                dir_path = os.path.join(root, dir)
                shutil.rmtree(dir_path)
                logger.warning(f"Deleted directory: {dir_path}")
