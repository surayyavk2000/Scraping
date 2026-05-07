from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import pandas as pd
import time

# --------------------------------
# SELENIUM SETUP
# --------------------------------
options = Options()
options.add_argument("--headless")

driver = webdriver.Chrome(options=options)

url = "https://taazaa.keka.com/careers"

driver.get(url)

time.sleep(10)

# --------------------------------
# GET JOB LINKS
# --------------------------------
job_cards = driver.find_elements(By.TAG_NAME, "a")

jobs = []

for card in job_cards:

    try:
        text = card.text.strip()
        href = card.get_attribute("href")

        if not text or not href:
            continue

        if "/jobdetails/" not in href:
            continue

        # split lines
        lines = text.split("\n")

        # default values
        title = lines[0] if len(lines) > 0 else "N/A"
        location = lines[1] if len(lines) > 1 else "N/A"
        experience = lines[2] if len(lines) > 2 else "N/A"
        job_type = lines[3] if len(lines) > 3 else "N/A"

        jobs.append({
            "Job_name": title,
            "Location": location,
            "Experience": experience,
            "Type": job_type,
            "Company": "Taazaa",
            "Job_Link": href
        })

    except Exception as e:
        print(e)

driver.quit()

# --------------------------------
# SAVE CSV
# --------------------------------
df = pd.DataFrame(jobs)

df.drop_duplicates(inplace=True)

df.to_csv(
    "taazaa_jobs.csv",
    index=False,
    encoding="utf-8"
)

print(df)
