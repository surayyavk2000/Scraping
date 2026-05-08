import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone
import json
import re
import time

# --------------------------------------------------
# CONFIG
# --------------------------------------------------
COMPANY_SLUG = "best-buy-india"

headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json,text/html"
}

jobs = []

# --------------------------------------------------
# DATE FILTER -> LAST 30 DAYS
# --------------------------------------------------
today = datetime.now(timezone.utc)

last_month = today - timedelta(days=30)

# --------------------------------------------------
# FETCH ALL JOBS
# --------------------------------------------------
all_jobs = []

offset = 0
size = 20

seen_ids = set()

while True:

    api_url = (
        f"https://prod-warmachine.talent500.co/api/v3/jobs/search/"
        f"?company_slug={COMPANY_SLUG}"
        f"&offset={offset}"
        f"&size={size}"
    )

    print("\nFetching:", api_url)

    response = requests.get(
        api_url,
        headers=headers
    )

    print("Status:", response.status_code)

    if response.status_code != 200:
        break

    data = response.json()

    current_jobs = data.get("data", [])

    # ----------------------------------------------
    # STOP IF EMPTY
    # ----------------------------------------------
    if not current_jobs:

        print("No more jobs.")

        break

    new_jobs = 0

    for job in current_jobs:

        job_id = job.get("id")

        if job_id not in seen_ids:

            seen_ids.add(job_id)

            all_jobs.append(job)

            new_jobs += 1

    print("New Jobs Added:", new_jobs)

    # ----------------------------------------------
    # STOP IF REPEATED
    # ----------------------------------------------
    if new_jobs == 0:

        print("Repeated jobs detected.")

        break

    # ----------------------------------------------
    # LAST PAGE
    # ----------------------------------------------
    if len(current_jobs) < size:

        print("Last page reached.")

        break

    offset += size

    time.sleep(1)

print("\nTotal Unique Jobs:", len(all_jobs))

# --------------------------------------------------
# PROCESS EACH JOB
# --------------------------------------------------
for job in all_jobs:

    try:

        created_at = job.get("created_at", "")

        created_date = datetime.fromisoformat(
            created_at.replace("Z", "+00:00")
        )

        # ------------------------------------------
        # FILTER LAST 30 DAYS
        # ------------------------------------------
        if created_date < last_month:
            continue

        # ------------------------------------------
        # BASIC DETAILS
        # ------------------------------------------
        title = job.get("title", "N/A")

        location = job.get("location", "N/A")

        employment_type = job.get(
            "employment_type",
            "N/A"
        )

        min_exp = job.get(
            "min_experience_years"
        )

        max_exp = job.get(
            "max_experience_years"
        )

        if (
            min_exp is not None
            and
            max_exp is not None
        ):

            experience = (
                f"{min_exp}-{max_exp} Years"
            )

        else:

            experience = "N/A"

        # ------------------------------------------
        # DATE FORMAT -> dd_mm_yyyy
        # ------------------------------------------
        posting_date = created_date.strftime(
            "%d_%m_%Y"
        )

        # ------------------------------------------
        # JOB URL
        # ------------------------------------------
        slug = job.get("slug", "")

        job_url = (
            f"https://talent500.com/jobs/"
            f"{COMPANY_SLUG}/{slug}/"
        )

        print("\nScraping:", title)

        # ------------------------------------------
        # FETCH JOB PAGE
        # ------------------------------------------
        final_desc = "N/A"

        job_response = requests.get(
            job_url,
            headers=headers
        )

        if job_response.status_code == 200:

            html = job_response.text

            # --------------------------------------------------
            # METHOD 1 -> JSON-LD SCRIPT
            # --------------------------------------------------
            soup = BeautifulSoup(
                html,
                "html.parser"
            )

            scripts = soup.find_all(
                "script",
                type="application/ld+json"
            )

            found = False

            for script in scripts:

                try:

                    data_json = json.loads(
                        script.string
                    )

                    # --------------------------------------
                    # JOB DESCRIPTION
                    # --------------------------------------
                    if isinstance(data_json, dict):

                        desc = data_json.get(
                            "description"
                        )

                        if desc:

                            final_desc = desc

                            found = True

                            break

                except:
                    pass

            # --------------------------------------------------
            # METHOD 2 -> META DESCRIPTION
            # --------------------------------------------------
            if not found:

                meta_desc = soup.find(
                    "meta",
                    attrs={
                        "name": "description"
                    }
                )

                if meta_desc:

                    final_desc = meta_desc.get(
                        "content",
                        "N/A"
                    )

            # --------------------------------------------------
            # CLEAN HTML TAGS
            # --------------------------------------------------
            final_desc = BeautifulSoup(
                final_desc,
                "html.parser"
            ).get_text(
                " ",
                strip=True
            )

            # --------------------------------------------------
            # REMOVE UNWANTED TEXT
            # --------------------------------------------------
            remove_texts = [

                title,

                "Apply for this job",

                "Share with someone awesome",

                "View all job openings",

                "Powered by",

                "Best Buy",

                "Jobs",

                "Careers"

            ]

            for txt in remove_texts:

                final_desc = final_desc.replace(
                    txt,
                    ""
                )

            # --------------------------------------------------
            # CLEAN SPACES
            # --------------------------------------------------
            final_desc = re.sub(
                r'\s+',
                ' ',
                final_desc
            ).strip()

        # ------------------------------------------
        # STORE DATA
        # ------------------------------------------
        jobs.append({

            "Job_name": title,

            "job_description": final_desc,

            "Posting_date": posting_date,

            "Experience": experience,

            "location": location,

            "company_name": "Best Buy India",

            "job_application_link": job_url,

            "Type": employment_type
            if employment_type
            else "N/A"
        })

        print("Added:", title)

    except Exception as e:

        print("Error:", e)

# --------------------------------------------------
# SAVE CSV
# --------------------------------------------------
df = pd.DataFrame(jobs)

df.drop_duplicates(inplace=True)

df.to_csv(
    "talent500_jobs.csv",
    index=False,
    encoding="utf-8"
)

print("\nSaved talent500_jobs.csv\n")

print(df) 

