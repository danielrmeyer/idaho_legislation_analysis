# Idaho Legislation Analysis Code
The goal of this project is to scrape bills from the Idaho Legislature and use the openai api to detect constitutional issues.

First off create a virtualenv or otherwise install a newer version of Python (Python 3.13). Then install the dependencies with 
`pip install -r requirements.txt` 

The first step in scraping the data is to run the script `python scrape.py`.  Upon completion this script will kick out a string 
that is the date the data was scraped and also the directory the data is stored in.  This string will be refereed to as the "DATARUN" and should be
set as an environment variable for the next next steps.  For example,

`export DATARUN=04_30_2025` if the DATARUN is 04_30_2025

Next you can interact with the DATARUN by running,
`streamlit run bill_data_explorer.py`

Once you have generated a datarun you can convert the downloaded pdf files into html, preserving the strike through and underlines
necessary for interpreting these legislative documents.

First make sure you have set your `DATARUN` environment variable.  Second you need to fetch the adobe credentials and set two variable:
```
export PDF_SERVICES_CLIENT_ID="################################"
export PDF_SERVICES_CLIENT_SECRET="####################################"
```

Finally run `python pdf_to_html.py`.  This task will take a long time (hours).  The code is throttled we don't put too much
pressure on the web resources we are hitting.