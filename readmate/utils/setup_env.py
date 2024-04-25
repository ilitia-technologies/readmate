import os

from os.path import join, dirname
from dotenv import load_dotenv

from readmate.utils.logger import set_logger


_logger = set_logger()


def load_environment_variables():
    """
    Load the environmental variables required for the application.
    """
    dotenv_path = join(dirname(__file__), ".env")

    load_dotenv(dotenv_path)  # Ensure dotenv is loaded here to capture .env variables
    with open(dotenv_path) as f:
        required_env_vars = [
            line.split("=")[0].strip()
            for line in f.readlines()
            if line.strip() and not line.startswith("#")
        ]
    missing_env_vars = [var for var in required_env_vars if not os.environ.get(var)]
    if missing_env_vars:
        raise EnvironmentError(
            f"Missing environment variables: {', '.join(missing_env_vars)}"
        )
    _logger.info("All required environment variables are set.")
