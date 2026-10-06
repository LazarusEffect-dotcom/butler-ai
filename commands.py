# commands.py

import os
import re
from urllib.parse import quote

from config import APPLICATION_ALIASES

from tools import (
    open_website,
    open_windows_app,
    open_vscode,
    open_downloads,
    open_terminal,
    open_path,
)


# ============================================================
# URL DETECTION
# ============================================================

def is_url(text):
    """
    Check whether the user entered a website.
    """

    # http://
    if text.startswith("http://"):
        return True

    # https://
    if text.startswith("https://"):
        return True

    # www.example.com
    if text.startswith("www."):
        return True

    # example.com
    if "." in text and " " not in text:

        pattern = r"^[a-zA-Z0-9-]+\.[a-zA-Z]{2,}$"

        if re.match(pattern, text):
            return True

    return False


# ============================================================
# OPEN WEBSITE
# ============================================================

def handle_website(target):

    if not target.startswith(
        ("http://", "https://")
    ):

        target = "https://" + target

    open_website(target)


# ============================================================
# GOOGLE SEARCH
# ============================================================

def google_search(query):

    encoded_query = quote(query)

    url = (
        "https://www.google.com/search?q="
        + encoded_query
    )

    open_website(url)


# ============================================================
# MAIN COMMAND PROCESSOR
# ============================================================

def process_command(command):

    command = command.strip()

    if not command:
        return "unknown"


    command_lower = command.lower()


    # ========================================================
    # EXIT
    # ========================================================

    if command_lower in [
        "exit",
        "quit",
        "shutdown",
        "goodbye"
    ]:

        return "exit"


    # ========================================================
    # OPEN COMMAND
    # ========================================================

    if command_lower.startswith("open "):

        target = command[5:].strip()

        target_lower = target.lower()


        # ----------------------------------------------------
        # WEBSITE
        # ----------------------------------------------------

        if is_url(target):

            handle_website(target)

            return "success"


        # ----------------------------------------------------
        # SPECIAL: VS CODE
        # ----------------------------------------------------

        if target_lower in [
            "vscode",
            "vs code",
            "visual studio code"
        ]:

            open_vscode()

            return "success"


        # ----------------------------------------------------
        # SPECIAL: DOWNLOADS
        # ----------------------------------------------------

        if target_lower in [
            "downloads",
            "download folder"
        ]:

            open_downloads()

            return "success"


        # ----------------------------------------------------
        # SPECIAL: TERMINAL
        # ----------------------------------------------------

        if target_lower in [
            "terminal",
            "command prompt",
            "cmd"
        ]:

            open_terminal()

            return "success"


        # ----------------------------------------------------
        # FILE OR FOLDER PATH
        # ----------------------------------------------------

        if os.path.exists(target):

            open_path(target)

            return "success"


        # ----------------------------------------------------
        # KNOWN APPLICATION ALIAS
        # ----------------------------------------------------

        if target_lower in APPLICATION_ALIASES:

            app_name = APPLICATION_ALIASES[target_lower]

            open_windows_app(app_name)

            return "success"


        # ----------------------------------------------------
        # ANY OTHER WINDOWS APPLICATION
        # ----------------------------------------------------

        # Example:
        #
        # open blender
        # open photoshop
        # open firefox
        # open telegram
        #
        # Astra sends the name to Windows Start Menu.

        open_windows_app(target)

        return "success"


    # ========================================================
    # SEARCH COMMAND
    # ========================================================

    if command_lower.startswith("search "):

        query = command[7:].strip()

        if query:

            google_search(query)

            return "success"


    # ========================================================
    # UNKNOWN
    # ========================================================

    return "unknown"