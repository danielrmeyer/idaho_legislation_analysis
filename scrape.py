import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import time

from datetime import datetime


current_date = datetime.now().strftime("%m_%d_%Y")

dir_path = os.path.join("Data", current_date)
os.makedirs(dir_path, exist_ok=True)


def write_soup_to_file(soup, filename):
    with open(filename, "w", encoding="utf-8") as f:
        f.write(soup.prettify())


def parse_detail_page(detail_url):
    base_url = "https://legislature.idaho.gov"
    full_url = base_url + detail_url

    resp = requests.get(full_url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    bill_table = soup.find("table", class_="bill-table")

    row = bill_table.find("tr")
    cells = row.find_all("td")

    sponsor_text = cells[2].get_text(strip=True)

    sponsor = sponsor_text.replace("by ", "").strip()

    return sponsor


def download_pdf(url):
    response = requests.get(url, stream=True)
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

        bill_number = cells[0].get_text(strip=True)
        link_tag = cells[0].find("a")
        detail_link = link_tag["href"]

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
    time.sleep(0.1)  # TODO rate limit

bill_df["sponsor"] = sponsors


local_pdf_paths = []
for pdf_url in bill_df["pdf_url"]:
    print(pdf_url)
    path = download_pdf(pdf_url)  # TODO Add try retry with backoff
    local_pdf_paths.append(path)
    time.sleep(0.1)  # TODO replace with rate limiter

bill_df["local_pdf_path"] = local_pdf_paths

bill_df.to_csv(
    os.path.join(
        dir_path, "idaho_bill_{current_date}.csv".format(current_date=current_date)
    ),
    index=False,
)
