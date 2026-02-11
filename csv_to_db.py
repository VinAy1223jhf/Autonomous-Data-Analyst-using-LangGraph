import pandas as pd
import sqlite3
from pathlib import Path

# Paths
CSV_PATH = Path("data/people-100.csv")
DB_PATH = Path("database/people.db")

# Ensure db directory exists
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

def load_csv_to_sqlite():
    print("Loading CSV...")
    df = pd.read_csv(CSV_PATH)

    print("CSV columns:")
    print(df.columns.tolist())

    print("Connecting to SQLite...")
    conn = sqlite3.connect(DB_PATH)

    print("Writing to database...")
    df.to_sql(
        name="people",
        con=conn,
        if_exists="replace",
        index=False
    )

    conn.close()
    print("✅ Data loaded successfully into db/people.db")

if __name__ == "__main__":
    load_csv_to_sqlite()
