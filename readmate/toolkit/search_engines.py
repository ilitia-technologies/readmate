from pathlib import Path
from typing import Dict, List, Union
from readmate.utils.logger import set_logger

_logger = set_logger()


def recursive_directory_search(directory: str) -> Dict[str, any]:
    """
    Recursively searches directories and gathers information about subfolders, number of files,
    file extensions, number of lines, the current folder with its path, and a list of files under that folder and subfolders. Output is a dictionary.
    """

    def search_dir(
        path: Path, project_path_abs: Path, is_root: bool = False
    ) -> Dict[str, any]:
        info = {
            "current_folder": path.relative_to(project_path_abs).as_posix(),
            "subfolders": {},
            "num_files": 0,
            "file_extensions": {},
            "num_lines": 0,
            "files": [],
        }
        if is_root:
            info["main_project_folder"] = True
            is_root = False
        for item in path.iterdir():
            if item.is_dir():
                info["subfolders"][item.name] = search_dir(item, project_path_abs)
            else:
                info["num_files"] += 1
                extension = item.suffix
                if extension in info["file_extensions"]:
                    info["file_extensions"][extension] += 1
                else:
                    info["file_extensions"][extension] = 1
                info["files"].append(item.name)
                with open(item, "r", encoding="utf-8", errors="ignore") as file:
                    info["num_lines"] += sum(1 for _ in file)
        return info

    root_info = search_dir(
        Path(directory), is_root=True, project_path_abs=Path(directory)
    )
    return root_info


def list_files_outside_folders(
    directory: str,
) -> Dict[str, any]:
    """
    Searches the given directory and lists files that are not inside any subfolders.
    The information is saved in a dictionary with keys: file_extension, num_lines, filename.
    """

    def list_files(
        path: Path, project_path_abs: Path
    ) -> List[Dict[str, Union[str, int]]]:
        files_info = []
        for item in path.iterdir():
            if item.is_file():
                file_info = {
                    "file_extension": item.suffix,
                    "filename": item.name,
                    "num_lines": 0,
                    "current_folder": path.relative_to(project_path_abs).as_posix(),
                }
                with open(item, "r", encoding="utf-8", errors="ignore") as file:
                    file_info["num_lines"] = sum(1 for _ in file)
                files_info.append(file_info)
        return files_info

    files_outside_folders = list_files(
        path=Path(directory), project_path_abs=Path(directory)
    )
    return {"files": files_outside_folders}
