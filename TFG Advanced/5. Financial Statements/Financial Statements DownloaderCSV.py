import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
import pandas as pd
import json


error = []

def main():
    try:
        # Leemos nuestra lista de ticker
        df = pd.read_csv('3. Price/ticker_list.csv',  index_col=0)
        print("CSV succesfully read.")

    except:
        print("Error: Cannot read csv.")
        return
    
    

    for index, row in df.iterrows():
        ticker = row["Ticker"]
        file = "{0}.csv".format(ticker)


       # Comprobamos que no tenemos ya los fundamentales (útil para no repetir trabajo)
        if os.path.exists("5. Financial Statements\\FinancialsCSV\\" + file):
            print("({0},{1}) exists. Skipping...".format(index, ticker))
            continue
        else:
            print("({0},{1}) does NOT exist. Creating".format(index, ticker))

            # Comprobamos si tenemos datos de nombre para el ticker
            if os.path.exists('4. Name&Other/OtherInfo/'+file):
                print("Información básica de ({0},{1}) leída correctamente. Comenzando ejecución...".format(index, ticker))
                downloadStockFundamentals(index, row)
                print(error)

            else:
                print("({0},{1}) no tiene información básica.Pasamos al siguinte...".format(index, ticker))
                continue
    print(error)

# Conseguir Fundamentales de una acción
def downloadStockFundamentals(i, row):
    ticker = row["Ticker"]
    print("Empezando " + ticker)
    firstTime = True


    url = "https://roic.ai/financials/" + ticker
    options = webdriver.ChromeOptions()
    # options.add_argument('--headless')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--ignore-ssl-errors')
    prefs = {
        "download.default_directory" : "5. Financial Statements\\FinancialsCSV",
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing_for_trusted_sources_enabled": False,
        "safebrowsing.enabled": False
        }
    options.add_experimental_option("prefs",prefs)
    browser = webdriver.Chrome(options=options)
    browser.get(url)


    if firstTime:
        browser.add_cookie({'domain': 'roic.ai', 'expiry': 1844004391, 'httpOnly': False, 'name': 'twt', 'path': '/', 'secure': False, 'value': 'IrvingSoh'})
        browser.get(url)
        firstTime = False
        print("Añadida Cookie!")
    
    time.sleep(1)
    try:
        browser.find_elements(By.XPATH, '//*[@id="__next"]/div/main/div[3]/div/div/div/div[1]/div[1]/div[5]/button')[0].click()
        time.sleep(1)
        try:
            df = pd.read_clipboard(sep='\t', index_col=False)
        except:
            df = pd.read_clipboard(sep='\\s+', index_col=False)
        
        
        df.to_csv("5. Financial Statements\\FinancialsCSV\\"+ ticker +'.csv')
        print(df.head(10))
    except Exception as e:
        print(e)
        error.append(ticker)
        return 

    print("Índice: ", i)
    print(ticker + " acabado")


    browser.close()
    browser.quit()
    
    return 











if __name__ == "__main__":
    main()