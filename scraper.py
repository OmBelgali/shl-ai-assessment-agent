import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import json
import time

BASE_URL = "https://www.shl.com"
CATALOG_URL = "https://www.shl.com/solutions/products/product-catalog/"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


def get_catalog_links():
    response = requests.get(CATALOG_URL, headers=HEADERS, timeout=20)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    links = soup.find_all("a")

    assessments = []
    seen = set()

    for link in links:
        title = link.get_text(strip=True)
        href = link.get("href")

        if not title or not href:
            continue

        if "/products/product-catalog/view/" in href:

            full_url = urljoin(BASE_URL, href)

            if full_url not in seen:
                seen.add(full_url)

                assessments.append({
                    "name": title,
                    "url": full_url
                })

    return assessments


def scrape_assessment_details(assessment):

    url = assessment["url"]

    try:
        response = requests.get(url, headers=HEADERS, timeout=20)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        page_text = soup.get_text("\n", strip=True)

        # ---------- DESCRIPTION ----------
        description = ""

        desc_heading = soup.find(
            lambda tag: tag.name in ["h2", "h3"]
            and "Description" in tag.get_text()
        )

        if desc_heading:
            desc_paragraph = desc_heading.find_next("p")

            if desc_paragraph:
                description = desc_paragraph.get_text(strip=True)

        # ---------- JOB LEVEL ----------
        job_level = ""

        job_heading = soup.find(
            lambda tag: tag.name in ["h2", "h3"]
            and "Job levels" in tag.get_text()
        )

        if job_heading:
            job_text = job_heading.find_next("p")

            if job_text:
                job_level = job_text.get_text(strip=True)

        # ---------- LANGUAGES ----------
        languages = ""

        lang_heading = soup.find(
            lambda tag: tag.name in ["h2", "h3"]
            and "Languages" in tag.get_text()
        )

        if lang_heading:
            lang_text = lang_heading.find_next("p")

            if lang_text:
                languages = lang_text.get_text(strip=True)

        # ---------- ASSESSMENT LENGTH ----------
        assessment_length = ""

        length_heading = soup.find(
            lambda tag: tag.name in ["h2", "h3"]
            and "Assessment length" in tag.get_text()
        )

        if length_heading:
            length_text = length_heading.find_next("p")

            if length_text:
                assessment_length = length_text.get_text(strip=True)

        # ---------- REMOTE TESTING ----------
        remote_testing = "No"

        if "Remote Testing" in page_text:
            remote_testing = "Yes"

        # ---------- TEST TYPE ----------
        test_type = ""

        test_type_section = soup.find(string=lambda text: text and "Test Type" in text)

        if test_type_section:
            test_type = test_type_section.strip()

        data = {
            "name": assessment["name"],
            "url": url,
            "description": description,
            "job_level": job_level,
            "languages": languages,
            "assessment_length": assessment_length,
            "remote_testing": remote_testing,
            "test_type": test_type
        }

        print(f"Scraped: {assessment['name']}")

        return data

    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None


def main():

    print("Fetching catalog links...\n")

    assessments = get_catalog_links()

    print(f"Found {len(assessments)} assessments\n")

    all_data = []

    for assessment in assessments:

        details = scrape_assessment_details(assessment)

        if details:
            all_data.append(details)

        # polite delay
        time.sleep(1)

    # SAVE JSON
    with open("catalog.json", "w", encoding="utf-8") as f:
        json.dump(all_data, f, indent=4, ensure_ascii=False)

    print("\nSaved data to catalog.json")


if __name__ == "__main__":
    main()