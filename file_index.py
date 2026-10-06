# ============================================================
# ASTRA FILE INDEX
# ============================================================

import os
import sqlite3

from config import ALLOWED_FOLDERS


DATABASE = "astra.db"


# ============================================================
# DATABASE
# ============================================================

def get_connection():

    return sqlite3.connect(DATABASE)


def initialize_database():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT UNIQUE NOT NULL,
            filename TEXT NOT NULL,
            extension TEXT,
            size INTEGER,
            modified REAL
        )
    """)

    connection.commit()
    connection.close()


# ============================================================
# INDEX FILES
# ============================================================

def rebuild_index():

    initialize_database()

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("DELETE FROM files")

    for folder in ALLOWED_FOLDERS:

        if not os.path.exists(folder):
            continue

        for root, dirs, files in os.walk(folder):

            for filename in files:

                path = os.path.join(root, filename)

                try:

                    stats = os.stat(path)

                    extension = os.path.splitext(
                        filename
                    )[1].lower()

                    cursor.execute("""
                        INSERT OR REPLACE INTO files
                        (path, filename, extension, size, modified)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        path,
                        filename,
                        extension,
                        stats.st_size,
                        stats.st_mtime
                    ))

                except OSError:
                    continue

    connection.commit()

    cursor.execute("SELECT COUNT(*) FROM files")

    count = cursor.fetchone()[0]

    connection.close()

    return count


# ============================================================
# SEARCH INDEX
# ============================================================

def search_index(query):

    initialize_database()

    connection = get_connection()

    cursor = connection.cursor()

    search = f"%{query}%"

    cursor.execute("""
        SELECT path, filename, extension, size
        FROM files
        WHERE filename LIKE ?
           OR path LIKE ?
        LIMIT 100
    """, (
        search,
        search
    ))

    rows = cursor.fetchall()

    connection.close()

    return rows