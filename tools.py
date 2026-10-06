# ============================================================
# ASTRA WINDOWS TOOLS
# ============================================================

import os
import subprocess
import time
import webbrowser

import pyautogui


# ============================================================
# WEBSITE
# ============================================================

def open_website(url):

    print(f"Opening website: {url}")

    webbrowser.open(url)

    return True


# ============================================================
# WINDOWS APPLICATION
# ============================================================

def open_windows_app(app_name):

    print(f"Searching Windows for: {app_name}")

    pyautogui.press("win")

    time.sleep(0.7)

    pyautogui.write(
        app_name,
        interval=0.03
    )

    time.sleep(1)

    pyautogui.press("enter")

    print(f"Started: {app_name}")

    return True


# ============================================================
# VS CODE
# ============================================================

def open_vscode():

    vscode_folder = (
        r"C:\Users\maina\AppData\Roaming"
        r"\Microsoft\Windows\Start Menu\Programs"
        r"\Visual Studio Code"
    )

    if not os.path.exists(vscode_folder):

        print("VS Code shortcut folder was not found.")

        return False

    for file in os.listdir(vscode_folder):

        if file.lower().endswith(".lnk"):

            shortcut = os.path.join(
                vscode_folder,
                file
            )

            os.startfile(shortcut)

            print(f"Opened VS Code: {file}")

            return True

    print("No VS Code shortcut was found.")

    return False


# ============================================================
# DOWNLOADS
# ============================================================

def open_downloads():

    downloads_path = os.path.join(
        os.path.expanduser("~"),
        "Downloads"
    )

    print("Opening Downloads...")

    subprocess.Popen([
        "explorer",
        downloads_path
    ])

    return True


# ============================================================
# TERMINAL
# ============================================================

def open_terminal():

    print("Opening terminal...")

    subprocess.Popen("cmd.exe")

    return True


# ============================================================
# OPEN PATH
# ============================================================

def open_path(path):

    path = os.path.expandvars(path)

    path = os.path.expanduser(path)

    if os.path.exists(path):

        print(f"Opening: {path}")

        os.startfile(path)

        return True

    print("Path does not exist.")

    return False