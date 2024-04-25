import os
from tqdm import tqdm
from readmate.utils.general_utils import num_tokens_from_string
from readmate.utils.utils_tools import load_toml
from readmate.utils.logger import set_logger


_logger = set_logger()

TOKEN_LIMITER = 100000
FILE_COUNTER = 400
LANGUAGE_KEY_EXTENSION = "py"


class Reviewandcheck:
    def __init__(self, folder_path: str, project_extensions_path) -> None:
        self.project_extensions_path = project_extensions_path
        self.read_token_counter = 0
        self.total_token_counter = 0
        self.token_read = 200
        self.folder_path = folder_path
        self.file_counter = 0
        self.python_flag = False

    def max_token_exception(self):
        if self.read_token_counter > TOKEN_LIMITER:
            exception_message = "Max read token reached: {}".format(
                self.read_token_counter
            )
            return False, exception_message
            # elif self.total_token_counter > TOKEN_LIMITER:
            #    exception_message = "Max total token reached: {}".format(
            #       self.total_token_counter
            #    )
            # return False, exception_message
        else:
            return True, None

    def max_files_exception(self):
        if self.file_counter > FILE_COUNTER:
            exception_message = "Max total files reached: {}".format(self.file_counter)
            return False, exception_message
        else:
            return True, None

    def python_exception(self):
        pass

    def list_all_files_recursively(self, folder_path):
        """Generator that yields file paths in the given folder and its subfolders."""
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                yield os.path.join(root, file)

    def read_file(self, file_path, supported_list_extensions):
        """Reads and prints the content of the given file."""
        _, file_extension = os.path.splitext(file_path)

        if file_extension[1:] == LANGUAGE_KEY_EXTENSION:
            self.python_flag = True

        if file_extension[1:] in supported_list_extensions:
            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    tokens = num_tokens_from_string(
                        file.read(), encoding_name="cl100k_base"
                    )

                    self.file_counter += 1
                    # _logger.info(f"Tokens of {file_path}: {tokens}")

                    if tokens < self.token_read:
                        self.read_token_counter += tokens
                    else:
                        self.read_token_counter += self.token_read
                    self.total_token_counter += tokens
                    # _logger.info("--------------------------------------------------")

                    status_tokens, msg_exception_tokens = self.max_token_exception()
                    status_files, msg_exception_files = self.max_files_exception()

                    if not status_tokens or not status_files:
                        if msg_exception_tokens is not None:
                            msg_to_return = msg_exception_tokens
                        else:
                            msg_to_return = msg_exception_files

                        return (
                            False,
                            msg_to_return,
                        )
                    else:
                        return True, _

            except Exception as e:
                _logger.info(f"Error reading file {file_path}: {e}")

        return True, _

    def read_all_files_in_folder(self):
        extension_support = load_toml(self.project_extensions_path)

        supported_list_extensions = list(extension_support["extensions"].keys())
        """Lists and then reads the content of all files in the specified folder."""
        for file_path in tqdm(self.list_all_files_recursively(self.folder_path)):
            status, msg_status = self.read_file(file_path, supported_list_extensions)

            if not status:
                _logger.error(msg_status)
                return False, msg_status

        if not self.python_flag:
            msg_python_error = "This project does not contain any python code"
            _logger.error(msg_python_error)
            return False, msg_python_error

        _logger.info("--------------------------------------------------")
        _logger.info(
            f"Total Tokens of the project {self.folder_path}: {self.total_token_counter}"
        )
        _logger.info("--------------------------------------------------")
        _logger.info(
            f"Total Read Tokens of the project {self.folder_path}: {self.read_token_counter}"
        )
        _logger.info("--------------------------------------------------")

        return True, None
