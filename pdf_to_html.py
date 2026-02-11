"""
Convert scraped Idaho legislation PDFs to HTML, preserving underline and
strikethrough formatting.

Two-step pipeline:
  1. PDF → DOCX using pdf2docx (local, no external API)
  2. DOCX → HTML using Mammoth with a style map that converts
     underline to <u> and strikethrough to <s>

These tags match the conventions used by the Idaho Legislature to mark
additions (underline) and deletions (strikethrough) in bills.  HTML
entities (&amp; &lt; &gt; &quot;) are properly escaped by Mammoth.

Usage:
    uv run python scrape.py      # writes Data/.datarun automatically
    uv run python pdf_to_html.py
"""

import os

import mammoth
import pandas as pd
from pdf2docx import Converter

from config import get_datarun


def pdf_to_docx(pdf_path, docx_path):
    """Convert a PDF file to DOCX using pdf2docx.

    Preserves underline and strikethrough formatting as native DOCX runs.
    """
    cv = Converter(pdf_path)
    cv.convert(docx_path)
    cv.close()


def docx_to_html(docx_path, html_path):
    """Convert a DOCX file to HTML using Mammoth.

    Maps underline runs to <u> tags and strikethrough runs to <s> tags.
    Mammoth automatically escapes HTML entities in text content.
    """
    style_map = """u => u
strike => s
"""

    with open(docx_path, "rb") as docx_file:
        result = mammoth.convert_to_html(docx_file, style_map=style_map)
        html_content = result.value

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)


# ---------------------------------------------------------------------------
# Main script
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    datarun = get_datarun()

    df = pd.read_csv(
        "Data/{datarun}/idaho_bills_{datarun}.csv".format(datarun=datarun)
    )

    for input_pdf_path in df["local_pdf_path"]:
        docx_path = input_pdf_path.replace(".pdf", ".docx")
        html_path = input_pdf_path.replace(".pdf", ".html")

        print(f"Converting {input_pdf_path} -> {docx_path}")
        pdf_to_docx(input_pdf_path, docx_path)

        print(f"Converting {docx_path} -> {html_path}")
        docx_to_html(docx_path, html_path)

        print(f"  Done: {html_path}")
