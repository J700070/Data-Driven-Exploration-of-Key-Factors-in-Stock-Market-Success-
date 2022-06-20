import numpy as np
import pandas as pd


# Lista de los campos a los que se le ha aplicado el fix trivial
trivial_fix_list = list({"Other Liabilities", "Preferred Stock", "Common Stock", "Tax Assets", "Tax Payable", "Capital Lease Obligations", "Common Stock Repurchased", "Common Stock Issued",
                    "Dividends Paid", "Interest Income", "Other Expenses", "Stock Based Compensation", "Deferred Income Tax",
                    "Interest Expense (Gain)", "Other Investing Activities", "Deferred Tax Liabilities", "Purchases of Investments", "Sales/Maturities of Investments","Investments",
                    "Other Assets", "Acquisitions Net", "Inventory", "Inventory (Cash Flow)", "Short-Term Debt", "Debt Repayment", "Long-Term Debt", "Research and Development Exp.", "Effect of Forex Changes on Cash", "Other Liabilities"
                    , "Other Working Capital", "Short-Term Investments", "Dividend Cum", "Dividend", "Other Non-Current Liabilities", "Accounts Payable (Cash Flow)",
                    "Accounts Receivable",'Intangible Assets', 'Goodwill'})

core_columns = ["Revenue", "Gross Profit", "Operating Income","Income Tax expense (Gain)", "Net Income", "Total Assets", "Total Liabilities", "Total Stockholders Equity"]

def try_repair_column(columns_to_repair,row, visited_columns, trivial_fix):
    # Intenta reparar una columna (la principal) usando otras columnas (las secundarias)
    # Intenta reparar las columnas secundarias llamando a applyFix
    # Si consigue reparar las necesarias, repara la columna principal

    for col_to_repair in columns_to_repair:            
        # Si es nula intentamos reparar
        if np.isnan(row[col_to_repair]):
            # Si es null pero ya la hemos visitado -> Se ha intentado reparar pero no se ha podido, ergo, tampoco podemos reparar la columna principal
            if col_to_repair in visited_columns:
                return False

            # Si la columna es nula y no la hemos visitado -> Intentamos repararla
            else:
                row[col_to_repair] = applyFix(row, col_to_repair, visited_columns, trivial_fix)
                # Volvemos a comprabar si la columna es nula
                if np.isnan(row[col_to_repair]):
                    return False

    return True
    



def reconstructDf(df, ticker, trivial_fix =False):
    # Reconstruimos los fundamentales de una empresa a partir de otros elementos

    df = df.copy()
    aux_df = df.copy()
    min_num_filas = 4

    if df.empty:
        print("El dataframe está vacío")
        return df
    
    if not df.isnull().values.any():
        print("El dataframe está en buen estado")
        return df

    if len(df.index) < min_num_filas:
        print("El dataframe tiene menos de {} filas".format(min_num_filas))
        return df
    
    # Los infinitos los tratamos como NaN
    if np.inf in df.values:
        df = df.replace(np.inf, np.nan)
    elif -np.inf in df.values:
        df = df.replace(-np.inf, np.nan)

    null_columns = []
    row_drop_set = set()

    for index, row in df.iterrows():
        # Vemos qué columna tiene un valor nulo y la guardamos
        null_columns = row[row.isna()].index.tolist()

        # Reparamos la columna con valor nulo
        for null_colum in null_columns:
            df.loc[index, null_colum] = applyFix(row, null_colum, visited_columns=[], trivial_fix=trivial_fix)

        # Si las columnas core no se han podido reparar, eliminamos la fila luego
        for core_col in core_columns:
            if row[core_col] == 0 or np.isnan(row[core_col]):
                row_drop_set.add(index)
                break
        
        null_columns.clear()

    if len(row_drop_set) > 0:
        df.drop(row_drop_set, inplace=True)

        # Al eliminar filas es posible que dejemos el dataframe vacío
        if df.empty:
            return df
        # O que no haya una cantidad de años representativa
        if len(df.index) < min_num_filas:
            return df


    df.drop(["General and Administrative Exp.","Selling and Marketing Exp.","High","Low"], axis=1, inplace=True)

    # Cogemos el primer año de la serie
    first_year = df.index[0]
    # Cogemos el último año de la serie
    last_year = df.index[-1]

    # Acotamos la serie a los años de la serie de datos
    aux_df = aux_df.loc[first_year:last_year]

    # Calculamos la suma cumulativa de los dividendos
    aux_df["Dividend Cum"] = aux_df["Dividend"].cumsum()
    # Calculamos la suma del precio con la suma cumulativa de los dividendos
    aux_df["Price with cum Dividends"] = aux_df["Adj Close"] + aux_df["Dividend Cum"]
    # Traspasamos los valores del precio con la suma cumulativa del dataframe auxiliar al principal
    df["Dividend Cum"] = aux_df["Dividend Cum"]
    df["Price with cum Dividends"] = aux_df["Price with cum Dividends"]


    if trivial_fix:
        df.to_csv("7. Data Preparation\\CleanedFundamentalsNormal&TrivialFix\\"+ticker+".csv")
    else:
        df.to_csv("7. Data Preparation\\CleanedFundamentalsNormalFix\\"+ticker+".csv")

    return df

