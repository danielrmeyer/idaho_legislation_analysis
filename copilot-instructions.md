# Copilot Instructions — Idaho Legislation Analysis

## Project Overview

This project scrapes legislative bills from the Idaho Legislature, converts PDFs to HTML preserving formatting (strikethroughs/underlines), analyzes them via OpenAI GPT-4o for constitutional issues, and presents results in an interactive dashboard.

## Technology Stack

- **Python**: 3.13+ (pinned in `.python-version`)
- **Package Manager**: uv (dependencies in `pyproject.toml`, lockfile in `uv.lock`)
- **Current Frontend**: Streamlit (being migrated to Django + Bootstrap)
- **Visualization**: Plotly Express
- **Data Format**: JSONL files read into Pandas DataFrames
- **APIs**: OpenAI (GPT-4o)
- **PDF Conversion**: pdf2docx (PDF→DOCX) + mammoth (DOCX→HTML) — fully local, no external API
- **Dev Tools**: black (formatter), ipython (REPL) — listed under `[dependency-groups] dev`

### Key Commands

```bash
uv sync                                          # install all deps + correct Python
uv run python scrape.py                          # step 1: scrape bills
uv run python pdf_to_html.py                     # step 2: convert PDFs
uv run python ml_analysis.py                     # step 3: OpenAI analysis
uv run streamlit run bill_data_explorer.py       # step 4: launch dashboard (current)
```

### Environment Variables

| Variable | Purpose |
|----------|---------|
| `DATARUN` | Optional override – date string like `04_30_2025`. When not set, the value is read from `Data/.datarun` (written automatically by `scrape.py`). |
| `OPENAI_API_KEY` | OpenAI API key for GPT-4o analysis |

## Data Pipeline

```
scrape.py → {DATARUN}/idaho_bills_{DATARUN}.csv
    ↓
pdf_to_html.py → {DATARUN}/*.docx, *.html (preserves strikethroughs/underlines)
    ↓
ml_analysis.py → {DATARUN}/*.json + Data/idaho_bills_enriched_{DATARUN}.jsonl
    ↓
Dashboard (bill_data_explorer.py + pages/) → reads enriched JSONL
```

## Data Models

### Bill Record (CSV → enriched JSONL)

| Field | Type | Description |
|-------|------|-------------|
| `bill_number` | string | e.g. "H0001" |
| `bill_title` | string | Full title |
| `bill_status` | string | Status code (see `pages/status_codes.py` for reference) |
| `detail_link` | string | URL to bill detail page |
| `pdf_url` | string | URL to bill PDF |
| `sponsor` | string | Bill sponsor name |
| `local_pdf_path` | string | Local path to downloaded PDF |
| `json_data` | JSON array | OpenAI analysis results (after ML step) |
| `issue_count` | int | Number of constitutional issues found |

### Constitutional Issue (inside `json_data` array)

```json
{
  "issue": "Short description of the constitutional issue",
  "references": "Relevant constitutional clauses/amendments",
  "explanation": "Detailed explanation of the potential conflict"
}
```

## Current File Structure

```
├── bill_data_explorer.py    # Main Streamlit app (multipage entrypoint)
├── pages/
│   ├── issue_type_histogram.py        # Plotly histogram of issue types
│   ├── issues_by_sponsor_histogram.py # Plotly histogram of issues by sponsor
│   └── status_codes.py               # Static reference table of status codes
├── utils.py                 # Shared helper: loads enriched JSONL with @st.cache_data
├── scrape.py                # Web scraper (requests + BeautifulSoup)
├── pdf_to_html.py           # PDF→DOCX (pdf2docx) → HTML (mammoth)
├── ml_analysis.py           # OpenAI GPT-4o constitutional analysis
├── Data/
│   ├── idaho_bills_enriched_04_30_2025.jsonl
│   └── idaho_bills_failed_04_30_2025.jsonl
├── .devcontainer/
│   └── devcontainer.json    # Codespaces/devcontainer config
├── pyproject.toml           # uv project config + dependencies
├── uv.lock                  # Deterministic lockfile
├── .python-version          # Python 3.13
├── .gitignore
├── README.md
└── LICENSE
```

