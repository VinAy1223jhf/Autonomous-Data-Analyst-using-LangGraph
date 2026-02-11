# tools/schema_inspector.py
# this file helps to extract column names and table name from the database, which can be used by the SQL agent to generate better SQL queries.

import sqlite3
from pathlib import Path
from typing import Dict, List

DB_PATH = Path("database/people.db")

def get_tables() -> List[str]:
    """
    Returns a list of table names in the database.
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table';"
    )
    tables = [row[0] for row in cur.fetchall()]

    conn.close()
    return tables


def get_table_columns(table_name: str) -> List[str]:
    """
    Returns a list of column names for a given table.
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute(f"PRAGMA table_info('{table_name}')")
    columns = [row[1] for row in cur.fetchall()]

    conn.close()
    return columns


def get_full_schema() -> Dict[str, List[str]]:
    """
    Returns full database schema:
    {
        table_name: [col1, col2, ...]
    }
    """
    schema = {}
    for table in get_tables():
        schema[table] = get_table_columns(table)
    return schema


print(get_tables())
print(get_table_columns("people"))
print(get_full_schema())
