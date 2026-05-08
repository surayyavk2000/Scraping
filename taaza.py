from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import pandas as pd
import time

# --------------------------------
# SELENIUM SETUP
# --------------------------------
options = Options()
options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(options=options)

base_url = "https://taazaa.keka.com/careers"
driver.get(base_url)

time.sleep(6)

# --------------------------------
# STEP 1: COLLECT JOB LINKS
# --------------------------------
job_cards = driver.find_elements(By.CSS_SELECTOR, "a[href*='/jobdetails/']")

urls = list(set([
    j.get_attribute("href")
    for j in job_cards
    if j.get_attribute("href")
]))

jobs = []

# --------------------------------
# STEP 2: SCRAPE EACH JOB PAGE
# --------------------------------
for url in urls:
    driver.get(url)
    time.sleep(3)

    # -------------------------
    # TITLE
    # -------------------------
    try:
        title = driver.find_element(
            By.CSS_SELECTOR,
            "h1.kch-text-heading"
        ).text.strip()
    except:
        title = "N/A"

    # -------------------------
    # EXPERIENCE / LOCATION / TYPE
    # -------------------------
    experience = "N/A"
    location = "N/A"
    job_type = "N/A"

    blocks = driver.find_elements(
        By.CSS_SELECTOR,
        "div.d-flex.align-items-center"
    )

    for b in blocks:
        html = b.get_attribute("innerHTML")
        text = b.text.strip()

        if "ki-user-tie" in html:
            experience = text

        elif "ki-location" in html:
            location = text

        elif "ki-briefcase" in html:
            job_type = text

    # -------------------------
    # DESCRIPTION (IMPORTANT FIX)
    # -------------------------
    try:
        description = driver.find_element(
            By.CSS_SELECTOR,
            ".job-description-container"
        ).text.strip()

        description = " ".join(description.split())  # clean spacing

    except:
        description = "N/A"

    # -------------------------
    # STORE DATA
    # -------------------------
    jobs.append({
        "Job_name": title,
        "Location": location,
        "Experience": experience,
        "Type": job_type,
        "Description": description,
        "Company": "Taazaa",
        "Job_Link": url
    })

# --------------------------------
# CLEANUP
# --------------------------------
driver.quit()

# --------------------------------
# SAVE OUTPUT
# --------------------------------
df = pd.DataFrame(jobs)
df.drop_duplicates(inplace=True)

df.to_csv("taazaa_jobs.csv", index=False, encoding="utf-8")

print(df)
