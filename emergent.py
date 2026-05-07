import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
from datetime import datetime, timedelta, timezone

BOARD = "emergentlabsinc"

# ---------------------------
# Fetch jobs list
# ---------------------------
api_url = f"https://boards-api.greenhouse.io/v1/boards/{BOARD}/jobs?content=true"
res = requests.get(api_url)
data = res.json()

jobs_data = data.get("jobs", [])
final_jobs = []

# ---------------------------
# Extract section safely
# ---------------------------
def extract_section(text, start, end_list):
    pattern = rf"{start}:(.*?)(?={'|'.join(end_list)}:|$)"
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)

    if match and match.group(1):
        content = match.group(1)

        # ✅ Remove duplicate headers inside section
        content = re.sub(r"(Good to Have|Nice to Have):?", "", content, flags=re.IGNORECASE)

        return content.strip()

    return ""

# ---------------------------
# Process jobs
# ---------------------------
for job in jobs_data:
    updated = job.get("updated_at", "")

    try:
        job_date = datetime.fromisoformat(updated.replace("Z", "+00:00"))
    except:
        continue

    # ✅ Filter last 2 days
    if job_date < datetime.now(timezone.utc) - timedelta(days=2):
        continue

    title = job.get("title", "N/A")
    location = job.get("location", {}).get("name", "N/A")
    link = job.get("absolute_url", "N/A")

    print("Processing:", title)

    try:
        page = requests.get(link)
        soup = BeautifulSoup(page.text, "html.parser")

        desc_div = soup.find("div", class_="job__description")
        if not desc_div:
            print("No description:", title)
            continue

        description_text = desc_div.get_text("\n", strip=True)

        # ---------------------------
        # Extract sections
        # ---------------------------
        what_you_do = extract_section(
            description_text,
            r"What You[’']ll Do",
            [r"What We[’']re Looking For", "Requirements", "Nice to Have", "Good to Have", "Why Join Us", "Benefits"]
        )

        what_we_look = extract_section(
            description_text,
            r"What We[’']re Looking For",
            ["Requirements", "Nice to Have", "Good to Have", "Why Join Us", "Benefits"]
        )

        # ✅ Prefer "Good to Have", fallback to "Nice to Have"
        good_to_have = extract_section(
            description_text,
            r"Good to Have",
            ["Why Join Us", "Benefits", "Perks"]
        )

        if not good_to_have:
            good_to_have = extract_section(
                description_text,
                r"Nice to Have",
                ["Why Join Us", "Benefits", "Perks"]
            )

        # ---------------------------
        # Extract Experience
        # ---------------------------
        exp_match = re.search(
            r"(\d+\+?\s*(?:to|-)\s*\d+\s*years|\d+\+?\s*years)",
            description_text,
            re.IGNORECASE
        )
        experience = exp_match.group(0) if exp_match else "N/A"

        # ---------------------------
        # Final Description (clean)
        # ---------------------------
        final_desc = f"""What You'll Do:
{what_you_do}

What We're Looking For:
{what_we_look}

Good to Have:
{good_to_have}"""

        # ✅ Remove extra blank lines
        final_desc = re.sub(r"\n\s*\n+", "\n\n", final_desc).strip()

        final_jobs.append({
            "Job_name": title,
            "job_description": final_desc,
            "Posting_date": job_date.strftime("%d_%m_%Y"),
            "Experience": experience,
            "location": location,
            "company_name": "Emergent",
            "job_application_link": link,
            "Type": "N/A"
        })

    except Exception as e:
        print("Error in job:", title)
        print("Reason:", e)

# ---------------------------
# Save CSV
# ---------------------------
df = pd.DataFrame(final_jobs)
df.to_csv("emergent_jobs.csv", index=False)

print("✅ Saved:", len(df), "jobs")
