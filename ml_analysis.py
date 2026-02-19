"""
Analyse Idaho legislation HTML files for potential constitutional issues
using the OpenAI ChatCompletion API.

Two-pass approach:
  1. Analyse every bill with the configured primary model.
  2. Re-analyse any bills that returned ``null`` with the configured retry model.

Produces two JSONL files in ``Data/``:
  - ``idaho_bills_enriched_<DATARUN>.jsonl`` — bills with detected issues
  - ``idaho_bills_failed_<DATARUN>.jsonl``   — bills where analysis failed

Usage::

    uv run python ml_analysis.py
"""

import json
import os
from pathlib import Path

import openai
import pandas as pd
from openai import (
    APIConnectionError,
    APIError,
    BadRequestError,
    RateLimitError,
    Timeout,
)
from ratelimit import limits, sleep_and_retry
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from config import get_datarun

PRIMARY_MODEL = os.getenv("OPENAI_PRIMARY_MODEL", "gpt-5.1")
RETRY_MODEL = os.getenv("OPENAI_RETRY_MODEL", "gpt-5-mini")
# High-context fallback for context-length failures.
LONG_CONTEXT_MODEL = os.getenv("OPENAI_LONG_CONTEXT_MODEL", "gpt-4.1-mini")


def _supports_explicit_temperature(model_name):
    """Return True when the model supports explicitly setting temperature=0."""
    name = (model_name or "").strip().lower()
    # GPT-5 chat models require default temperature.
    return not name.startswith("gpt-5")


def _chat_completion(model, messages):
    """Call chat completions with model-specific parameter compatibility."""
    kwargs = {
        "model": model,
        "messages": messages,
    }
    if _supports_explicit_temperature(model):
        kwargs["temperature"] = 0
    return openai.chat.completions.create(**kwargs)


def find_null_json_files(directory):
    """Return paths of JSON files in *directory* whose content is ``null``."""
    null_files = []
    for filename in os.listdir(directory):
        if filename.endswith(".json"):
            filepath = os.path.join(directory, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = json.load(f)
                    if content is None:
                        null_files.append(filepath)
            except json.JSONDecodeError:
                print(f"Invalid JSON in file: {filename}")
            except Exception as e:
                print(f"Error reading file {filename}: {e}")
    return null_files


@retry(
    retry=retry_if_exception_type(
        (RateLimitError, APIError, Timeout, APIConnectionError)
    ),
    wait=wait_exponential(multiplier=1, min=4, max=60),
    stop=stop_after_attempt(6),
    reraise=True,
)
@sleep_and_retry
@limits(calls=10, period=1)
def analyze_legislation_html(local_html_path, model=PRIMARY_MODEL):
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
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message},
    ]

    try:
        response = _chat_completion(model=model, messages=messages)
    except RateLimitError as e:
        err_text = str(e).lower()
        if "insufficient_quota" in err_text or "exceeded your current quota" in err_text:
            raise SystemExit(
                "OpenAI quota exceeded. Top up billing/credits and rerun ml_analysis.py."
            )
        raise
    except BadRequestError as e:
        # Keep strongest model first; only fall back when input is too large.
        err_text = str(e).lower()
        is_context_error = (
            "context_length_exceeded" in err_text
            or "maximum context length" in err_text
            or "too many tokens" in err_text
        )
        if is_context_error and LONG_CONTEXT_MODEL and model != LONG_CONTEXT_MODEL:
            print(
                f"Context length exceeded for {local_html_path} on {model}; "
                f"retrying with {LONG_CONTEXT_MODEL}."
            )
            try:
                response = _chat_completion(model=LONG_CONTEXT_MODEL, messages=messages)
            except Exception as fallback_error:
                print("Error calling OpenAI API after context fallback:", fallback_error)
                return None
        else:
            print("Error calling OpenAI API:", e)
            return None
    except Exception as e:
        print("Error calling OpenAI API:", e)
        return None

    reply_content = response.choices[0].message.content

    try:
        parsed_json = json.loads(reply_content)
        return parsed_json
    except json.JSONDecodeError:
        print("OpenAI returned invalid JSON:\n", reply_content)
        return None


def load_json_data(pdf_path_str):
    """Load the JSON analysis result for a bill, keyed by its PDF path."""
    json_path = Path(pdf_path_str).with_suffix(".json")
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    except json.JSONDecodeError:
        return {"error": "Invalid JSON"}


def _analyse_bills(df, model):
    """Run OpenAI analysis on every bill in *df* and write per-bill JSON."""
    for input_pdf_path in df["local_pdf_path"]:
        print(f"processing {input_pdf_path}")
        input_html_path = input_pdf_path.replace(".pdf", ".html")
        issue_data = analyze_legislation_html(input_html_path, model=model)
        output_json_path = input_pdf_path.replace(".pdf", ".json")
        with open(output_json_path, "w") as f:
            json.dump(issue_data, f, indent=4)


def main():
    """Run the full two-pass analysis pipeline and write enriched JSONL."""
    datarun = get_datarun()
    directory_path = f"Data/{datarun}"

    df = pd.read_csv(f"{directory_path}/idaho_bills_{datarun}.csv")

    print(
        f"Pass 1 model: {PRIMARY_MODEL} | "
        f"Pass 2 model: {RETRY_MODEL} | "
        f"Context fallback model: {LONG_CONTEXT_MODEL}"
    )

    # Pass 1: analyze with strongest model first.
    _analyse_bills(df, model=PRIMARY_MODEL)

    # Re-analyze failures with a lower-cost backup model.
    null_file_list = find_null_json_files(directory_path)
    print("Files with null content:", null_file_list)

    pdf_paths = [p.replace(".json", ".pdf") for p in null_file_list]
    un_analyzed_df = df[df["local_pdf_path"].isin(pdf_paths)]

    _analyse_bills(un_analyzed_df, model=RETRY_MODEL)

    null_file_list = find_null_json_files(directory_path)
    print("Files with null content:", null_file_list)

    # Build enriched dataset
    df["json_data"] = df["local_pdf_path"].apply(load_json_data)

    none_df = df.loc[df["json_data"].isna()].copy()
    issues_df = df.loc[df["json_data"].apply(lambda x: isinstance(x, list))].copy()

    issues_df["issue_count"] = issues_df["json_data"].apply(len)
    none_df["issue_count"] = 0

    issues_df_sorted = issues_df.sort_values(
        by="issue_count", ascending=False,
    ).reset_index(drop=True)

    issues_df_sorted.to_json(
        os.path.join("Data", f"idaho_bills_enriched_{datarun}.jsonl"),
        index=False,
        orient="records",
        lines=True,
    )

    none_df.to_json(
        os.path.join("Data", f"idaho_bills_failed_{datarun}.jsonl"),
        index=False,
        orient="records",
        lines=True,
    )


if __name__ == "__main__":
    main()
