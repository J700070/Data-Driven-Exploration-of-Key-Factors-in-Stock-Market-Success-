import datetime
from bs4 import BeautifulSoup
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
import pandas as pd
import os.path
import threading

# Almacenamos la hora de inicio del programa
start_time = time.time()

# Almacenamos los tickers que han dado error
errores = []

def main():
    try:
        # Leemos la lista de tickers
        df = pd.read_csv('1. Sitemap/sitemap.txt')
        print(df)
        print("CSV succesfully read.")
    except:
        print("Error: Cannot read csv.")
        return


    num_filas = df.shape[0]
    medio = round((num_filas/2))

    # Multi-threading
    try:
        # El primer thread recorre la lista desde el principio
        thread1 = threading.Thread(target=iterTickers, args=("Hilo1",df))

        # El segundo thread recorre la lista desde el final
        thread2 = threading.Thread(target=iterTickers, args=("Hilo2", df[::-1]))

        # El tercero thread recorre la lista desde el medio hacia el inicio
        thread3 = threading.Thread(target=iterTickers, args=("Hilo3", df[:medio:][::-1]))

        # El tercero thread recorre la lista desde el medio hacia el final
        thread4 = threading.Thread(target=iterTickers, args=("Hilo4", df[medio::]))

        thread1.start()
        thread2.start()
        thread3.start()
        thread4.start()

        # Esperamos
        thread1.join()
        thread2.join()
        thread3.join()
        thread4.join()
           
    except:
        print("No se ha podido iniciar el hilo.")

    

def iterTickers(thread_name,df):
    print("Thread: {0}. Iniciado.".format(thread_name))
    
    for index, row in df.iterrows():
        ticker = row["Ticker"]
        file = "{0}.csv".format(ticker)

        # Comprobamos que no tenemos ya el precio (útil para no repetir trabajo)
        
        if os.path.exists("3. Price\\HistoricalPrices\\" + file):
            print("({0},{1}) exists. Skipping...".format(index, ticker))
            continue
        else:
            print("({0},{1}) does NOT exist. Creating".format(index, ticker))
            downloadStockPrice(index, row, errores, ticker)



# Conseguir Fundamentales de una acción
def downloadStockPrice(i, row, errores, ticker):
    print("Empezando " + ticker)

    url = "https://finance.yahoo.com/quote/"+ ticker + "/history?period1=0&period2=1645920000&interval=1mo&filter=history&frequency=1mo&includeAdjustedClose=true"
    
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--ignore-ssl-errors')

    browser = webdriver.Chrome(options=options)
    browser.get(url)

    
    time.sleep(2)
    browser.find_elements(By.XPATH, '//*[@id="consent-page"]/div/div/div/form/div[2]/div[2]/button')[0].click()
    time.sleep(1)

    # Comprobamos que la dirección es la adecuada, en otro caso se trata de un error
    if browser.current_url == "https://finance.yahoo.com/lookup?s="+ticker+"":
        # errores.append(ticker)
        browser.close()
        browser.quit()
        return

    # Hacemos scroll para que la tabla de precios se cargue por completo
    browser.execute_script("window.scrollTo(0, document.body.scrollHeight*50)")
    time.sleep(1)
    browser.execute_script("window.scrollTo(0, document.body.scrollHeight*50)")
    time.sleep(1)
    browser.execute_script("window.scrollTo(0, document.body.scrollHeight*50)")
    time.sleep(1)
    browser.execute_script("window.scrollTo(0, document.body.scrollHeight*50)")
    time.sleep(1)
    browser.execute_script("window.scrollTo(0, document.body.scrollHeight*50)")
    time.sleep(1)
    browser.execute_script("window.scrollTo(0, document.body.scrollHeight*50)")
    time.sleep(1)


    html = browser.page_source
    soup = BeautifulSoup(html, "lxml")
    
    # Cogemos los datos de la tabla
    data = []
    table = soup.find('table', attrs={'class':'W(100%)'})
    table_body = table.find('tbody')

    rows = table_body.find_all('tr')
    for row in rows:
        cols = row.find_all('td')
        cols = [ele.text.strip() for ele in cols]
        data.append(cols)

    # Creamos un dataframe con los datos la tabla
    columns = ["Date", "Open", "High", "Low", "Close", "Adj Close","Volume"]
    df = pd.DataFrame(data, columns = columns)

    # Guardamos el dataframe en formato csv
    df.to_csv('3. Price\\HistoricalPrices\\'+ ticker +'.csv')
    print(df.head(10))

    print("Índice: ", i)
    print(ticker + " acabado") 
    print("Errores hasta ahora: ", errores)
    print("Execution Time: {0}".format(datetime.timedelta(seconds=(time.time() - start_time))))

    browser.close()
    browser.quit()

    return




if __name__ == "__main__":
    main()