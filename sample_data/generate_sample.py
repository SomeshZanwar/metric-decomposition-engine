"""
Run once to generate the demo dataset.
Usage: python sample_data/generate_sample.py
"""
import pandas as pd
import numpy as np
import os

np.random.seed(42)
os.makedirs("sample_data", exist_ok=True)

DATES   = ["2024-01-15", "2024-01-22"]
ACTORS  = [
    "alice-dev", "bob-codes", "carol-eng",
    "github-actions[bot]", "dependabot[bot]",
    "frank-ops", "grace-ml", "henry-backend",
]
ORGS = ["tech-corp", "startup-co", "open-source-org", "0", "0", None]
REPO_COUNT = 3

rows, eid = [], 1

for date in DATES:
    push_drop = 1.0 if date == "2024-01-15" else 0.42

    for actor in ACTORS:
        org = np.random.choice(ORGS)
        for i in range(1, REPO_COUNT + 1):
            repo = f"{actor}/project-{i:02d}"

            base_n      = np.random.randint(30, 90)
            actor_drop  = (
                0.15 if actor in ["alice-dev", "github-actions[bot]"] and date == "2024-01-22"
                else 1.0
            )
            n_push = max(0, int(base_n * push_drop * actor_drop))
            for _ in range(n_push):
                rows.append(dict(
                    event_id=eid, event_type="PushEvent",
                    actor_login=actor, repo_name=repo,
                    org_login=org or "0", event_date=date,
                    created_at=f"{date}T{np.random.randint(0,24):02d}:{np.random.randint(0,60):02d}:00Z",
                ))
                eid += 1

            for _ in range(np.random.randint(2, 12)):
                rows.append(dict(
                    event_id=eid, event_type="PullRequestEvent",
                    actor_login=actor, repo_name=repo,
                    org_login=org or "0", event_date=date,
                    created_at=f"{date}T{np.random.randint(0,24):02d}:{np.random.randint(0,60):02d}:00Z",
                ))
                eid += 1

            for _ in range(np.random.randint(1, 7)):
                rows.append(dict(
                    event_id=eid, event_type="IssuesEvent",
                    actor_login=actor, repo_name=repo,
                    org_login=org or "0", event_date=date,
                    created_at=f"{date}T{np.random.randint(0,24):02d}:{np.random.randint(0,60):02d}:00Z",
                ))
                eid += 1

df = pd.DataFrame(rows)
out = "sample_data/github_events_sample.csv"
df.to_csv(out, index=False)
print(f"✓ Generated {len(df):,} rows → {out}")
print(df.groupby(["event_date", "event_type"]).size().unstack(fill_value=0))