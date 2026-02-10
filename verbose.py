"""
Shared logging for chat automation
"""
import os

VERBOSE = os.environ.get("CHAT_AUTOMATION_VERBOSE", "") == "1"


def log(msg: str):
    """Print only if verbose mode enabled"""
    if VERBOSE:
        print(msg)


def set_verbose(enabled: bool):
    """Set verbose mode globally"""
    global VERBOSE
    VERBOSE = enabled
    if enabled:
        os.environ["CHAT_AUTOMATION_VERBOSE"] = "1"
    else:
        os.environ.pop("CHAT_AUTOMATION_VERBOSE", None)
