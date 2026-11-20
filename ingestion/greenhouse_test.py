import requests
from datetime import datetime, timedelta, timezone

BOARD = "hackerrank"
DAYS = 3
INDIA_WORDS = ["bangalore", "bengaluru", "india"]

url = f"https://boards-api.greenhouse.io/v1/boards/{BOARD}/jobs"
jobs = requests.get(url, timeout=30).json()["jobs"]
print(f"Total jobs on {BOARD}: {len(jobs)}")

cutoff = datetime.now(timezone.utc) - timedelta(days=DAYS)

for job in jobs:
    if not job.get("first_published"):
        continue
    posted = datetime.fromisoformat(job["first_published"])
    location = job["location"]["name"]
    is_fresh = posted >= cutoff
    is_india = any(w in location.lower() for w in INDIA_WORDS)

    if is_fresh or is_india:
        tag = ("FRESH " if is_fresh else "      ") + ("INDIA" if is_india else "")
        print(f"[{tag:11}] {posted.date()} | {job['title']} | {location}")
