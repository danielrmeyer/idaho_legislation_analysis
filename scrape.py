"""
Scrape Idaho legislative bill data from legislature.idaho.gov.

Downloads bill metadata (number, title, status, sponsor) and the
corresponding PDF files into a date-stamped ``Data/<DATARUN>/`` directory.
The datarun value is persisted to ``Data/.datarun`` so that downstream
pipeline steps can find it automatically.

Usage::

    uv run python scrape.py
"""

import os
import time
from datetime import datetime

import pandas as pd
import requests
from bs4 import BeautifulSoup
from ratelimit import limits, sleep_and_retry
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from config import save_datarun

BASE_URL = "https://legislature.idaho.gov"
LEGISLATION_URL = f"{BASE_URL}/sessioninfo/2026/legislation/"


def write_soup_to_file(soup, filename):
    """Write prettified BeautifulSoup HTML to *filename*."""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(soup.prettify())


@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=4, max=30),
    retry=retry_if_exception_type(requests.exceptions.RequestException),
)
@sleep_and_retry
@limits(calls=10, period=1)
def parse_detail_page(session, detail_url):
    """Fetch a bill's detail page and return the sponsor name."""
    full_url = BASE_URL + detail_url

    resp = session.get(full_url, timeout=(5, 10))
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    bill_table = soup.find("table", class_="bill-table")

    row = bill_table.find("tr")
    cells = row.find_all("td")
    sponsor_text = cells[2].get_text(strip=True)

    return sponsor_text.replace("by ", "").strip()


@sleep_and_retry
@limits(calls=10, period=1)
@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=4, max=30),
    retry=retry_if_exception_type(requests.exceptions.RequestException),
)
def download_pdf(session, url, dir_path):
    """Download a PDF from *url* into *dir_path* and return the local path."""
    response = session.get(url, stream=True, timeout=(5, 10))
    response.raise_for_status()

    pdf_local_path = os.path.join(dir_path, url.split("/")[-1])

    with open(pdf_local_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    print(f"Downloaded PDF from {url} to {pdf_local_path}")
    return pdf_local_path


@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=4, max=30),
    retry=retry_if_exception_type(requests.exceptions.RequestException),
)
@sleep_and_retry
@limits(calls=10, period=1)
def scrape_idaho_legislation(session, url):
    """Scrape the Idaho legislation index page and return a list of bill records."""
    response = session.get(url, timeout=(5, 10))
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    mini_tables = soup.find_all("table", class_="mini-data-table")[2:]

    results = []
    for table in mini_tables:
        bill_row = table.find("tr", id=lambda x: x and x.startswith("bill"))
        if not bill_row:
            continue

        cells = bill_row.find_all("td")
        if len(cells) < 4:
            continue

        link_tag = cells[0].find("a")
        detail_link = link_tag["href"]
        bill_number = detail_link.split("/")[-1]
        bill_title = cells[1].get_text(strip=True) if len(cells) > 1 else ""
        pdf_url = (
            f"{BASE_URL}/wp-content/uploads/sessioninfo/2026"
            f"/legislation/{bill_number}.pdf"
        )
        status = cells[3].get_text(strip=True)

        results.append([bill_number, bill_title, status, detail_link, pdf_url])

    return results


def main():
    """Run the full scrape pipeline: index → sponsors → PDFs → CSV."""
    datarun = os.getenv("DATARUN", "").strip()
    if not datarun:
        datarun = datetime.now().strftime("%m_%d_%Y")
    save_datarun(datarun)

    dir_path = os.path.join("Data", datarun)
    os.makedirs(dir_path, exist_ok=True)

    session = requests.Session()
    try:
        bill_data = scrape_idaho_legislation(session, LEGISLATION_URL)

        bill_df = pd.DataFrame(
            bill_data,
            columns=[
                "bill_number", "bill_title", "bill_status",
                "detail_link", "pdf_url",
            ],
        )

        sponsors = []
        for link in bill_df["detail_link"]:
            sponsor = parse_detail_page(session, link) if link else ""
            print(sponsor)
            sponsors.append(sponsor)
            time.sleep(0.1)

        bill_df["sponsor"] = sponsors

        local_pdf_paths = []
        for pdf_url in bill_df["pdf_url"]:
            print(pdf_url)
            path = download_pdf(session, pdf_url, dir_path)
            local_pdf_paths.append(path)
            time.sleep(0.1)

        bill_df["local_pdf_path"] = local_pdf_paths

        bill_df.to_csv(
            os.path.join(dir_path, f"idaho_bills_{datarun}.csv"),
            index=False,
        )

        print(f"Scrape Successful.  Data directory: Data/{datarun}")
    finally:
        session.close()


if __name__ == "__main__":
    main()
