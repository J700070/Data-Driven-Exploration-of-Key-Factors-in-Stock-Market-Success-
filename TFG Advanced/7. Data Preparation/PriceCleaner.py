import pandas as pd

ticker_list = pd.read_csv("5. Financial Statements\\ticker_list.csv", index_col=0)

# función para saber si la row es de dividendo
def is_dividend_or_split(row1):
    if "Dividend" in str(row1["Open"]):
        return 1
    elif "Split" in str(row1["Open"]):
        return 2
    else:
        return 0

for index,row in ticker_list.iterrows():
    ticker = row["Ticker"]
    
    print("Empezando ", ticker)

    ticker_prices = pd.read_csv("3. Price\\HistoricalPrices\\"+ticker+".csv", index_col=0)

    # Si está vacío continuamos
    if len(ticker_prices) == 0:
        print("No hay datos para ", ticker)
        continue

    ticker_prices['Date']= pd.to_datetime(ticker_prices['Date'])

    # Ahora sabemos que rows correspenden a dividendos o splits
    ticker_prices["Dividend or Split"] = ticker_prices.apply(lambda row: is_dividend_or_split(row), axis=1)

    # Trabajamos ahora solo con las rows de dividendo
    dividends = ticker_prices[ticker_prices["Dividend or Split"] == 1].copy()

    # Dropeamos de ticker_prices las filas de añadir divedendo o de stock splits
    ticker_prices.drop(ticker_prices[ticker_prices["Dividend or Split"] != 0 ].index, inplace=True)


    ticker_prices.replace(",", "", regex=True, inplace=True)
    ticker_prices.replace("-", "", regex=True, inplace=True)

    ticker_prices[['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']] = ticker_prices[['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']].apply(pd.to_numeric, errors='coerce')


    # Cogemos los precios medianos de cada año
    dfMedian = ticker_prices.groupby(by=ticker_prices["Date"].dt.year).median()

    if len(dividends) != 0:
        # Cogemos el valor del dividendo y lo guardamos el la columna "Value"
        dividends["Value"] = pd.to_numeric(dividends.apply(lambda row: row["Open"].replace("Dividend", "") , axis=1))

        # Cogemos los dividendos por año
        dividend_col = dividends.groupby(dividends["Date"].dt.year).sum()["Value"]

        dfMedian["Dividend"] = dividend_col

    else:
        dfMedian["Dividend"] = 0

    dfMedian["Dividend"].fillna(0, inplace=True)

    # Calculamos la suma acumulativa
    dfMedian["Dividend Cum"] = dfMedian["Dividend"].cumsum()
    dfMedian["Price with cum Dividends"] = dfMedian["Adj Close"] + dfMedian["Dividend Cum"]

    # Eliminamos las filas Nan
    dfMedian.dropna(thresh=4, inplace=True)

    if 'Dividend or Split' in dfMedian:
        # Eliminamos la columna que ya no nos interesa
        dfMedian.drop("Dividend or Split", axis=1, inplace=True)


    dfMedian.to_csv("7. Data Preparation\\CleanedPrice\\"+ticker+".csv")
    print("Acabado ", ticker)
   