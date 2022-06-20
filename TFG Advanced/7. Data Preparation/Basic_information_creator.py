import pandas as pd
from datetime import datetime

ticker_list = pd.read_csv("7. Data Preparation\\ticker_list.csv", index_col=0)

general_df = pd.DataFrame(columns=["Name","Currency","Sector","Industry","Country","IPO","Insider Percentage","Institution Percentage",	"Years since IPO"])

for index, row in ticker_list.iterrows():
    ticker = row["Ticker"]

    # Ccomprobamos la existencia de la información básica y los fundamentales.
    try:
        basic_data = pd.read_csv("4. Name&Other\\OtherInfo\\"+ticker+".csv", index_col=0)
        basic_data.reset_index(inplace=True)

        # Si está vacío continuamos
        if len(basic_data) == 0:
            continue
    except:
        continue

    try:
        fundamental_data = pd.read_csv("7. Data Preparation\\CleanedFundamentals\\"+ticker+".csv", index_col=0)

        # Si está vacío continuamos
        if len(fundamental_data) == 0:
            continue
    except:
        continue

    if basic_data.iat[5,1] == "Invalid Date": # Corresponde a la entrada de la "IPO"
        years_since_ipo= None 
    else:
        years_since_ipo = datetime.now().year - int(basic_data.iat[5,1][-4:]) # Año actual - Año de la IPO

    data = []


    data.insert(0,{'index': 'Ticker', '0': ticker})
    basic_data =pd.concat([pd.DataFrame(data), basic_data], ignore_index=True)

    # Insertamos los años desde la salida a bolsa al final
    basic_data.loc[len(basic_data.index)] = {'index': 'Years since IPO', '0': years_since_ipo}


    # Volvemos a utilizar 'index' como índice
    basic_data.set_index('index', inplace=True)
    basic_data.index.name = None

    # Trasponemos
    basic_data = basic_data.T

    
    # ATENCIÓN
    # ==================================================================================================================================
    # La solución propuesta es poco eficiente. La memoria se reasigna para cada operación de concatenación.
    # Combianndo esto con el bucle for llegamos a una operación de complejidad cuadrática. Una mejor solución es operarlo
    # en listas y posteriormente convertirlo a un df. En mi caso la eficiencia no es un problema, por lo que ha optado por esta solución.
    # ==================================================================================================================================

    # Agregamos al df resultado
    general_df = pd.concat([general_df, basic_data], ignore_index=True)

# Quitamos las entradas '- -' que representan NaNs
general_df.replace("- -",None, inplace=True)

# Eliminamos las acciones sin "Sector"
general_df.drop(general_df[general_df["Sector"].isna()].index, inplace=True)

# Las fechas inválidas las cambiamos por "None"
general_df.replace("Invalid Date",None, inplace=True)

# Convertimos la columna IPO a datetime
general_df["IPO"] = pd.to_datetime(general_df["IPO"])

# Quitamos los porcentajes y multiplicamos por 100
general_df['Insider Percentage'] = general_df['Insider Percentage'].str.rstrip('%').astype('float') / 100.0
general_df['Institution Percentage'] = general_df['Institution Percentage'].str.rstrip('%').astype('float') / 100.0


general_df.to_csv("7. Data Preparation\\Basic_information.csv")