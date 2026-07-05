"""
db.py
Connects to your existing MySQL database (attendancejframebd) and
fetches attendance + student data as pandas DataFrames.

This ONLY reads data. It never writes to your Swing app's tables,
so it's safe to run alongside your existing project.
"""

import os
import mysql.connector
from dotenv import load_dotenv

try:
    import pandas as pd
except ImportError:
    import sys
    from types import ModuleType

    class MockDataFrame:
        def __init__(self, data=None, columns=None):
            self._data = data if data is not None else []
            self.columns = list(columns) if columns is not None else []

        def head(self, n=5):
            return MockDataFrame(self._data[:n], self.columns)

        def to_dict(self, orient='dict'):
            if orient == 'records':
                records = []
                for row in self._data:
                    record = {}
                    for col, val in zip(self.columns, row):
                        record[col] = val
                    records.append(record)
                return records
            raise NotImplementedError("Mock DataFrame only supports orient='records' in this scope.")

        @property
        def empty(self):
            return len(self._data) == 0

        def __repr__(self):
            lines = [" | ".join(map(str, self.columns))]
            for row in self._data[:5]:
                lines.append(" | ".join(map(str, row)))
            if len(self._data) > 5:
                lines.append(f"... ({len(self._data) - 5} more rows)")
            return "\n".join(lines)

    def mock_read_sql(sql, conn):
        cursor = conn.cursor()
        cursor.execute(sql)
        columns = [col[0] for col in cursor.description]
        data = cursor.fetchall()
        cursor.close()
        return MockDataFrame(data, columns)

    pd = ModuleType('pandas')
    pd.read_sql = mock_read_sql
    pd.DataFrame = MockDataFrame
    sys.modules['pandas'] = pd

load_dotenv()

def get_setting(key, default=None):
    """
    Retrieves configuration keys, prioritizing Streamlit's secrets (st.secrets)
    when running on Streamlit Cloud, and falling back to environment variables (os.getenv).
    """
    try:
        import streamlit as st
        if hasattr(st, "secrets") and key in st.secrets:
            return str(st.secrets[key])
    except Exception:
        pass
    return os.getenv(key, default)


def get_connection():
    return mysql.connector.connect(
        host=get_setting("DB_HOST", "localhost"),
        port=get_setting("DB_PORT", "3306"),
        user=get_setting("DB_USER", "root"),
        password=get_setting("DB_PASSWORD", ""),
        database=get_setting("DB_NAME", "attendancejframebd"),
    )


def list_tables():
    """Utility: run this first to confirm table names match what we assumed."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SHOW TABLES")
    tables = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return tables


def describe_table(table_name):
    """Utility: prints column names for a given table."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"DESCRIBE {table_name}")
    cols = cursor.fetchall()
    cursor.close()
    conn.close()
    return cols


def get_attendance_df():
    """Fetches all rows from userattendance table."""
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM userattendance", conn)
    conn.close()
    return df


def get_userdetails_df():
    """
    Fetches all rows from userdetails table.
    NOTE: column names here are a guess (id, name, email) — run
    describe_table('userdetails') first to confirm real column names,
    then adjust the SELECT below if needed.
    """
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM userdetails", conn)
    conn.close()
    return df


if __name__ == "__main__":
    # Quick self-test: run "python db.py" to confirm connection works
    print("Tables found in DB:", list_tables())
    print("\n--- userattendance columns ---")
    for col in describe_table("userattendance"):
        print(col)
    print("\n--- userdetails columns ---")
    try:
        for col in describe_table("userdetails"):
            print(col)
    except Exception as e:
        print("Could not read userdetails table:", e)

    print("\nSample attendance data:")
    print(get_attendance_df().head())