def applyFix(row, col, visited_columns, trivial_fix=False):
    # Dependiendo de la columna, aplica un arreglo

    if col in visited_columns:
        print("Ya visitada. Saliendo...")
        return row[col]

    if row[col] == np.nan:
        print("No es nula. Saliendo...")
        return row[col]

    visited_columns.append(col)

    # Revenue
    if col == "Revenue":
        return  np.nan

    # COGS
    elif col == "COGS":
        repaired = try_repair_column(["Revenue", "Gross Profit"],row, visited_columns, trivial_fix)

        if repaired:
            return row["Revenue"] - row["Gross Profit"]

    # Gross Profit
    elif col == "Gross Profit":
        # Fix 1
        repaired = try_repair_column(["Revenue", "COGS"],row, visited_columns, trivial_fix)

        if repaired:
            return row["Revenue"] - row["COGS"]

        # Fix 2
        repaired = try_repair_column(["Revenue","Gross Profit Ratio"],row, visited_columns, trivial_fix)

        if repaired:
            return row["Revenue"] * row["Gross Profit Ratio"]
        
        # Fix 3
        repaired = try_repair_column(["Operating Expenses","Operating Income"],row, visited_columns, trivial_fix)

        if repaired:
            return row["Operating Income"] + row["Operating Expenses"]

    # Gross Profit Ratio
    elif col == "Gross Profit Ratio":
        repaired = try_repair_column(["Revenue", "Gross Profit"],row, visited_columns, trivial_fix)

        if repaired:
            return row["Gross Profit"] / row["Revenue"]


    # Other Assets
    elif col == "Other Assets":
        repaired = try_repair_column(["Total Assets", "Total Current Assets", "Total Non-Current Assets"],row, visited_columns, trivial_fix)

        if repaired:
            return row["Total Assets"] - row["Total Current Assets"] - row["Total Non-Current Assets"]
    
    # Selling and Marketing Exp.
    elif col == "Selling and Marketing Exp.":
        repaired = try_repair_column(["Selling, General and Administrative Exp.", "General and Administrative Exp."],row, visited_columns, trivial_fix)

        if repaired:
            return row["Selling, General and Administrative Exp."] - row["General and Administrative Exp."]
        else:
            return np.nan

    # Acquisitions Net
    elif col == "Acquisitions Net":
        repaired = try_repair_column(["CAPEX", "Purchases of Investments", "Sales/Maturities of Investments", "Other Investing Activities", "Cash Used for Investing Activites"],row, visited_columns, trivial_fix)
        
        if repaired:
            return row["Cash Used for Investing Activites"] - row["CAPEX"] - row["Purchases of Investments"] - row["Sales/Maturities of Investments"] - row["Other Investing Activities"] 
        
    # Minority Interest
    elif col == "Minority Interest":
        repaired = try_repair_column(["Total Liabilities And Stockholders Equity", "Total Liabilities & Equity"],row, visited_columns, trivial_fix)

        if repaired:
            return row["Total Liabilities & Equity"] - row["Total Liabilities And Stockholders Equity"]

    # Deferred Tax Liabilities
    elif col == "Deferred Tax Liabilities":
        repaired = try_repair_column(["Long-Term Debt", "Deferred Revenue (Non-Current)", "Other Non-Current Liabilities", "Total Non-Current Liabilities"],row, visited_columns, trivial_fix)

        if repaired:
            return row["Total Non-Current Liabilities"] - row["Long-Term Debt"] - row["Deferred Revenue (Non-Current)"] - row["Other Non-Current Liabilities"]

    # Investments
    elif col == "Investments":
        repaired = try_repair_column(["PP&E", "Goodwill", "Intangible Assets", "Tax Assets", "Other Non-Current Assets", "Total Non-Current Assets"],row, visited_columns, trivial_fix)
        
        if repaired:
            return row["Total Non-Current Assets"] - row["PP&E"] - row["Goodwill"] - row["Intangible Assets"] - row["Tax Assets"] - row["Other Non-Current Assets"]
    
    # Short-Term Investments
    elif col == "Short-Term Investments":
        repaired = try_repair_column(["Cash and Cash Equivalents", "Cash and Short-Term Investments"],row, visited_columns, trivial_fix)

        if repaired:
            return row["Cash and Short-Term Investments"] - row["Cash and Cash Equivalents"]
    # Deferred Revenue (Current)
    elif col == "Deferred Revenue (Current)":
        repaired = try_repair_column(["Accounts Payable (Balance)", "Short-Term Debt","Total Current Liabilities", "Other Current Liabilities"],row, visited_columns, trivial_fix)

        if repaired:
            return row["Total Current Liabilities"] - row["Accounts Payable (Balance)"] - row["Short-Term Debt"] - row["Other Current Liabilities"]        

    # Accounts Payable (Balance)
    elif col == "Accounts Payable (Balance)":
        repaired = try_repair_column(["Deferred Revenue (Current)", "Short-Term Debt", "Other Current Liabilities", "Total Current Liabilities"],row, visited_columns, trivial_fix)

        if repaired:
            return row["Total Current Liabilities"] - row["Deferred Revenue (Current)"] - row["Short-Term Debt"] - row["Other Current Liabilities"]

    # Deferred Revenue (Non-Current)
    elif col == "Deferred Revenue (Non-Current)":
        repaired = try_repair_column(["Long-Term Debt", "Deferred Tax Liabilities", "Other Non-Current Liabilities", "Total Non-Current Liabilities"],row, visited_columns, trivial_fix)

        if repaired:
            return row["Total Non-Current Liabilities"] - row["Long-Term Debt"] - row["Deferred Tax Liabilities"] - row["Other Non-Current Liabilities"]

    # Research and Development Exp.
    elif col == "Research and Development Exp.":
        repaired = try_repair_column(["Selling, General and Administrative Exp.", "Operating Expenses", "Other Expenses"],row, visited_columns, trivial_fix)

        if repaired:
            return row["Operating Expenses"] -  row["Selling, General and Administrative Exp."] - row["Other Expenses"]

    # Effect of Forex Changes on Cash
    elif col == "Effect of Forex Changes on Cash":
        repaired = try_repair_column(["Cash Provided by Operating Activities", "Cash Used/Provided by Financing Activities", "Cash Used for Investing Activites", "Net Change In Cash"],row, visited_columns, trivial_fix)

        if repaired:
            return row["Net Change In Cash"] - row["Cash Provided by Operating Activities"] - row["Cash Used/Provided by Financing Activities"] - row["Cash Used for Investing Activites"]

    # Sales/Maturities of Investments
    elif col == "Sales/Maturities of Investments":
        repaired = try_repair_column(["CAPEX", "Acquisitions Net", "Purchases of Investments", "Other Investing Activities", "Cash Used for Investing Activites"],row, visited_columns, trivial_fix)

        if repaired:
            return row["Cash Used for Investing Activites"] - row["CAPEX"] - row["Acquisitions Net"] - row["Purchases of Investments"] - row["Other Investing Activities"]

    # Purchases of Investments
    elif col == "Purchases of Investments":
        repaired = try_repair_column(["CAPEX", "Acquisitions Net", "Sales/Maturities of Investments", "Other Investing Activities", "Cash Used for Investing Activites"],row, visited_columns, trivial_fix)

        if repaired:
            return row["Cash Used for Investing Activites"] - row["CAPEX"] - row["Acquisitions Net"] - row["Sales/Maturities of Investments"] - row["Other Investing Activities"]

    # Goodwill and Intangible Assets
    elif col == "Goodwill and Intangible Assets":
        # Fix 1
        repaired = try_repair_column(["Goodwill", "Intangible Assets"],row, visited_columns, trivial_fix)

        if repaired:
            return row["Goodwill"] + row["Intangible Assets"]

        # Fix 2
        repaired = try_repair_column(["Investments", "Tax Assets", "Other Non-Current Assets", "Total Non-Current Assets", "PP&E"],row, visited_columns, trivial_fix)

        if repaired:
            return row["Total Non-Current Assets"] - row["PP&E"] - row["Investments"] - row["Tax Assets"] - row["Other Non-Current Assets"]
    
    # PP&E
    elif col == "PP&E":
        repaired = try_repair_column(["Investments", "Tax Assets", "Other Non-Current Assets", "Total Non-Current Assets", "Goodwill and Intangible Assets"],row, visited_columns, trivial_fix)

        if repaired:
            return row["Total Non-Current Assets"] - row["Goodwill and Intangible Assets"] - row["Investments"] - row["Tax Assets"] - row["Other Non-Current Assets"]

    # Goodwill
    elif col == "Goodwill":
        # Fix 1
        repaired = try_repair_column(["Goodwill and Intangible Assets", "Intangible Assets"],row, visited_columns, trivial_fix)

        if repaired:
            return row["Goodwill and Intangible Assets"] - row["Intangible Assets"]

        # Fix 2
        repaired = try_repair_column(["PP&E", "Intangible Assets", "Investments", "Tax Assets", "Other Non-Current Assets", "Total Non-Current Assets"],row, visited_columns, trivial_fix)

        if repaired:
            return row["Total Non-Current Assets"] - row["PP&E"] - row["Intangible Assets"] - row["Investments"] - row["Tax Assets"] - row["Other Non-Current Assets"]
        
    # Inventory (Balance)
    elif col == "Inventory (Balance)":
        repaired = try_repair_column(["Cash and Short-Term Investments", "Net Receivables", "Other Current Assets", "Total Current Assets"],row, visited_columns, trivial_fix)

        if repaired:
            return row["Total Current Assets"] - row["Cash and Short-Term Investments"] - row["Net Receivables"] - row["Other Current Assets"]
        
    # Intangible Assets
    elif col == "Intangible Assets":
        repaired = try_repair_column(["Goodwill", "Investments", "PP&E", "Tax Assets", "Other Non-Current Assets", "Total Non-Current Assets"],row, visited_columns, trivial_fix)

        if repaired:
            return row["Total Non-Current Assets"] - row["Goodwill"] - row["Investments"] - row["PP&E"] - row["Tax Assets"] - row["Other Non-Current Assets"]

    # Debt Repayment
    elif col == "Debt Repayment":
        repaired = try_repair_column(["Common Stock Issued", "Common Stock Repurchased", "Dividends Paid", "Other Financing Activites", "Cash Used/Provided by Financing Activities"],row, visited_columns, trivial_fix)

        if repaired:
            return row["Cash Used/Provided by Financing Activities"] - row["Common Stock Issued"] - row["Common Stock Repurchased"] - row["Dividends Paid"] - row["Other Financing Activites"]
        
    # Short-Term Debt
    elif col == "Short-Term Debt":
        repaired = try_repair_column(["Accounts Payable (Balance)", "Deferred Revenue (Current)", "Other Current Liabilities", "Total Current Liabilities"],row, visited_columns, trivial_fix)

        if repaired:
            return row["Total Current Liabilities"] - row["Accounts Payable (Balance)"] - row["Deferred Revenue (Current)"] - row["Other Current Liabilities"]

    # Long-Term Debt
    elif col == "Long-Term Debt":
        repaired = try_repair_column(["Deferred Revenue (Non-Current)", "Deferred Tax Liabilities", "Other Non-Current Liabilities", "Total Non-Current Liabilities"],row, visited_columns, trivial_fix)

        if repaired:
            return row["Total Non-Current Liabilities"] - row["Deferred Revenue (Non-Current)"] - row["Deferred Tax Liabilities"] - row["Other Non-Current Liabilities"]

    # Other Non-Current Liabilities
    elif col == "Other Non-Current Liabilities":
        repaired = try_repair_column(["Long-Term Debt", "Deferred Tax Liabilities", "Other Non-Current Liabilities", "Total Non-Current Liabilities"],row, visited_columns, trivial_fix)

        if repaired:
            return row["Total Non-Current Liabilities"] - row["Long-Term Debt"] - row["Deferred Revenue (Non-Current)"] - row["Deferred Tax Liabilities"]
        
    # Cash Used/Provided by Financing Activities
    elif col == "Cash Used/Provided by Financing Activities":
        repaired = try_repair_column(["Debt Repayment", "Common Stock Issued", "Common Stock Repurchased", "Dividends Paid", "Other Financing Activites"],row, visited_columns, trivial_fix)
        
        if repaired:
            return row["Debt Repayment"] + row["Common Stock Issued"] + row["Common Stock Repurchased"] + row["Dividends Paid"] + row["Other Financing Activites"]
        
    # Other Comprehensive Income/Loss
    elif col == "Other Comprehensive Income/Loss":
        repaired = try_repair_column(["Preferred Stock", "Common Stock", "Retained Earnings", "Other Total Stockholders Equity", "Total Stockholders Equity"],row, visited_columns, trivial_fix)
        
        if repaired:
            return row["Total Stockholders Equity"] - row["Preferred Stock"] - row["Common Stock"] - row["Retained Earnings"] - row["Other Total Stockholders Equity"]  

    # Net Receivables
    elif col == "Net Receivables":
        repaired = try_repair_column(["Cash and Short-Term Investments", "Inventory (Balance)", "Other Current Assets", "Total Current Assets"],row, visited_columns, trivial_fix)
        
        if repaired:
            return row["Total Current Assets"] - row["Cash and Short-Term Investments"] - row["Inventory (Balance)"] - row["Other Current Assets"]
    
    # General and Administrative Exp.
    elif col == "General and Administrative Exp.":
        repaired = try_repair_column(["Selling and Marketing Exp.", "Selling, General and Administrative Exp."],row, visited_columns, trivial_fix)
        
        if repaired:
            return row["Selling, General and Administrative Exp."] - row["Selling and Marketing Exp."]
        
    # Total Non-Current Liabilities
    elif col == "Total Non-Current Liabilities":
        repaired = try_repair_column(["Long-Term Debt", "Deferred Tax Liabilities", "Other Non-Current Liabilities", "Deferred Revenue (Non-Current)"],row, visited_columns, trivial_fix)
        
        if repaired:
            return row["Long-Term Debt"] + row["Other Non-Current Liabilities"] + row["Deferred Revenue (Non-Current)"] + row["Deferred Tax Liabilities"]
    
    # Selling, General and Administrative Exp.
    elif col == "Selling, General and Administrative Exp.":
        repaired = try_repair_column(["Research and Development Exp.", "Operating Expenses", "Other Expenses"],row, visited_columns, trivial_fix)
        
        if repaired:
            return row["Operating Expenses"]  - row["Research and Development Exp."] - row["Other Expenses"]
    
    # CAPEX
    elif col == "CAPEX":
        repaired = try_repair_column(["Acquisitions Net", "Purchases of Investments", "Sales/Maturities of Investments", "Other Investing Activities", "Cash Used for Investing Activites"],row, visited_columns, trivial_fix)
        
        if repaired:
            return row["Cash Used for Investing Activites"] - row["Acquisitions Net"] - row["Purchases of Investments"] - row["Sales/Maturities of Investments"] - row["Other Investing Activities"]

    # Total Other Income Expenses (Gains)
    elif col == "Total Other Income Expenses (Gains)":
        repaired = try_repair_column(["Operating Income", "Income Before Tax"],row, visited_columns, trivial_fix)
        
        if repaired:
            return row["Income Before Tax"] - row["Operating Income"]

    # COGS and Expenses
    elif col == "COGS and Expenses":
        repaired = try_repair_column(["COGS", "Operating Expenses"],row, visited_columns, trivial_fix)
        
        if repaired:
            return row["COGS"] + row["Operating Expenses"]

    # Income Tax Expense (Gain)
    elif col == "Income Tax Expense (Gain)":
        repaired = try_repair_column(["Income Before Tax", "Net Income"],row, visited_columns, trivial_fix)
        
        if repaired:
            return row["Income Before Tax"] - row["Net Income"]

    # Other Non-Current Assets
    elif col == "Other Non-Current Assets":
        repaired = try_repair_column(["PP&E", "Goodwill", "Intangible Assets", "Investments", "Tax Assets","Total Non-Current Assets"],row, visited_columns, trivial_fix)
        
        if repaired:
            return row["Total Non-Current Assets"] - row["PP&E"] - row["Goodwill"] - row["Intangible Assets"] - row["Investments"] - row["Tax Assets"]
    
    # Other Current Assets
    elif col == "Other Current Assets":
        repaired = try_repair_column(["Cash and Short-Term Investments", "Inventory (Balance)", "Net Receivables", "Total Current Assets"],row, visited_columns, trivial_fix)
        
        if repaired:
            return row["Total Current Assets"] - row["Cash and Short-Term Investments"] - row["Inventory (Balance)"] - row["Net Receivables"]

    # Other Current Liaibilities
    elif col == "Other Current Liabilities":
        repaired = try_repair_column(["Accounts Payable (Balance)", "Short-Term Debt", "Deferred Revenue (Current)", "Total Current Liabilities"],row, visited_columns, trivial_fix)
        
        if repaired:
            return row["Total Current Liabilities"] - row["Accounts Payable (Balance)"] - row["Short-Term Debt"] - row["Deferred Revenue (Current)"]

    # Total Non-Current Assets
    elif col == "Total Non-Current Assets":
        repaired = try_repair_column(["PP&E", "Goodwill", "Intangible Assets", "Investments", "Tax Assets", "Other Non-Current Assets", "Tax Assets"],row, visited_columns, trivial_fix)
        
        if repaired:
            return row["Tax Assets"] + row["PP&E"] + row["Goodwill"] + row["Intangible Assets"] + row["Investments"] + row["Tax Assets"] + row["Other Non-Current Assets"]

    # EBITDA
    elif col == "EBITDA":
        # Fix 1
        repaired = try_repair_column(["Interest Expense (Gain)", "Depreciation and Amortization", "Operating Income", "Total Other Income Expenses (Gains)"],row, visited_columns, trivial_fix)

        if repaired:
            return row["Interest Expense (Gain)"] + row["Depreciation and Amortization"] + row["Operating Income"] + row["Total Other Income Expenses (Gains)"]
        
        # Fix 2
        repaired = try_repair_column(["EBITDA Ratio", "Revenue"],row, visited_columns, trivial_fix)

        if repaired:
            return row["Revenue"] * row["EBITDA Ratio"]

    # Depreciation and Amortization
    elif col == "Depreciation and Amortization":
        repaired = try_repair_column(["Interest Expense (Gain)", "EBITDA", "Operating Income", "Total Other Income Expenses (Gains)"],row, visited_columns, trivial_fix)

        if repaired:
            return row["EBITDA"] - row["Interest Expense (Gain)"] - row["Operating Income"] - row["Total Other Income Expenses (Gains)"]
        
    # Other Financing Activites
    elif col == "Other Financing Activites":
        repaired = try_repair_column(["Debt Repayment", "Common Stock Issued", "Common Stock Repurchased", "Dividends Paid", "Cash Used/Provided by Financing Activities"],row, visited_columns, trivial_fix)

        if repaired:
            return row["Cash Used/Provided by Financing Activities"] - row["Debt Repayment"] - row["Common Stock Issued"] - row["Common Stock Repurchased"] - row["Dividends Paid"]
    
    # Other Total Stockholders Equity
    elif col == "Other Total Stockholders Equity":
        repaired = try_repair_column(["Total Stockholders Equity", "Preferred Stock", "Common Stock", "Retained Earnings","Other Comprehensive Income/Loss"],row, visited_columns, trivial_fix)

        if repaired:
            return row["Total Stockholders Equity"] - row["Preferred Stock"] - row["Common Stock"] - row["Retained Earnings"] - row["Other Comprehensive Income/Loss"]

    # Operating Income
    elif col == "Operating Income":
        # Fix 1
        repaired = try_repair_column(["Interest Expense (Gain)", "Depreciation and Amortization", "EBITDA", "Total Other Income Expenses (Gains)"],row, visited_columns, trivial_fix)

        if repaired:
            return row["EBITDA"] - row["Interest Expense (Gain)"] - row["Depreciation and Amortization"] - row["Total Other Income Expenses (Gains)"]
        
        # Fix 2
        repaired = try_repair_column(["Operating Income Ratio", "Revenue"],row, visited_columns, trivial_fix)

        if repaired:
            return row["Revenue"] * row["Operating Income Ratio"]
        
        # Fix 3
        repaired = try_repair_column(["Gross Profit", "Operating Expenses"],row, visited_columns, trivial_fix)

        if repaired:
            return row["Gross Profit"] - row["Operating Expenses"]
        
        # Fix 4
        repaired = try_repair_column(["Income Before Tax", "Total Other Income Expenses (Gains)"],row, visited_columns, trivial_fix)

        if repaired:
            return row["Income Before Tax"] + row["Total Other Income Expenses (Gains)"]

    # Operating Income Ratio
    elif col == "Operating Income Ratio":
        repaired = try_repair_column(["Operating Income", "Revenue"],row, visited_columns, trivial_fix)

        if repaired:
            return row["Operating Income"] / row["Revenue"]

    # Cash at the End of Period
    elif col == "Cash at the End of Period":
        repaired = try_repair_column(["Cash at the Beginning of Period", "Net Change In Cash"],row, visited_columns, trivial_fix)
        
        if repaired:
            return row["Cash at the Beginning of Period"] + row["Net Change In Cash"]

    # Retained Earnings
    elif col == "Retained Earnings":
        repaired = try_repair_column(["Preferred Stock", "Common Stock", "Other Comprehensive Income/Loss","Other Total Stockholders Equity", "Total Stockholders Equity"],row, visited_columns, trivial_fix)

        if repaired:
            return row["Total Stockholders Equity"] - row["Preferred Stock"] - row["Common Stock"] - row["Other Comprehensive Income/Loss"] - row["Other Total Stockholders Equity"]

    # Cash Used for Investing Activites
    elif col == "Cash Used for Investing Activites":
        # Fix 1
        repaired = try_repair_column(["CAPEX", "Acquisitions Net", "Purchases of Investments", "Sales/Maturities of Investments", "Other Investing Activities"],row, visited_columns, trivial_fix)

        if repaired:
            return row["CAPEX"] + row["Acquisitions Net"] + row["Purchases of Investments"] + row["Sales/Maturities of Investments"] + row["Other Investing Activities"]
        
    # Operating Expenses
    elif col == "Operating Expenses":
        # Fix 1
        repaired = try_repair_column(["Gross Profit", "Operating Income"],row, visited_columns, trivial_fix)

        if repaired:
            return row["Gross Profit"] - row["Operating Income"]

        # Fix 2
        repaired = try_repair_column(["Research and Development Exp.", "Selling, General and Administrative Exp.", "Other Expenses"],row, visited_columns, trivial_fix)

        if repaired:
            return row["Research and Development Exp."] + row["Selling, General and Administrative Exp."] + row["Other Expenses"]
        
    # Total Current Liaibilities
    elif col == "Total Current Liabilities":
        repaired = try_repair_column(["Accounts Payable (Balance)", "Short-Term Debt", "Deferred Revenue (Current)", "Other Current Liabilities"],row, visited_columns, trivial_fix)

        if repaired:
            return row["Accounts Payable (Balance)"] + row["Short-Term Debt"] + row["Deferred Revenue (Current)"] + row["Other Current Liabilities"]

    # Total Current Assets
    elif col == "Total Current Assets":
        repaired = try_repair_column(["Cash and Short-Term Investments", "Net Receivables", "Inventory (Balance)","Other Current Assets"],row, visited_columns, trivial_fix)

        if repaired:
            return row["Cash and Short-Term Investments"] + row["Net Receivables"] + row["Inventory (Balance)"] + row["Other Current Assets"]

    # Cash at the Beginning of Period
    elif col == "Cash at the Beginning of Period":
        repaired = try_repair_column(["Cash at the End of Period", "Net Change In Cash"],row, visited_columns, trivial_fix)

        if repaired:
            return row["Cash at the End of Period"] - row["Net Change In Cash"]
    
    # Net Change In Cash
    elif col == "Net Change In Cash":
        repaired = try_repair_column(["Cash at the Beginning of Period", "Cash at the End of Period"],row, visited_columns, trivial_fix)

        if repaired:
            return row["Cash at the End of Period"] - row["Cash at the Beginning of Period"]
    
    # Income Before Tax
    elif col == "Income Before Tax":
        # Fix 1
        repaired = try_repair_column(["Net Income", "Interest Expense (Gain)"],row, visited_columns, trivial_fix)

        if repaired:
            return row["Net Income"] + row["Interest Expense (Gain)"]

        # Fix 2
        repaired = try_repair_column(["Operating Income", "Total Other Income Expenses (Gains)"],row, visited_columns, trivial_fix)

        if repaired:
            return row["Operating Income"] - row["Total Other Income Expenses (Gains)"]

        # Fix 3
        repaired = try_repair_column(["Income Before Tax Ratio", "Revenue"],row, visited_columns, trivial_fix)

        if repaired:
            return row["Revenue"] * row["Income Before Tax Ratio"]

    # Income Before Tax Ratio
    elif col == "Income Before Tax Ratio":
        repaired = try_repair_column(["Income Before Tax", "Revenue"],row, visited_columns, trivial_fix)

        if repaired:
            return row["Income Before Tax"] / row["Revenue"]

    # Cash and Short-Term Investments
    elif col == "Cash and Short-Term Investments":
        repaired = try_repair_column(["Cash and Cash Equivalents","Short-Term Investments"],row, visited_columns, trivial_fix)

        if repaired:
            return row["Cash and Cash Equivalents"] + row["Short-Term Investments"]

    # Cash and Cash Equivalents
    elif col == "Cash and Cash Equivalents":
        repaired = try_repair_column(["Cash and Short-Term Investments", "Short-Term Investments"],row, visited_columns, trivial_fix)

        if repaired:
            return row["Cash and Short-Term Investments"] - row["Short-Term Investments"]
    
    # Cash Provided by Operating Activities
    elif col == "Cash Provided by Operating Activities":
        # Fix 1
        repaired = try_repair_column(["Effect of Forex Changes on Cash","Cash Used/Provided by Financing Activities", "Cash Used for Investing Activites", "Net Change In Cash"],row, visited_columns, trivial_fix)

        if repaired:
            return row["Net Change In Cash"] - row["Effect of Forex Changes on Cash"] - row["Cash Used/Provided by Financing Activities"] - row["Cash Used for Investing Activites"]

        # Fix 2
        repaired = try_repair_column(["Net Income", "Depreciation and Amortization (Cash Flow)", "Deferred Income Tax", "Stock Based Compensation", "Change in Working Capital", "Other Non-Cash Items"],row, visited_columns, trivial_fix)

        if repaired:
            return row["Net Income"] + row["Depreciation and Amortization (Cash Flow)"] + row["Deferred Income Tax"] + row["Stock Based Compensation"] + row["Change in Working Capital"] + row["Other Non-Cash Items"]
    
    # Total Stockholders Equity
    elif col == "Total Stockholders Equity":
        repaired = try_repair_column(["Total Assets", "Total Liabilities"],row, visited_columns, trivial_fix)

        if repaired:
            return row["Total Assets"] - row["Total Liabilities"]
    
    # Free Cash Flow
    elif col == "Free Cash Flow":
        repaired = try_repair_column(["Cash Provided by Operating Activities", "CAPEX"],row, visited_columns, trivial_fix)

        if repaired:
            return row["Cash Provided by Operating Activities"] + row["CAPEX"]

    # Total Assets
    elif col == "Total Assets":
        # Fix 1
        repaired = try_repair_column(["Total Current Assets", "Total Non-Current Assets", "Other Assets"],row, visited_columns, trivial_fix)

        if repaired:
            return row["Total Current Assets"] + row["Total Non-Current Assets"] + row["Other Assets"]
        
        # Fix 2
        repaired = try_repair_column(["Total Liabilities", "Total Stockholders Equity"],row, visited_columns, trivial_fix)

        if repaired:
            return row["Total Stockholders Equity"] + row["Total Liabilities"]

    # Total Liabilities & Equity
    elif col == "Total Liabilities & Equity":
        repaired = try_repair_column(["Total Liabilities", "Total Stockholders Equity", "Minority Interest"],row, visited_columns, trivial_fix)

        if repaired:
            return row["Total Liabilities"] + row["Total Stockholders Equity"] + row["Minority Interest"]

    # Total Liabilities And Stockholders Equity
    elif col == "Total Liabilities And Stockholders Equity":
        repaired = try_repair_column(["Total Liabilities", "Total Stockholders Equity"],row, visited_columns, trivial_fix)

        if repaired:
            return row["Total Liabilities"] + row["Total Stockholders Equity"]
    
    # Total Liabilities
    elif col == "Total Liabilities":
        # Fix 1
        repaired = try_repair_column(["Total Current Liabilities", "Total Non-Current Liabilities", "Other Liabilities"],row, visited_columns, trivial_fix)

        if repaired:
            return row["Total Current Liabilities"] + row["Total Non-Current Liabilities"] + row["Other Liabilities"]

        # Fix 2
        repaired = try_repair_column(["Total Liabilities & Equity", "Minority Interest", "Total Stockholders Equity"],row, visited_columns, trivial_fix)

        if repaired:
            return row["Total Liabilities & Equity"] - row["Minority Interest"] - row["Total Stockholders Equity"]

        # Fix 3
        repaired = try_repair_column(["Total Liabilities And Stockholders Equity", "Total Stockholders Equity"],row, visited_columns, trivial_fix)

        if repaired:
            return row["Total Liabilities And Stockholders Equity"] - row["Total Stockholders Equity"]

    # EPS
    elif col == "EPS":
        repaired = try_repair_column(["Net Income","Weighted Average Shares Outstanding"],row, visited_columns, trivial_fix)

        if repaired:
            return row["Net Income"] / row["Weighted Average Shares Outstanding"]

    # EPS Diluted
    elif col == "EPS Diluted":
        repaired = try_repair_column(["Net Income","Weighted Average Shares Outstanding Diluted"],row, visited_columns, trivial_fix)

        if repaired:
            return row["Net Income"] / row["Weighted Average Shares Outstanding Diluted"]
    
    # EBITDA Ratio
    elif col == "EBITDA Ratio":
        repaired = try_repair_column(["EBITDA", "Revenue"],row, visited_columns, trivial_fix)

        if repaired:
            return row["EBITDA"] / row["Revenue"]
    
    # Net Income Ratio
    elif col == "Net Income Ratio":
        repaired = try_repair_column(["Net Income", "Revenue"],row, visited_columns, trivial_fix)

        if repaired:
            return row["Net Income"] / row["Revenue"]

    # Net Income
    elif col == "Net Income":
        # Fix 1
        repaired = try_repair_column(["Income Before Tax", "Income Tax expense (Gain)"],row, visited_columns, trivial_fix)

        if repaired:
            return row["Income Before Tax"] - row["Income Tax expense (Gain)"]
        
        # Fix 2
        repaired = try_repair_column(["Net Income Ratio", "Revenue"],row, visited_columns, trivial_fix)

        if repaired:
            return row["Net Income Ratio"] * row["Revenue"]
        
        # Fix 3
        repaired = try_repair_column(["Net Income (Cash Flow)"],row, visited_columns, trivial_fix)

        if repaired:
            return row["Net Income (Cash Flow)"]
    
    # Depreciation and Amortization (Cash Flow)
    elif col == "Depreciation and Amortization (Cash Flow)":
        repaired = try_repair_column(["Net Income (Cash Flow)", "Deferred Income Tax", "Stock Based Compensation", "Change in Working Capital", "Other Non-Cash Items", "Cash Provided by Operating Activities"],row, visited_columns, trivial_fix)

        if repaired:
            return row["Cash Provided by Operating Activities"] - row["Deferred Income Tax"] - row["Stock Based Compensation"] - row["Change in Working Capital"] - row["Other Non-Cash Items"] - row["Net Income (Cash Flow)"]

    # Net Income (Cash Flow)
    elif col == "Net Income (Cash Flow)":
        # Fix 1
        repaired = try_repair_column(["Depreciation and Amortization (Cash Flow)", "Deferred Income Tax", "Stock Based Compensation", "Change in Working Capital", "Other Non-Cash Items", "Cash Provided by Operating Activities"],row, visited_columns, trivial_fix)

        if repaired:
            return row["Cash Provided by Operating Activities"] - row["Deferred Income Tax"] - row["Stock Based Compensation"] - row["Change in Working Capital"] - row["Other Non-Cash Items"] - row["Depreciation and Amortization (Cash Flow)"]
        
        # Fix 2
        repaired = try_repair_column(["Net Income Ratio", "Revenue"],row, visited_columns, trivial_fix)

        if repaired:
            return row["Net Income Ratio"] * row["Revenue"]
        
        # Fix 3
        repaired = try_repair_column(["Net Income"],row, visited_columns, trivial_fix)

        if repaired:
            return row["Net Income"]

    # Price with cum Dividends
    elif col == "Price with cum Dividends":
        repaired = try_repair_column(["Adj Close", "Dividend cum"],row, visited_columns, trivial_fix)

        if repaired:
            return row["Adj Close"] + row["Dividend cum"]

    # Adj Close
    elif col == "Adj Close":
        print("Entered Adj Close")
        repaired = try_repair_column(["Close"],row, visited_columns, trivial_fix)

        if repaired:
            return row["Close"]

    # Aplicamos el fix trivial
    if trivial_fix and col in trivial_fix_list:
        return  0

    # No tenemos implementación
    else:
        return np.nan

    

