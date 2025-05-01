# Idaho Legislation Analysis Code
The goal of this project is to scrape bills from the Idaho Legislature and use chatGPT to detect constitutional issues.

The first step is to run the script `scrape.py`.  Upon completion it will kick out a string that is the date the data
was scraped and also the directory the data is stored in.  This string will be refereed to as the "DATARUN" and should be
set as an enironment variable for the next next steps.