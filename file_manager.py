# ============================================================
# ASTRA FILE MANAGER
# ============================================================

import os

from config import (
    ALLOWED_FOLDERS,
    MAX_FILE_SIZE_MB,
    TEXT_FILE_EXTENSIONS,
)


MAX_FILE_SIZE = MAX_FILE_SIZE_MB * 1024 * 1024


# ============================================================
# PATH SECURITY
# ============================================================

def get_allowed_path(path):

    path = os.path.expandvars(path)
    path = os.path.expanduser(path)

    path = os.path.abspath(path)

    for allowed_folder in ALLOWED_FOLDERS:

        allowed_folder = os.path.abspath(allowed_folder)

        try:
            common = os.path.commonpath([
                path,
                allowed_folder
            ])

            if common == allowed_folder:
                return path

        except ValueError:
            continue

    return None


# ============================================================
# LIST FILES
# ============================================================

def list_files(folder=None):

    if folder is None:

        folder = ALLOWED_FOLDERS[0]

    safe_folder = get_allowed_path(folder)

    if safe_folder is None:
        return {
            "success": False,
            "error": "Access denied. Folder is not allowed."
        }

    if not os.path.isdir(safe_folder):

        return {
            "success": False,
            "error": "Folder does not exist."
        }

    results = []

    for root, dirs, files in os.walk(safe_folder):

        for filename in files:

            full_path = os.path.join(root, filename)

            results.append(full_path)

            # Don't return thousands of results.
            if len(results) >= 200:
                return {
                    "success": True,
                    "files": results,
                    "truncated": True
                }

    return {
        "success": True,
        "files": results,
        "truncated": False
    }


# ============================================================
# SEARCH FILE NAMES
# ============================================================

def search_files(query):

    query = query.lower().strip()

    results = []

    for folder in ALLOWED_FOLDERS:

        if not os.path.exists(folder):
            continue

        for root, dirs, files in os.walk(folder):

            for filename in files:

                if query in filename.lower():

                    results.append(
                        os.path.join(root, filename)
                    )

                    if len(results) >= 100:

                        return {
                            "success": True,
                            "results": results,
                            "truncated": True
                        }

    return {
        "success": True,
        "results": results,
        "truncated": False
    }


# ============================================================
# SEARCH FILE CONTENT
# ============================================================

def search_file_content(query):

    query = query.lower().strip()

    results = []

    for folder in ALLOWED_FOLDERS:

        if not os.path.exists(folder):
            continue

        for root, dirs, files in os.walk(folder):

            for filename in files:

                extension = os.path.splitext(filename)[1].lower()

                if extension not in TEXT_FILE_EXTENSIONS:
                    continue

                path = os.path.join(root, filename)

                try:

                    size = os.path.getsize(path)

                    if size > MAX_FILE_SIZE:
                        continue

                    with open(
                        path,
                        "r",
                        encoding="utf-8",
                        errors="ignore"
                    ) as file:

                        content = file.read()

                    if query in content.lower():

                        results.append({
                            "file": path,
                            "match": True
                        })

                        if len(results) >= 50:

                            return {
                                "success": True,
                                "results": results,
                                "truncated": True
                            }

                except (PermissionError, OSError):
                    continue

    return {
        "success": True,
        "results": results,
        "truncated": False
    }


# ============================================================
# READ FILE
# ============================================================

def read_file(path):

    safe_path = get_allowed_path(path)

    if safe_path is None:

        return {
            "success": False,
            "error": "Access denied. File is outside allowed folders."
        }

    if not os.path.isfile(safe_path):

        return {
            "success": False,
            "error": "File does not exist."
        }

    extension = os.path.splitext(safe_path)[1].lower()

    if extension not in TEXT_FILE_EXTENSIONS:

        return {
            "success": False,
            "error": f"File type {extension} is not allowed for reading."
        }

    try:

        size = os.path.getsize(safe_path)

        if size > MAX_FILE_SIZE:

            return {
                "success": False,
                "error": "File is too large to read."
            }

        with open(
            safe_path,
            "r",
            encoding="utf-8",
            errors="ignore"
        ) as file:

            content = file.read()

        return {
            "success": True,
            "path": safe_path,
            "content": content
        }

    except PermissionError:

        return {
            "success": False,
            "error": "Permission denied."
        }

    except OSError as error:

        return {
            "success": False,
            "error": str(error)
        }