## Streamlit → Django + Bootstrap Migration Guide

### Current Streamlit Usage by File

**`bill_data_explorer.py`** (main dashboard):
- `st.title()` — page title
- `st.selectbox()` — dropdown to filter by issue count
- `st.columns()` — two-column layout for bill cards
- `st.button()` — clickable bill cards
- `st.dialog()` — modal dialog showing bill details (issues, sponsor, status, links)
- `st.markdown()` — renders formatted text

**`pages/issue_type_histogram.py`**:
- `st.title()`, `st.slider()` — page title + minimum-count filter
- `st.plotly_chart()` — renders Plotly histogram
- `st.info()` — informational message

**`pages/issues_by_sponsor_histogram.py`**:
- `st.title()`, `st.slider()` — page title + minimum-count filter
- `st.plotly_chart()` — renders Plotly histogram
- `st.info()` — informational message

**`pages/status_codes.py`**:
- `st.title()`, `st.markdown()` — static reference table rendered as markdown

**`utils.py`**:
- `@st.cache_data` — caches JSONL loading (replace with Django cache or queryset)
- Returns a Pandas DataFrame

### Migration Mapping: Streamlit → Django + Bootstrap

| Streamlit | Django + Bootstrap Equivalent |
|-----------|-------------------------------|
| `st.title()` | `<h1>` in template |
| `st.markdown()` | Template with `|safe` filter or markdown lib |
| `st.selectbox()` | `<select>` form element or Django `ChoiceField` |
| `st.slider()` | `<input type="range">` or Bootstrap range slider |
| `st.columns()` | Bootstrap grid (`row` / `col-md-6`) |
| `st.button()` | `<a>` or `<button>` with Bootstrap classes |
| `st.dialog()` | Bootstrap modal component |
| `st.plotly_chart()` | Plotly.js in template (`plotly.offline.plot()` or JSON to frontend) |
| `st.info()` | Bootstrap alert (`alert-info`) |
| `@st.cache_data` | Django cache framework or database-backed queries |
| Streamlit multipage (pages/) | Django URL routing + views |

### Suggested Django App Structure

```
idaho_legislation/
├── manage.py
├── config/                  # Django project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── bills/                   # Main Django app
│   ├── models.py            # Bill, ConstitutionalIssue models
│   ├── views.py             # Dashboard, histograms, status codes views
│   ├── urls.py              # URL routing (replaces pages/ directory)
│   ├── admin.py             # Django admin for data management
│   ├── management/
│   │   └── commands/
│   │       ├── scrape_bills.py       # scrape.py as management command
│   │       ├── convert_pdfs.py       # pdf_to_html.py as management command
│   │       └── analyze_bills.py      # ml_analysis.py as management command
│   └── templates/
│       └── bills/
│           ├── base.html             # Bootstrap layout
│           ├── dashboard.html        # bill_data_explorer.py
│           ├── issue_histogram.html  # issue_type_histogram.py
│           ├── sponsor_histogram.html # issues_by_sponsor_histogram.py
│           └── status_codes.html     # status_codes.py
├── static/
│   ├── css/
│   └── js/
├── scrape.py                # Keep standalone scripts working too
├── pdf_to_html.py
└── ml_analysis.py
```

### Suggested Django Models

```python
class Bill(models.Model):
    bill_number = models.CharField(max_length=20, unique=True)
    bill_title = models.TextField()
    bill_status = models.CharField(max_length=50)
    detail_link = models.URLField()
    pdf_url = models.URLField()
    sponsor = models.CharField(max_length=200)
    local_pdf_path = models.CharField(max_length=500, blank=True)
    html_content = models.TextField(blank=True)
    datarun = models.CharField(max_length=20)  # e.g. "04_30_2025"
    created_at = models.DateTimeField(auto_now_add=True)

class ConstitutionalIssue(models.Model):
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name='issues')
    issue = models.TextField()
    references = models.TextField()
    explanation = models.TextField()
```

