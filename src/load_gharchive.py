import gzip
import json
import os
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

engine = create_engine(
    f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)


def parse_gharchive_file(filepath):
    """Parse a single .json.gz file from GitHub Archive."""
    events = []
    with gzip.open(filepath, "rt", encoding="utf-8") as f:
        for line in f:
            try:
                event = json.loads(line)
                events.append({
                    "event_id": event.get("id"),
                    "event_type": event.get("type"),
                    "actor_login": event.get("actor", {}).get("login"),
                    "repo_name": event.get("repo", {}).get("name"),
                    "created_at": event.get("created_at"),
                    "org_login": event.get("org", {}).get("login") if event.get("org") else None,
                })
            except json.JSONDecodeError:
                continue
    return pd.DataFrame(events)


def load_all_files(data_dir="data/raw"):
    """Load all .json.gz files into PostgreSQL."""
    all_files = [
        os.path.join(data_dir, f)
        for f in os.listdir(data_dir)
        if f.endswith(".json.gz")
    ]

    for filepath in sorted(all_files):
        print(f"Processing: {filepath}")
        df = parse_gharchive_file(filepath)
        df.to_sql("github_events", engine, if_exists="append", index=False)
        print(f"  Loaded {len(df)} events")

    print("Done.")


if __name__ == "__main__":
    load_all_files()