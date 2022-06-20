import pandas as pd

ticker_list = pd.read_csv("7. Data Preparation\\ticker_list.csv", index_col=0)

counter = 0

for index, row in ticker_list.iterrows():
    ticker = row["Ticker"]

    # Intentamos leer datos financieros y precios de acciones
    # Si no hay datos financieros o precios de acciones, continuamos
    try:
        fundamental_data = pd.read_csv("7. Data Preparation\\CleanedFinancials\\"+ticker+".csv", index_col=0)
        fundamental_data.dropna(how='all', inplace=True)
    except:
        continue

    try:
        price_data = pd.read_csv("7. Data Preparation\\CleanedPrice\\"+ticker+".csv", index_col=0)
        price_data.dropna(how='all', inplace=True)
    except:
        continue

    # Los juntamos
    joined_data = fundamental_data.join(price_data, how='inner')

    # Si el join resulta en un df vacío se ignora
    if len(joined_data) == 0:
        continue

    joined_data.to_csv("7. Data Preparation\\CleanedFundamentals\\"+ticker+".csv")