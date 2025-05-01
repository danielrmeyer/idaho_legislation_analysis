import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import time

from tenacity import retry, stop_after_attempt, wait_fixed, RetryError, retry_if_exception_type
from datetime import datetime
from ratelimit import limits, sleep_and_retry

current_date = datetime.now().strftime("%m_%d_%Y")

dir_path = os.path.join("Data", current_date)
os.makedirs(dir_path, exist_ok=True)


def write_soup_to_file(soup, filename):
    with open(filename, "w", encoding="utf-8") as f:
        f.write(soup.prettify())

@retry(stop=stop_after_attempt(3), wait=wait_fixed(1), retry=retry_if_exception_type(requests.exceptions.RequestException))
@sleep_and_retry
@limits(calls=10, period=1)
def parse_detail_page(detail_url):
    base_url = "https://legislature.idaho.gov"
    full_url = base_url + detail_url

    resp = requests.get(full_url, timeout=(3, 5))
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    bill_table = soup.find("table", class_="bill-table")

    row = bill_table.find("tr")
    cells = row.find_all("td")

    sponsor_text = cells[2].get_text(strip=True)

    sponsor = sponsor_text.replace("by ", "").strip()

    return sponsor


@sleep_and_retry
@limits(calls=10, period=1)
@retry(stop=stop_after_attempt(3), wait=wait_fixed(1), retry=retry_if_exception_type(requests.exceptions.RequestException))
def download_pdf(url):
    response = requests.get(url, stream=True, timeout=(3,5))
    response.raise_for_status()

    pdf_local_path = os.path.join(dir_path, url.split("/")[-1])

    with open(pdf_local_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    print(f"Downloaded PDF from {pdf_url} to {pdf_local_path}")
    return pdf_local_path


def scrape_idaho_legislation(url):
    response = requests.get(url)
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
        bill_number = detail_link.split('/')[-1]
        bill_title = cells[1].get_text(strip=True) if len(cells) > 1 else ""
        pdf_url = f"https://legislature.idaho.gov/wp-content/uploads/sessioninfo/2025/legislation/{bill_number}.pdf"
        status = cells[3].get_text(strip=True)

        results.append([bill_number, bill_title, status, detail_link, pdf_url])

    return results


url = "https://legislature.idaho.gov/sessioninfo/2025/legislation/"
bill_data = scrape_idaho_legislation(url)

bill_df = pd.DataFrame(
    bill_data,
    columns=["bill_number", "bill_title", "bill_status", "detail_link", "pdf_url"],
)

sponsors = []
for link in bill_df["detail_link"]:
    sponsor = parse_detail_page(link) if link else ""
    print(sponsor)
    sponsors.append(sponsor)
    time.sleep(0.1)

bill_df["sponsor"] = sponsors


local_pdf_paths = []
for pdf_url in bill_df["pdf_url"]:
    print(pdf_url)
    path = download_pdf(pdf_url)
    local_pdf_paths.append(path)
    time.sleep(0.1)

bill_df["local_pdf_path"] = local_pdf_paths

bill_df.to_csv(
    os.path.join(
        dir_path, "idaho_bill_{current_date}.csv".format(current_date=current_date)
    ),
    index=False,
)

print(f"""Scrape Successful.  Please, 'export DATARUN={current_date}'""")