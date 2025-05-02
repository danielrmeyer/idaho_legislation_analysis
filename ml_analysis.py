import os
import sys
import json
import openai
import pandas as pd
from pathlib import Path
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from openai import APIError, RateLimitError, Timeout, APIConnectionError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_fixed,
    RetryError,
    retry_if_exception_type,
)

from ratelimit import limits, sleep_and_retry


def find_null_json_files(directory):
    null_files = []

    for filename in os.listdir(directory):
        if filename.endswith(".json"):
            filepath = os.path.join(directory, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = json.load(f)
                    if content is None:
                        null_files.append(os.path.join(directory, filename))
            except json.JSONDecodeError:
                print(f"Invalid JSON in file: {filename}")
            except Exception as e:
                print(f"Error reading file {filename}: {e}")

    return null_files


@retry(
    retry=retry_if_exception_type((RateLimitError, APIError, Timeout, APIConnectionError)),
    wait=wait_exponential(multiplier=1, min=4, max=60),
    stop=stop_after_attempt(6),
    reraise=True,
)
@sleep_and_retry
@limits(calls=10, period=1)
def analyze_legislation_html(local_html_path, model="gpt-4o"):
    """
    Reads an HTML file containing proposed legislation (with <u> and <s> tags
    indicating additions/strikeouts) and sends it to the OpenAI ChatCompletion API.

    The system prompt instructs the model to:
      - Act as a legislative analyst,
      - Return ONLY valid JSON listing potential constitutional issues,
      - Use <u> and <s> tags to interpret text additions or deletions.

    Returns a Python object parsed from the JSON response:
      e.g., [ { "issue": "...", "references": "..." }, ... ]

    If there are no issues, the model should return [].
    """

    # 1) Read the entire HTML from file
    with open(local_html_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    system_message = """
You are a legislative analyst. You will receive HTML text representing a proposed bill.
Text that is being added to existing law is wrapped in <u>...</u>.
Text that is being removed from existing law is wrapped in <s>...</s>.
In some cases a new chapter is being added and and everything is an addition but nothing is wrapped in <u>...</u>.

Your task:
1) Identify potential constitutional issues with the proposed legislation.
2) Return ONLY valid JSON.
3) Do NOT include any extra text, markdown, or explanations—just the JSON.
4) The JSON should be an array of objects, each with the following keys:
   "issue"        (short label of the constitutional concern),
   "references"   (constitutional provisions, e.g. "U.S. Const. amend. I"),
   "explanation"  (a short paragraph explaining the concern).

Example:
[
  {
    "issue": "First Amendment concern",
    "references": "U.S. Const. amend. I",
    "explanation": "This portion of the bill may impinge on freedom of speech because..."
  },
  {
    "issue": "Right to due process",
    "references": "Fifth and Fourteenth Amendments",
    "explanation": "The new section sets procedures that could violate fundamental fairness..."
  }
]

If there are no issues, return an empty array: []
"""

    user_message = (
        "Analyze the following HTML legislative text for possible constitutional conflicts.\n"
        "Remember: return ONLY valid JSON with the described format.\n\n"
        f"HTML Document:\n{html_content}"
    )

    try:
        response = openai.chat.completions.create(
            model=model,  # or "gpt-4", depending on your preference
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
            ],
            temperature=0,
        )
    except Exception as e:
        print("Error calling OpenAI API:", e)
        return None

    reply_content = response.choices[0].message.content

    try:
        parsed_json = json.loads(reply_content)
        return parsed_json
    except json.JSONDecodeError:
        # The model might occasionally not return valid JSON. You might want to handle or retry.
        print("OpenAI returned invalid JSON:\n", reply_content)
        return None

datarun = os.getenv("DATARUN")

if datarun is None:
    print("You need to set the DATARUN environment variable")
    sys.exit(1)

df = pd.read_csv("Data/{datarun}/idaho_bills_{datarun}.csv".format(datarun=datarun))

for input_pdf_path in df["local_pdf_path"]:
    print("processing {input_pdf_path}".format(input_pdf_path=input_pdf_path))
    input_html_path = input_pdf_path.replace(".pdf", ".html")
    issue_data = analyze_legislation_html(input_html_path)
    output_json_path = input_pdf_path.replace(".pdf", ".json")
    with open(output_json_path, "w") as f:
        json.dump(issue_data, f, indent=4)


# Find list of failed analyses
directory_path = "Data/{datarun}".format(datarun=datarun)
null_file_list = find_null_json_files(directory_path)
print("Files with null content:", null_file_list)

pdf_paths = [p.replace('.json', '.pdf') for p in null_file_list]
un_analyzed_df = df[df["local_pdf_path"].isin(pdf_paths)]

for input_pdf_path in un_analyzed_df["local_pdf_path"]:
    print("processing {input_pdf_path}".format(input_pdf_path=input_pdf_path))
    input_html_path = input_pdf_path.replace(".pdf", ".html")
    issue_data = analyze_legislation_html(input_html_path, model="gpt-4o-mini")
    output_json_path = input_pdf_path.replace(".pdf", ".json")
    with open(output_json_path, "w") as f:
        json.dump(issue_data, f, indent=4)
    

null_file_list = find_null_json_files(directory_path)
print("Files with null content:", null_file_list)


def load_json_data(pdf_path_str):
    json_path = Path(pdf_path_str).with_suffix('.json')
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    except json.JSONDecodeError:
        return {"error": "Invalid JSON"}

# Apply the function to create a new column
df["json_data"] = df["local_pdf_path"].apply(load_json_data)

df.to_csv(
    os.path.join(
        directory_path, "idaho_bills_enriched_{current_date}.csv".format(current_date=datarun)
    ),
    index=False,
)