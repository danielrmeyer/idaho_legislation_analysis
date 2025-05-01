import logging
import os
from datetime import datetime
import mammoth
import pandas as pd
import sys

from adobe.pdfservices.operation.auth.service_principal_credentials import (
    ServicePrincipalCredentials,
)
from adobe.pdfservices.operation.exception.exceptions import (
    ServiceApiException,
    ServiceUsageException,
    SdkException,
)
from adobe.pdfservices.operation.io.cloud_asset import CloudAsset
from adobe.pdfservices.operation.io.stream_asset import StreamAsset
from adobe.pdfservices.operation.pdf_services import PDFServices
from adobe.pdfservices.operation.pdf_services_media_type import PDFServicesMediaType
from adobe.pdfservices.operation.pdfjobs.jobs.export_pdf_job import ExportPDFJob
from adobe.pdfservices.operation.pdfjobs.params.export_pdf.export_pdf_params import (
    ExportPDFParams,
)
from adobe.pdfservices.operation.pdfjobs.params.export_pdf.export_pdf_target_format import (
    ExportPDFTargetFormat,
)
from adobe.pdfservices.operation.pdfjobs.result.export_pdf_result import ExportPDFResult

from ratelimit import limits, sleep_and_retry

from tenacity import (
    retry,
    stop_after_attempt,
    wait_fixed,
    RetryError,
    retry_if_exception_type,
)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_fixed(1),
    retry=retry_if_exception_type(SdkException),
)
@sleep_and_retry
@limits(calls=10, period=1)
def pdf_to_docx(input_stream):
    input_asset = pdf_services.upload(
        input_stream=input_stream, mime_type=PDFServicesMediaType.PDF
    )

    # Create parameters for the job
    export_pdf_params = ExportPDFParams(target_format=ExportPDFTargetFormat.DOCX)

    # Creates a new job instance
    export_pdf_job = ExportPDFJob(
        input_asset=input_asset, export_pdf_params=export_pdf_params
    )

    # Submit the job and gets the job result
    location = pdf_services.submit(export_pdf_job)
    pdf_services_response = pdf_services.get_job_result(location, ExportPDFResult)

    # Get content from the resulting asset(s)
    result_asset: CloudAsset = pdf_services_response.get_result().get_asset()
    stream_asset: StreamAsset = pdf_services.get_content(result_asset)

    # output_path = input_pdf_path.replace('.pdf', '.docx')

    return stream_asset.get_input_stream()


def docx_to_html_mammoth(docx_filename, html_filename):
    """
    Convert a .docx to .html using the Mammoth library.
    Saves HTML result to 'html_filename'.
    """

    docx_abs = os.path.abspath(docx_filename)
    html_abs = os.path.abspath(html_filename)

    style_map = """u => u
strike => s"
"""

    with open(docx_abs, "rb") as docx_file:
        # Mammoth returns an object with 'value' for the raw HTML
        result = mammoth.convert_to_html(docx_file, style_map=style_map)
        html_content = result.value  # The generated HTML as a string

    # Write HTML to disk
    with open(html_abs, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"DOCX converted to HTML successfully: {html_abs}")


credentials = ServicePrincipalCredentials(
    client_id=os.getenv("PDF_SERVICES_CLIENT_ID"),
    client_secret=os.getenv("PDF_SERVICES_CLIENT_SECRET"),
)

datarun = os.getenv("DATARUN")

if datarun is None:
    print("You need to set the DATARUN environment variable")
    sys.exit(1)

pdf_services = PDFServices(credentials=credentials)

df = pd.read_csv("Data/{datarun}/idaho_bills_{datarun}.csv".format(datarun=datarun))

for input_pdf_path in df["local_pdf_path"]:
    print(input_pdf_path)

    with open(input_pdf_path, "rb") as f:
        input_stream = f.read()

    output_stream = pdf_to_docx(input_stream)
    output_path = input_pdf_path.replace(".pdf", ".docx")

    with open(output_path, "wb") as file:
        file.write(output_stream)


for input_pdf_path in df["local_pdf_path"]:
    input_docx_path = input_pdf_path.replace(".pdf", ".docx")
    print(input_docx_path)
    output_html_path = input_pdf_path.replace(".pdf", ".html")
    docx_to_html_mammoth(input_docx_path, output_html_path)
