"""
Resolve the current DATARUN value.

Priority:
  1. ``DATARUN`` environment variable (allows one-off overrides)
  2. ``Data/.datarun`` file written automatically by ``scrape.py``
  3. Auto-detect from the most recent ``idaho_bills_enriched_*.jsonl`` file
     in the ``Data/`` directory (enables dashboard-only deployments)

``scrape.py`` writes the date string to ``Data/.datarun`` at the end of each
successful run so that subsequent pipeline steps can pick it up without
requiring the user to manually export an environment variable.

When neither the environment variable nor the ``.datarun`` file is available
(e.g. a fresh clone used only for the Streamlit dashboard), the resolver
falls back to scanning ``Data/`` for enriched JSONL files and extracts the
date string from the filename.
"""

import glob
import os
import re
import sys

DATA_DIR = "Data"
DATARUN_FILE = os.path.join(DATA_DIR, ".datarun")

_ENRICHED_PATTERN = os.path.join(DATA_DIR, "idaho_bills_enriched_*.jsonl")
_ENRICHED_RE = re.compile(r"idaho_bills_enriched_(\d{2}_\d{2}_\d{4})\.jsonl$")


def _detect_datarun_from_files():
    """Scan ``Data/`` for enriched JSONL files and return the latest date string."""
    matches = []
    for path in glob.glob(_ENRICHED_PATTERN):
        m = _ENRICHED_RE.search(os.path.basename(path))
        if m:
            matches.append(m.group(1))
    if matches:
        # Sort by (year, month, day) descending so the most recent run wins.
        # Date format is MM_DD_YYYY.
        matches.sort(
            key=lambda d: (int(d.split("_")[2]), int(d.split("_")[0]), int(d.split("_")[1])),
            reverse=True,
        )
        return matches[0]
    return None


def get_datarun():
    """Return the current datarun string, or exit with an error message."""
    datarun = os.getenv("DATARUN")
    if datarun:
        return datarun.strip()

    if os.path.isfile(DATARUN_FILE):
        with open(DATARUN_FILE, "r") as f:
            datarun = f.read().strip()
        if datarun:
            return datarun

    datarun = _detect_datarun_from_files()
    if datarun:
        return datarun

    print(
        "Could not determine DATARUN.\n"
        "Either set the DATARUN environment variable, run scrape.py first\n"
        f"(which writes the value to {DATARUN_FILE}), or ensure\n"
        "idaho_bills_enriched_*.jsonl files exist in Data/."
    )
    sys.exit(1)


def save_datarun(value):
    """Persist *value* to the datarun file so later steps can find it."""
    os.makedirs(os.path.dirname(DATARUN_FILE), exist_ok=True)
    with open(DATARUN_FILE, "w") as f:
        f.write(value + "\n")
