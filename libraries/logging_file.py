"""Basic logging, centralized so sinks/other logging necessities can be customized centrally."""

import json
import logging
import os

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.propagate = False

formatter = logging.Formatter(
    r"%(asctime)s - %(levelname)-7s %(threadName)-12s [%(filename)s:%(lineno)s - %(funcName)s()] - %(message)s"
)
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)


def log_build_info() -> None:
    """Logs build information."""
    if os.path.exists("commit_info.json"):
        with open("commit_info.json", "r") as json_file:
            commit_info = json.load(json_file)

        repository_name = commit_info["repository_name"]
        branch_name = commit_info["branch"]
        commit_message = commit_info["commit_message"]

        log_message = "\n------------------------ Build Info ------------------------\n"
        log_message += f"Repository: {repository_name}\n"
        log_message += f"Branch: {branch_name}\n"
        log_message += f'Last Commit: "{commit_message}"\n'
        log_message += f"Committed by {commit_info['author_display_name']} at {commit_info['commit_datetime']}\n"
        log_message += "------------------------------------------------------------"
        logger.info(log_message)


if __name__ == "__main__":
    logger.info("Info logging test")
    logger.warning("Warning logging test")
    logger.error("Error logging test")
    logger.exception(Exception("Exception logging test"))
