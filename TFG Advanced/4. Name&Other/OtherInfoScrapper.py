import datetime
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
        df = pd.read_csv('./3. Price/ticker_list.csv', index_col=0)
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
        if os.path.exists("4. Name&Other\\OtherInfo\\" + file):
            print("({0},{1}) exists. Skipping...".format(index, ticker))
            continue
        else:
            print("({0},{1}) does NOT exist. Creating".format(index, ticker))
            downloadStockPrice(index, errores, ticker)

errors = []

# Conseguir Fundamentales de una acción
def downloadStockPrice(i, errores, ticker):
    print("Empezando " + ticker)

    url = "https://roic.ai/company/"+ ticker
    
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--ignore-ssl-errors')

    browser = webdriver.Chrome(options=options)
    browser.get(url)

    
    time.sleep(2)

    # Comprobamos que la dirección es la adecuada, en otro caso se trata de un error
    if browser.current_url == "https://roic.ai/404":
        errores.append(ticker)
        browser.close()
        browser.quit()
        return
    try:
        name = browser.find_elements(By.XPATH, '//*[@id="__next"]/div/main/div[2]/div[1]/div[2]/div[2]/h1')[0].text
        currency = browser.find_elements(By.XPATH, '//*[@id="__next"]/div/main/div[2]/div[1]/div[3]/div[1]/div[1]/div[1]')[0].text
        sector = browser.find_elements(By.XPATH, '//*[@id="__next"]/div/main/div[3]/div/div[2]/div[2]/div[1]/div/div[2]/div[1]/div[1]/div[2]')[0].text
        industry = browser.find_elements(By.XPATH, '//*[@id="__next"]/div/main/div[3]/div/div[2]/div[2]/div[1]/div/div[2]/div[1]/div[2]/div[2]')[0].text
        country = browser.find_elements(By.XPATH, '//*[@id="__next"]/div/main/div[2]/div[1]/div[1]/span')[0].text.split()[0]
        ipo = browser.find_elements(By.XPATH, '//*[@id="__next"]/div/main/div[3]/div/div[2]/div[2]/div[1]/div/div[2]/div[3]/div[1]/div[2]')[0].text
        insider = browser.find_elements(By.XPATH, '//*[@id="__next"]/div/main/div[3]/div/div[1]/div/div[1]/div[1]/div[5]/div[3]')[0].text
        institution = browser.find_elements(By.XPATH, '//*[@id="__next"]/div/main/div[3]/div/div[1]/div/div[1]/div[1]/div[6]/div[3]')[0].text
    except:
        errors.append(ticker)
        browser.close()
        browser.quit()
        return

    data = [name, currency, sector, industry, country, ipo, insider, institution]


    # Creamos un dataframe con los datos la tabla
    index = ["Name", "Currency", "Sector", "Industry", "Country", "IPO","Insider Percentage", "Institution Percentage"]
    df = pd.DataFrame(data, index = index)
    # print(df.head(10))

    # Guardamos el dataframe en formato csv
    df.to_csv('4. Name&Other\\OtherInfo\\'+ ticker +'.csv')
    

    print("Índice: ", i)
    print(ticker + " acabado") 
    print("Errores hasta ahora: ", errores)
    print("Execution Time: {0}".format(datetime.timedelta(seconds=(time.time() - start_time))))

    browser.close()
    browser.quit()

    return




if __name__ == "__main__":
    main()