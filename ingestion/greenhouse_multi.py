import csv
import os
import requests
import psycopg
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
from psycopg.types.json import Jsonb

DAYS = 3
INDIA_WORDS = ["bangalore", "bengaluru", "india"]
# Target roles. Plain "operations" included on purpose for wider Ops coverage (see JI-6)
ROLE_WORDS = ["business analyst", "product analyst", "product operations",
              "business operations", "operations analyst", "product manager",
              "operations"]
# Company list lives in config/companies.csv so companies can be added without code changes
CONFIG_FILE = Path(__file__).parent.parent / "config"/"companies.csv"
with open (CONFIG_FILE, newline="") as f:
    companies = list(csv.DictReader(f))

boards = [c["token"] for c in companies if c["source"]=="greenhouse"]
print(f"Loaded {len(boards)} Greenhouse companies from {CONFIG_FILE.name}")
cutoff = datetime.now(timezone.utc) - timedelta(days=DAYS)
run_date = datetime.now(ZoneInfo("Asia/Kolkata")).date()   # today's date in India
names = {c["token"]: c["company"] for c in companies if c["source"] == "greenhouse"}
to_save = []                                               # all matches across all companies
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
            to_save.append((
                "greenhouse", names[board], str(job["id"]), job["title"].strip(),
                location, job["absolute_url"], posted, Jsonb(job), run_date,
            ))
    print(f"OK         {board}: {len(jobs)} jobs, {len(matches)} matching roles")
    for m in matches:
        print(f"           -> {m[0]} | {m[1]} | {m[2]}")

INSERT_SQL = """
    insert into raw.job_postings
        (source, company, external_id, title, location, url, posted_at, payload, run_date)
    values (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    on conflict (source, external_id, run_date) do nothing
"""

load_dotenv()
inserted = 0
with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
    with conn.cursor() as cur:
        for row in to_save:
            cur.execute(INSERT_SQL, row)
            inserted += cur.rowcount

print(f"Saved {inserted} new rows ({len(to_save) - inserted} already saved today)")