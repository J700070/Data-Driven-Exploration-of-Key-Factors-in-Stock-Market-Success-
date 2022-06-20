from bs4 import BeautifulSoup
import time
from selenium import webdriver
import pandas as pd

# Conseguir lista de acciones
url = "https://www.slickcharts.com/dowjones"
browser = webdriver.Chrome()
browser.get(url)
time.sleep(3)
html = browser.page_source
soup = BeautifulSoup(html, "lxml")



data = []
table = soup.find('table', attrs={'class':'table'})
table_body = table.find('tbody')

rows = table_body.find_all('tr')
for row in rows:
    cols = row.find_all('td')
    cols = [ele.text.strip() for ele in cols]
    data.append([ele for ele in cols if ele]) # Get rid of empty values


df = pd.DataFrame(columns=('Name', 'Ticker'))
for i in range(len(data)):
   df.loc[i] = [data[i][1], data[i][2]]

print(df)
df.to_csv('dowjones_lista.csv')

browser.close()
browser.quit()