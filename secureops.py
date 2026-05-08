from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import requests
import re
import pandas as pd
import time

BASE_URL = "https://secureops.bamboohr.com"
LIST_URL = f"{BASE_URL}/careers/list"

headers = {"User-Agent": "Mozilla/5.0"}

data = requests.get(LIST_URL, headers=headers).json()

all_jobs = []

# =========================
# SELENIUM SETUP
# =========================
options = Options()
options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(options=options)

# =========================
# CLEAN DESCRIPTION
# =========================
def clean_job_description(text):

    include_sections = [
        "primary responsibilities",
        "qualifying skills",
        "responsibilities and duties",
        "qualification requirements",
        "qualifications and skills"
    ]

    noise_sections = [
        "benefits",
        "apply for this job",
        "link to this job",
        "location",
        "department",
        "employment type",
        "privacy policy",
        "terms of service",
        "©"
    ]

    lines = text.split("\n")

    result = []
    capture = False

    for line in lines:

        l = line.lower().strip()

        if any(sec in l for sec in include_sections):
            capture = True
            result.append("\n" + line.strip())
            continue

        if any(noise in l for noise in noise_sections):
            capture = False
            continue

        if capture and line.strip():
            result.append(line.strip())

    return "\n".join(result).strip()


# =========================
# MAIN LOOP
# =========================
for job in data.get("result", []):

    job_id = job["id"]
    url = f"{BASE_URL}/careers/{job_id}"

    print("Processing:", url)

    try:
        driver.get(url)
        time.sleep(5)

        soup = BeautifulSoup(driver.page_source, "html.parser")

        # =========================
        # TITLE
        # =========================
        title_tag = soup.find("meta", property="og:title")
        title = title_tag["content"] if title_tag else "N/A"

        # =========================
        # RAW TEXT
        # =========================
        main = soup.find("main")

        raw_text = (
            main.get_text("\n", strip=True)
            if main
            else soup.get_text("\n", strip=True)
        )

        raw_text = re.sub(r'\n+', '\n', raw_text)

        # =========================
        # CLEAN DESCRIPTION
        # =========================
        final_desc = clean_job_description(raw_text)

        if not final_desc:
            final_desc = "N/A"

        # =========================
        # ✅ CORRECT EXPERIENCE FIELD
        # =========================
        experience = (
            job.get("minimumExperience")
            or job.get("minimum_experience")
            or "N/A"
        )

        # =========================
        # LOCATION
        # =========================
        city = job.get("location", {}).get("city")
        state = job.get("location", {}).get("state")

        location = (
            f"{city}, {state}" if city and state
            else city or state or "N/A"
        )

        # =========================
        # STORE DATA
        # =========================
        all_jobs.append({
            "Job_name": title,
            "job_description": final_desc,
            "Posting_date": "N/A",
            "Experience": experience,
            "location": location,
            "company_name": "SecureOps",
            "job_application_link": url,
            "Type": "N/A"
        })

    except Exception as e:
        print("Error:", e)

driver.quit()

# =========================
# SAVE OUTPUT
# =========================
df = pd.DataFrame(all_jobs)
df.to_csv("secureops_jobs.csv", index=False, encoding="utf-8")

print(f"Saved {len(all_jobs)} jobs to secureops_jobs.csv")
