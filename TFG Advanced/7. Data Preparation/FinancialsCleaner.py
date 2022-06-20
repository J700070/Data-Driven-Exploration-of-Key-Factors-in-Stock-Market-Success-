import pandas as pd


df = pd.read_csv("5. Financial Statements\\ticker_list.csv", index_col=0)

for index, row in df.iterrows():
    ticker = row["Ticker"]

    # if ticker != "CO":
    #     continue
    # Leemos los fundamentales de cada acción y los cambiamos
    route = "5. Financial Statements\\FinancialsCSV\\"+ ticker +'.csv'

    try:
        # El índice será la entrada en los documentos financieros (ej. Revenue, EBITDA, etc.)
        ticker_df = pd.read_csv(route, index_col=1)

        ticker_df.index.name = None
        ticker_df = ticker_df.T
        ticker_df.drop(ticker_df.index[0], inplace= True)

        # Arreglamos los nombre duplicados con datos diferentes
        ticker_df.columns.values[35] = "Inventory (Balance)"
        ticker_df.columns.values[79] = "Inventory (Cash Flow)"
        ticker_df.columns.values[41] = "Goodwill and Intangible Assets"
        ticker_df.columns.values[51] = "Deferred Revenue (Current)"
        ticker_df.columns.values[55] = "Deferred Revenue (Non-Current)"
        ticker_df.columns.values[73] = "Net Income (Cash Flow)"
        ticker_df.columns.values[74] = "Depreciation and Amortization (Cash Flow)"
        ticker_df.columns.values[48] = "Accounts Payable (Balance)"
        ticker_df.columns.values[80] = "Accounts Payable (Cash Flow)"

        # Otros arreglos a los nombres
        ticker_df.rename(columns={"Interest Income ": 'Interest Income'}, inplace=True)
        ticker_df.rename(columns={"Other Investing Activites": 'Other Investing Activities'}, inplace=True)

        cols = []
        for column in ticker_df.columns:
            if "ratio" in column:
                cols.append(column.replace("ratio", "Ratio"))
                continue
            cols.append(column)
        ticker_df.columns = cols
        
        # Dropeamos duplicados
        ticker_df = ticker_df.loc[:,~ticker_df.columns.duplicated()]

        ticker_df.drop("INCOME STATEMENT",axis=1, inplace = True)
        ticker_df.drop("BALANCE SHEET",axis=1, inplace = True)
        ticker_df.drop("CASH FLOW STATEMENT",axis=1, inplace = True)
        ticker_df.drop("SEC Link",axis=1, inplace = True)
        try:
            ticker_df.drop("false",axis=1, inplace = True)
            ticker_df.drop("true",axis=1, inplace = True)
        except:
            pass
      
        ticker_df.replace("- -", None, inplace=True)
        ticker_df.replace("undefined", None, inplace=True)

        ticker_df.apply(pd.to_numeric)     

        # El dataframe está completamente vacío, no nos interesa
        if ticker_df.dropna(how='all').empty:
            print("Vacío")
            continue     

        ticker_df.to_csv("7. Data Preparation\\CleanedFinancials\\"+ ticker +'.csv')

    except Exception as e:
        print(e)
        print("Error leyendo " + ticker)

    