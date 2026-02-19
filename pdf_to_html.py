"""
Convert scraped Idaho legislation PDFs to HTML, preserving underline and
strikethrough formatting.

Two-step pipeline:
  1. PDF → DOCX using one of two modes:
     - pdf2docx (local, no external API)
     - Adobe PDF Services API
  2. DOCX → HTML using Mammoth with a style map that converts
     underline to <u> and strikethrough to <s>

These tags match the conventions used by the Idaho Legislature to mark
additions (underline) and deletions (strikethrough) in bills.  HTML
entities (&amp; &lt; &gt; &quot;) are properly escaped by Mammoth.

Usage:
    uv run python scrape.py      # writes Data/.datarun automatically
    export PDF_CONVERSION_MODE=pdf2docx  # or: adobe
    uv run python pdf_to_html.py
"""

import os
import time

import mammoth
import pandas as pd
from pdf2docx import Converter

from config import get_datarun

SUPPORTED_MODES = {"pdf2docx", "adobe"}
DEFAULT_MODE = "pdf2docx"


def get_conversion_mode():
    """Return the configured PDF conversion mode."""
    mode = os.getenv("PDF_CONVERSION_MODE", DEFAULT_MODE).strip().lower()
    if mode not in SUPPORTED_MODES:
        raise SystemExit(
            "Invalid PDF_CONVERSION_MODE. "
            "Use one of: pdf2docx, adobe."
        )
    return mode


def pdf_to_docx_local(pdf_path, docx_path):
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


def init_adobe_pdf_services():
    """Initialize Adobe PDF Services client and related classes.

    Requires:
      - PDF_SERVICES_CLIENT_ID
      - PDF_SERVICES_CLIENT_SECRET
      - pdfservices-sdk package installed
    """
    client_id = os.getenv("PDF_SERVICES_CLIENT_ID", "").strip()
    client_secret = os.getenv("PDF_SERVICES_CLIENT_SECRET", "").strip()

    if not client_id or not client_secret:
        raise SystemExit(
            "Adobe mode requires PDF_SERVICES_CLIENT_ID and "
            "PDF_SERVICES_CLIENT_SECRET environment variables."
        )

    try:
        from adobe.pdfservices.operation.auth.service_principal_credentials import (
            ServicePrincipalCredentials,
        )
        from adobe.pdfservices.operation.pdf_services import PDFServices
        from adobe.pdfservices.operation.pdf_services_media_type import (
            PDFServicesMediaType,
        )
        from adobe.pdfservices.operation.pdfjobs.jobs.export_pdf_job import ExportPDFJob
        from adobe.pdfservices.operation.pdfjobs.params.export_pdf.export_pdf_params import (
            ExportPDFParams,
        )
        from adobe.pdfservices.operation.pdfjobs.params.export_pdf.export_pdf_target_format import (
            ExportPDFTargetFormat,
        )
        from adobe.pdfservices.operation.pdfjobs.result.export_pdf_result import (
            ExportPDFResult,
        )
    except ImportError as exc:
        raise SystemExit(
            "Adobe mode requires the `pdfservices-sdk` package. "
            "Install it first, e.g. `uv run python -m pip install pdfservices-sdk`."
        ) from exc

    credentials = ServicePrincipalCredentials(
        client_id=client_id,
        client_secret=client_secret,
    )

    return {
        "pdf_services": PDFServices(credentials=credentials),
        "PDFServicesMediaType": PDFServicesMediaType,
        "ExportPDFJob": ExportPDFJob,
        "ExportPDFParams": ExportPDFParams,
        "ExportPDFTargetFormat": ExportPDFTargetFormat,
        "ExportPDFResult": ExportPDFResult,
    }


def pdf_to_docx_adobe(pdf_path, docx_path, adobe_ctx, max_attempts=3):
    """Convert PDF to DOCX using Adobe PDF Services with basic retries."""
    pdf_services = adobe_ctx["pdf_services"]

    for attempt in range(1, max_attempts + 1):
        try:
            with open(pdf_path, "rb") as f:
                input_stream = f.read()

            input_asset = pdf_services.upload(
                input_stream=input_stream,
                mime_type=adobe_ctx["PDFServicesMediaType"].PDF,
            )

            export_pdf_params = adobe_ctx["ExportPDFParams"](
                target_format=adobe_ctx["ExportPDFTargetFormat"].DOCX
            )
            export_pdf_job = adobe_ctx["ExportPDFJob"](
                input_asset=input_asset,
                export_pdf_params=export_pdf_params,
            )

            location = pdf_services.submit(export_pdf_job)
            pdf_services_response = pdf_services.get_job_result(
                location, adobe_ctx["ExportPDFResult"]
            )

            result_asset = pdf_services_response.get_result().get_asset()
            stream_asset = pdf_services.get_content(result_asset)

            with open(docx_path, "wb") as output_file:
                output_file.write(stream_asset.get_input_stream())
            return
        except Exception:
            if attempt == max_attempts:
                raise
            time.sleep(1)


# ---------------------------------------------------------------------------
# Main script
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    datarun = get_datarun()
    mode = get_conversion_mode()

    print(f"PDF conversion mode: {mode}")

    adobe_ctx = None
    if mode == "adobe":
        adobe_ctx = init_adobe_pdf_services()

    df = pd.read_csv(
        "Data/{datarun}/idaho_bills_{datarun}.csv".format(datarun=datarun)
    )

    for input_pdf_path in df["local_pdf_path"]:
        docx_path = input_pdf_path.replace(".pdf", ".docx")
        html_path = input_pdf_path.replace(".pdf", ".html")

        print(f"Converting {input_pdf_path} -> {docx_path}")
        if mode == "pdf2docx":
            pdf_to_docx_local(input_pdf_path, docx_path)
        else:
            pdf_to_docx_adobe(input_pdf_path, docx_path, adobe_ctx)

        print(f"Converting {docx_path} -> {html_path}")
        docx_to_html(docx_path, html_path)

        print(f"  Done: {html_path}")
