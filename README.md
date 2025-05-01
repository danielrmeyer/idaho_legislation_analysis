# Idaho Legislation Analysis

This project scrapes legislative bills from the Idaho Legislature and uses the OpenAI API to detect potential constitutional issues.

---

## 🔧 Setup

1. **Install Python 3.13+** and create a virtual environment (optional but recommended).
2. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

---

## 📥 Step 1: Scrape Legislative Data

Run the scraper:

```bash
python scrape.py
```

Upon completion, the script will output a string representing the date of the scrape and the directory where the data is stored. This value is referred to as the **`DATARUN`**, and should be exported as an environment variable for use in subsequent steps. For example:

```bash
export DATARUN=04_30_2025
```

---

## 📊 Step 2: Explore Bill Data

Launch the interactive explorer with Streamlit:

```bash
streamlit run bill_data_explorer.py
```

---

## 📄 Step 3: Convert PDFs to HTML

This step converts the downloaded PDF files into HTML while preserving formatting like strikethroughs and underlines, which are essential for interpreting legislative changes.

### 🔑 Prerequisites

1. Make sure the `DATARUN` environment variable is set:

   ```bash
   export DATARUN=04_30_2025
   ```

2. Set your Adobe PDF Services credentials:

   ```bash
   export PDF_SERVICES_CLIENT_ID="your_client_id_here"
   export PDF_SERVICES_CLIENT_SECRET="your_client_secret_here"
   ```

### ▶️ Run the Conversion

Start the conversion process:

```bash
python pdf_to_html.py
```

> ⚠️ **Note:** This process may take several hours. It is intentionally throttled to avoid overloading external services.

---

## 📁 Output

All processed data is stored in a subdirectory named after the `DATARUN` value (e.g., `04_30_2025`). This enables archival and comparison of different scrape sessions over time.

---

## 🧠 Future Goals

- Fine-tune an OpenAI or Mistral model on historical Idaho legislation
- Automatically identify constitutional conflicts in proposed bills
- Provide a searchable legislative history for citizens and advocacy groups

---

## 📝 License

This project is open-source. See `LICENSE` for more information.

---

## 🤝 Contributing

Contributions are welcome! Please open an issue or pull request with ideas or improvements.
