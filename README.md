# Idaho Legislation Analysis Code
The goal of this project is to scrape bills from the Idaho Legislature and use chatGPT to detect constitutional issues.

First off create a virtualenv or otherwise install a newer version of Python (Python 3.13). Then install the dependencies with 
`pip install -r requirements.txt` 

The first step in scraping the data is to run the script `python scrape.py`.  Upon completion this script will kick out a string 
that is the date the data was scraped and also the directory the data is stored in.  This string will be refereed to as the "DATARUN" and should be
set as an environment variable for the next next steps.  For example,

`export DATARUN=04_30_2025` if the DATARUN is 04_30_2025

Next you can interact with the DATARUN by running,
`streamlit run bill_data_explorer.py`

