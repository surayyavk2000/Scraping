import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import pandas as pd

headers = {"User-Agent": "Mozilla/5.0"}

# =========================
# STEP 1: Get job links
# =========================
base_url = "https://webkul.com/jobs/"
res = requests.get(base_url, headers=headers)
soup = BeautifulSoup(res.text, "html.parser")

job_links = []
for a in soup.find_all("a", href=True):
    link = a["href"]
    if "webkul.com/jobs/" in link and link != base_url:
        job_links.append(link)

job_links = list(set(job_links))

print("Job links found:", len(job_links))


# =========================
# STEP 2: Scrape each job
# =========================
jobs = []

for link in job_links:
    print("Processing:", link)

    try:
        res = requests.get(link, headers=headers)
        soup = BeautifulSoup(res.text, "html.parser")

        # =========================
        # Extract Experience (TABLE)
        # =========================
        experience = "N/A"
        rows = soup.select("table tr")

        for row in rows:
            cols = row.find_all("td")
            if len(cols) == 2:
                key = cols[0].get_text(strip=True)
                value = cols[1].get_text(strip=True)

                if key.lower() == "experience":
                    experience = value
                    break

        # =========================
        # Extract Rich Description
        # =========================

        # Intro
        intro_tag = soup.select_one("p.desc.desc-job")
        intro = intro_tag.get_text(strip=True) if intro_tag else ""

        # Sections
        details_div = soup.select_one("div.wkgrid-left")
        sections_text = ""

        if details_div:
            elements = details_div.find_all(["h2", "ul"])
            capture = False

            for el in elements:
                if el.name == "h2":
                    heading = el.get_text(strip=True)

                    if "What You'll Do" in heading or "What You'll Bring" in heading:
                        capture = True
                        sections_text += f"\n\n{heading}:\n"
                    else:
                        capture = False

                elif el.name == "ul" and capture:
                    for li in el.find_all("li"):
                        sections_text += f"- {li.get_text(strip=True)}\n"

        job_description = intro + "\n" + sections_text

        # =========================
        # Extract JSON-LD
        # =========================
        scripts = soup.find_all("script", type="application/ld+json")

        for script in scripts:
            try:
                if not script.string:
                    continue

                data = json.loads(script.string)

                # Normalize structure
                if isinstance(data, dict) and "@graph" in data:
                    items = data["@graph"]
                elif isinstance(data, list):
                    items = data
                else:
                    items = [data]

                for item in items:
                    if item.get("@type") == "JobPosting":

                        title = item.get("title", "N/A")
                        job_url = item.get("url", link)
                        date_posted = item.get("datePosted", "")
                        employment = item.get("employmentType", "N/A")

                        # Format date
                        if date_posted:
                            posting_date = datetime.strptime(date_posted, "%Y-%m-%d")
                            posting_date = posting_date.strftime("%d_%m_%Y")
                        else:
                            posting_date = "N/A"

                        # Location (FIXED → addressRegion)
                        address = item.get("jobLocation", {}).get("address", {})
                        location = address.get("addressRegion", "N/A")

                        # Job Type detection
                        desc_lower = job_description.lower()
                        if "remote" in desc_lower:
                            job_type = "Remote"
                        elif "hybrid" in desc_lower:
                            job_type = "Hybrid"
                        else:
                            job_type = "On-site"

                        # Final record
                        jobs.append({
                            "Job_name": title,
                            "job_description": job_description.strip(),
                            "Posting_date": posting_date,
                            "Experience": experience,
                            "location": location,
                            "company_name": "Webkul",
                            "job_application_link": job_url,
                            "Type": job_type
                        })

            except:
                continue

    except Exception as e:
        print("Error:", e)


# =========================
# STEP 3: Save CSV
# =========================
df = pd.DataFrame(jobs)
df.to_csv("webkul_jobs.csv", index=False)

print("Saved:", len(df), "jobs")
