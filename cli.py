import os
import typer
import uuid
from readmate.readmate_agent import ReadMateAgent
from review_and_check import Reviewandcheck
from readmate.utils.logger import setup_logs_folder, set_logger
from readmate.utils.general_utils import (
    copy_project_folder,
    unzip_project_folder,
    is_zip_file,
    check_required_files,
    clean_project,
)
from readmate.utils.setup_env import load_environment_variables

app = typer.Typer()

load_environment_variables()


@app.command()
def main(
    output_dir: str = typer.Option(
        "readmate/json_output",
        "--output-dir",
        "-o",
        help="The path of the directory where we save the experiments",
    ),
    input_dir: str = typer.Option(
        "",
        "--input-dir",
        "-id",
        help="The path of the folder or zip file where the project is located",
    ),
    readme_only: bool = typer.Option(
        False,
        "--readme-only",
        "-ro",
        help="Flag to generate the readme from the input_dir",
    ),
):
    if input_dir == "":
        typer.echo(
            "Please provide a directory to document with the --input-dir or -id option."
        )
        raise typer.Abort()

    if readme_only and not check_required_files(input_dir, ReadMateAgent):
        typer.echo(
            "Readme only was selected but not all JSON files are present in the input folder. Please provide a directory where all the files are located."
        )
        raise typer.Abort()

    unique_id = str(uuid.uuid4())
    workspace_folder = os.path.join(output_dir, unique_id)
    os.makedirs(workspace_folder, exist_ok=True)

    setup_logs_folder(unique_dir=workspace_folder)
    _logger = set_logger()

    # Check if the input directory is a zip file and log the result
    if is_zip_file(input_dir):
        _logger.info(f"The input directory {input_dir} is a zip file.")

        # Call the function to unzip if the input is not a folder
        final_dst = unzip_project_folder(input_dir, workspace_folder, _logger)
        _logger.info(final_dst)
    else:
        _logger.info(f"The input directory {input_dir} is a folder.")

        # Call the function to copy the folder
        final_dst = copy_project_folder(input_dir, workspace_folder, _logger)

    clean_project(directory=final_dst, logger=_logger)

    rac = Reviewandcheck(
        folder_path=final_dst,
        project_extensions_path="readmate/configs/include_extensions.toml",
    )
    status, _ = rac.read_all_files_in_folder()

    if status:
        maa = ReadMateAgent(
            input_path=final_dst,
            workspace_path=workspace_folder,
            output_path=workspace_folder,
        )

        if readme_only:
            maa.run_readme_test(test_folder=input_dir)
        else:
            maa.run()


if __name__ == "__main__":
    app()
