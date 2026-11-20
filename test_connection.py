import os
import psycopg
from dotenv import load_dotenv

load_dotenv()                          # read the .env file
url = os.environ["DATABASE_URL"]       # pick out the connection string

with psycopg.connect(url) as conn:     # open the line to Supabase
    with conn.cursor() as cur:         # a "cursor" = the pen we write SQL with
        cur.execute("select version();")
        print("Connected!", cur.fetchone()[0])

        cur.execute("select count(*) from raw.job_postings;")
        print("Rows in raw.job_postings:", cur.fetchone()[0])
