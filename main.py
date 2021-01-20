import requests
from bs4 import BeautifulSoup
import pandas as pd

years = range(1970,2021)

for year in years:
    url = 'https://www.pro-football-reference.com/years/{}/draft.htm'.format(year)

    html_content = requests.get(url).text

    soup = BeautifulSoup(html_content)

    table = soup.find_all('table')

    df = pd.read_html(str(table))[0]

    with open('{}.csv'.format(year), "wb") as out:
        df["year"] = year
        df.to_csv(out)

