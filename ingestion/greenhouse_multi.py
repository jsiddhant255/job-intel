import csv
import requests
from datetime import datetime, timedelta, timezone
from pathlib import Path

DAYS = 3
INDIA_WORDS = ["bangalore", "bengaluru", "india"]
ROLE_WORDS = ["business analyst", "product analyst", "product operations",
              "business operations", "operations analyst", "product manager",
              "operations"]
CONFIG_FILE = Path(__file__).parent.parent / "config"/"companies.csv"
with open (CONFIG_FILE, newline="") as f:
    companies = list(csv.DictReader(f))

boards = [c["token"] for c in companies if c["source"]=="greenhouse"]
print(f"Loaded {len(boards)} Greenhouse companies from {CONFIG_FILE.name}")
cutoff = datetime.now(timezone.utc) - timedelta(days=DAYS)

for board in boards:
    url = f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs"
    resp = requests.get(url, timeout=30)

    if resp.status_code != 200:                 # 200 = OK, 404 = not found
        print(f"NOT FOUND  {board} (status {resp.status_code})")
        continue

    jobs = resp.json()["jobs"]
    matches = []
    for job in jobs:
        if not job.get("first_published"):
            continue
        posted = datetime.fromisoformat(job["first_published"])
        location = job["location"]["name"]
        if posted >= cutoff and any(w in location.lower() for w in INDIA_WORDS) and any(w in job["title"].lower() for w in ROLE_WORDS):
            matches.append((posted.date(), job["title"].strip(), location))
    print(f"OK         {board}: {len(jobs)} jobs, {len(matches)} matching roles")
    for m in matches:
        print(f"           -> {m[0]} | {m[1]} | {m[2]}")