### Migration Notes

- **Pipeline scripts** (`scrape.py`, `pdf_to_html.py`, `ml_analysis.py`) do NOT use Streamlit and can remain as standalone scripts or become Django management commands.
- **Data loading** currently reads JSONL files into Pandas DataFrames. With Django, data should be loaded into the database via a management command or data migration.
- **Plotly charts** can be rendered server-side with `plotly.offline.plot()` returning HTML, or passed as JSON to Plotly.js on the frontend for interactivity.
- **Rate limiting** (`ratelimit`, `tenacity`) is used in scrape, PDF conversion, and ML analysis — keep these in management commands.
- The project is **stateless** by design — each pipeline step reads/writes files. Django adds database persistence.
- **No existing test infrastructure** — consider adding tests during the migration.
- **Dev container** (`.devcontainer/devcontainer.json`) will need updating: change the `postAttachCommand` from `uv run streamlit run ...` to `uv run python manage.py runserver`.

## Code Review Findings (2026-02-08)

Summary of the full repo review performed before the Django + Bootstrap migration.

### Structural improvements applied

- **`scrape.py`** and **`ml_analysis.py`** — all top-level script logic is now
  wrapped in `main()` with an `if __name__ == "__main__":` guard.  This makes
  the modules safely importable (e.g. for Django management commands or tests)
  without triggering side-effects on import.
- **`scrape.py`** — functions that formerly relied on module-level globals
  (`session`, `dir_path`) now receive them as explicit parameters.
  `BASE_URL` and `LEGISLATION_URL` are module-level constants.
- **`ml_analysis.py`** — duplicate `tenacity` import block removed; shared
  analysis loop extracted into `_analyse_bills()` helper to eliminate
  copy-paste between pass-1 (gpt-4o) and pass-2 (gpt-4o-mini).
  `load_json_data()` moved above `main()` so it can be imported separately.

### Bugs fixed

- **`ml_analysis.py`** line 203 (old) wrote the failed-bills JSONL to
  `"data/..."` (lowercase) instead of `"Data/..."`.  Fixed to `"Data"`.

### Pythonic style improvements

- All `.format()` string interpolation replaced with f-strings.
- Unused imports removed (`os` in `issue_type_histogram.py`, `RetryError` in
  `scrape.py`, `plotly.express` in `utils.py`).
- Stale filename comment in `issues_by_sponsor_histogram.py` corrected.
- Module-level docstrings added to every Python file.
- Function docstrings added where they aid understanding (helpers, public
  API); not added where the code is self-explanatory.
- Import order follows stdlib → third-party → local convention.

### Documentation improvements

- **`README.md`** rewritten with: prerequisites, quick-start block, detailed
  per-step instructions, project structure tree, environment-variable table,
  troubleshooting table, and future goals mentioning Django migration.
- **`copilot-instructions.md`** updated with this findings section.

### Django migration readiness

With `__main__` guards in place the three pipeline scripts (`scrape.py`,
`pdf_to_html.py`, `ml_analysis.py`) can be directly imported by Django
management commands without modification.  The shared `config.py` and
`utils.py` modules are also import-safe.

### Scraper robustness (2026-02-08)

All three functions in `scrape.py` that hit the Idaho Legislature site now use
exponential backoff retries (5 attempts, waits of ~4s → 8s → 16s → 30s,
totalling ~60 seconds) instead of the previous 3 attempts with a fixed
1-second wait.  Connection/read timeouts increased from (3, 5) to (5, 10)
seconds.  The `ratelimit` decorators (`@sleep_and_retry` + `@limits`) are
preserved on all three functions to avoid hammering the site.

### Items intentionally left unchanged

- No test infrastructure exists; adding it is deferred to the Django
  migration since the test framework and runner will change.
- Streamlit page files in `pages/` keep their top-level `df = load_data()`
  pattern — this is idiomatic Streamlit and will be replaced during
  migration.
- `pdf_to_html.py` already had a `__main__` guard and docstrings; no
  changes needed.
