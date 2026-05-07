import requests
from bs4 import BeautifulSoup
import re
import pandas as pd

BASE_URL = "https://secureops.bamboohr.com"

LIST_URL = f"{BASE_URL}/careers/list"

headers = {
    "User-Agent": "Mozilla/5.0"
}

response = requests.get(LIST_URL, headers=headers)

data = response.json()

all_jobs = []

for job in data.get("result", []):

    job_id = job.get("id")

    job_url = f"{BASE_URL}/careers/{job_id}"

    # --------------------------------
    # OPEN JOB PAGE
    # --------------------------------
    detail_response = requests.get(
        job_url,
        headers=headers
    )

    soup = BeautifulSoup(
        detail_response.text,
        "html.parser"
    )

    # --------------------------------
    # JOB TITLE
    # --------------------------------
    title_meta = soup.find(
        "meta",
        attrs={"property": "og:title"}
    )

    title = (
        title_meta.get("content", "N/A")
        if title_meta else "N/A"
    )

    # --------------------------------
    # DESCRIPTION
    # --------------------------------
    desc_meta = soup.find(
        "meta",
        attrs={"property": "twitter:description"}
    )

    if desc_meta:
        final_desc = desc_meta.get(
            "content",
            "N/A"
        ).strip()
    else:
        final_desc = "N/A"

    # --------------------------------
    # EXPERIENCE EXTRACTION
    # --------------------------------
    experience = "N/A"

    experience_patterns = [

        r'(\d+\+?\s*(?:years?|yrs?)\s*(?:of)?\s*experience)',

        r'((?:one|two|three|four|five|six|seven|eight|nine|ten)'
        r'\s*\(\d+\)\s*years?)',

        r'(at least\s+\d+\s*(?:years?|yrs?))',
    ]

    for pattern in experience_patterns:

        match = re.search(
            pattern,
            final_desc,
            re.IGNORECASE
        )

        if match:
            experience = match.group(1)
            break

    # --------------------------------
    # LOCATION
    # --------------------------------
    city = job.get(
        "location",
        {}
    ).get("city")

    state = job.get(
        "location",
        {}
    ).get("state")

    if city and state:
        location = f"{city}, {state}"
    elif city:
        location = city
    elif state:
        location = state
    else:
        location = "N/A"

    # --------------------------------
    # STORE DATA
    # --------------------------------
    all_jobs.append({

        "Job_name": title,

        "job_description": final_desc,

        "Posting_date": "N/A",

        "Experience": experience,

        "location": location,

        "company_name": "SecureOps",

        "job_application_link": job_url,

        "Type": "N/A"
    })

# --------------------------------
# SAVE TO CSV
# --------------------------------
df = pd.DataFrame(all_jobs)

csv_file_name = "secureops_jobs.csv"

df.to_csv(
    csv_file_name,
    index=False,
    encoding="utf-8"
)

print(f"Saved {len(all_jobs)} jobs to {csv_file_name}")
