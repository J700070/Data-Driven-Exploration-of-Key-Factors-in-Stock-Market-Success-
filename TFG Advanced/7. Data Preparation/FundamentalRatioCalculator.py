import pandas as pd
import multiprocessing
import numpy as np


def calculateGrowthMetrics(df):
    for column in df.columns:
        df[column+" growth year over year"] = df[column] / df[column].shift(1) - 1
        df[column+" growth 3 year average"] = (df[column+" growth year over year"] + df[column+" growth year over year"].shift(1) + df[column+" growth year over year"].shift(2))  / 3
        df[column+" growth 5 year average"] = (df[column+" growth year over year"] + df[column+" growth year over year"].shift(1) + df[column+" growth year over year"].shift(2) + df[column+" growth year over year"].shift(3) + df[column+" growth year over year"].shift(4))  / 5
        df[column+" growth 10 year average"] = (df[column+" growth year over year"] + df[column+" growth year over year"].shift(1) + df[column+" growth year over year"].shift(2) + df[column+" growth year over year"].shift(3) + df[column+" growth year over year"].shift(4) + df[column+" growth year over year"].shift(5) + df[column+" growth year over year"].shift(6) + df[column+" growth year over year"].shift(7) + df[column+" growth year over year"].shift(8) + df[column+" growth year over year"].shift(9) + df[column+" growth year over year"].shift(10))  / 10

    # Quitamos infinitos
    df = df.replace([np.inf, -np.inf], np.nan)

def currency_converter(df):
    exclude_list = ["Gross Profit Ratio","EBITDA Ratio","Operating Income Ratio","Income Before Tax Ratio","Net Income Ratio","Weighted Average Shares Outstanding","Weighted Average Shares Outstanding Diluted"
                    ,"Open","Close","Adj Close","Volume","Dividend","Dividend Cum","Price with cum Dividends","Forex Rate"]
    for column in df.columns:
        if column in exclude_list:
            continue
        df[column] *= df["Forex Rate"]


def FundamentalCalculator(ticker):

    # Abrimos los fundamentales con el precio
    fundamental_data = pd.read_csv("CleanedFundamentalsNormal&TrivialFix\\"+ticker+".csv", index_col=0)

    # Si hace falta hacer conversión de moneda, la hacemos.
    if "Forex Rate" in fundamental_data.columns:
        currency_converter(fundamental_data)

    # ===================================================================================================================================
    #                                                     AÑADIR RatioS FINANCIEROS
    # ===================================================================================================================================
    shares = fundamental_data["Weighted Average Shares Outstanding"]
    fundamental_data["Tax Rate"] = fundamental_data["Income Tax expense (Gain)"] / fundamental_data["Income Before Tax"]
    fundamental_data["Deferred Revenue"] = fundamental_data["Deferred Revenue (Current)"] + fundamental_data["Deferred Revenue (Non-Current)"]
    fundamental_data["Net Interest Income"] = fundamental_data["Interest Income"] - fundamental_data["Interest Expense (Gain)"]
    fundamental_data["Free Cash Flow to the Firm"] = fundamental_data["Free Cash Flow"] - fundamental_data["Interest Expense (Gain)"] * (1 - fundamental_data["Tax Rate"])
    fundamental_data["Tangible Assets"] = fundamental_data["Total Assets"] - fundamental_data["Goodwill and Intangible Assets"]
    fundamental_data["Adjusted Operating Income"] = fundamental_data["Gross Profit"] - fundamental_data["Selling, General and Administrative Exp."] - fundamental_data["Depreciation and Amortization"]
    fundamental_data["EBIT"] = fundamental_data["Income Before Tax"] + fundamental_data["Interest Expense (Gain)"]
    fundamental_data["EBITDA"] = fundamental_data["EBIT"] + fundamental_data["Depreciation and Amortization"]
    fundamental_data["Operating Cash Flow"] = fundamental_data["Operating Income"] + fundamental_data["Depreciation and Amortization"] - fundamental_data["Income Tax expense (Gain)"] + fundamental_data["Change in Working Capital"]
    fundamental_data["Common Book Value"] = fundamental_data["Total Stockholders Equity"].sub(fundamental_data["Preferred Stock"], fill_value=0)
    fundamental_data["Tangible Book Value"] = fundamental_data["Total Stockholders Equity"].sub(fundamental_data["Goodwill and Intangible Assets"], fill_value=0)
    fundamental_data["Common Tangible Book Value"] = fundamental_data["Tangible Book Value"].sub(fundamental_data["Preferred Stock"], fill_value=0)



    # ==========================================        Ratios        ===============================================
    fundamental_data["Free Cash Flow Ratio"] = fundamental_data["Free Cash Flow"] / fundamental_data["Revenue"]
    fundamental_data["Selling, General and Administrative Exp. Ratio"] = fundamental_data["Selling, General and Administrative Exp."] / fundamental_data["Revenue"]
    fundamental_data["Research and Development Exp. Ratio"] = fundamental_data["Research and Development Exp."] / fundamental_data["Revenue"]
    fundamental_data["Other Expenses Ratio"] = fundamental_data["Other Expenses"] / fundamental_data["Revenue"]
    fundamental_data["Net Interest IncomeRatio"] = fundamental_data["Net Interest Income"] / fundamental_data["Revenue"]
    fundamental_data["Depreciation and Amortization Ratio"] = fundamental_data["Depreciation and Amortization"] / fundamental_data["Revenue"]
    #EBIT margin
    fundamental_data["EBIT Margin"] = fundamental_data["EBIT"] / fundamental_data["Revenue"]
    # Adjusted Operating Margin
    fundamental_data["Adjusted Operating Margin"] = fundamental_data["Adjusted Operating Income"] / fundamental_data["Revenue"]
    # Operating Cash Flow margin
    fundamental_data["Operating Cash Flow Margin"] = fundamental_data["Operating Cash Flow"] / fundamental_data["Revenue"]
    # Cost-to-Income Ratio
    fundamental_data["Cost-to-Income Ratio"] = fundamental_data["Operating Expenses"] / fundamental_data["Operating Income"]
    # Operating Expense Ratio
    fundamental_data["Operating Expense Ratio"] = fundamental_data["Operating Expenses"] / fundamental_data["Revenue"]
    # Selling General & Administrative expenses/ Gross Profit
    fundamental_data["Selling, General and Administrative Exp. Ratio"] = fundamental_data["Selling, General and Administrative Exp."] / fundamental_data["Gross Profit"]

    # ==========================================        MÉTRICAS PER SHARE        ===============================================

    fundamental_data["Revenue per share"] = fundamental_data["Revenue"] / shares
    fundamental_data["Operating Income per share"] = fundamental_data["Operating Income"] / shares
    fundamental_data["FCF per share"] = fundamental_data["Free Cash Flow"] / shares
    fundamental_data["CAPEX per share"] = fundamental_data["CAPEX"] / shares
    fundamental_data["Book value per share"] = fundamental_data["Total Stockholders Equity"] / shares
    fundamental_data["Dividends per share"] = fundamental_data["Dividends Paid"] / shares



    

    # =======================================     MÉTRICAS DE SALUD FINANCIERA       ===============================================
    fundamental_data["Total Debt"] = fundamental_data["Short-Term Debt"].add(fundamental_data["Long-Term Debt"], fill_value=0)
    fundamental_data["Financial leverage"] = fundamental_data["Total Debt"] / fundamental_data["Total Stockholders Equity"]

    # Calculamos el Cash to Debt Ratio
    fundamental_data["Cash to Debt Ratio"] = fundamental_data["Cash and Cash Equivalents"] / fundamental_data["Total Debt"]
    if np.inf in fundamental_data["Cash to Debt Ratio"].values:
        fundamental_data["Cash to Debt Ratio"] = fundamental_data["Cash to Debt Ratio"].replace(np.inf, 99)

    fundamental_data["Cash & Investments"] = fundamental_data["Cash and Short-Term Investments"]+fundamental_data["Investments"]
    fundamental_data["Cash & Investments to Debt Ratio"] = fundamental_data["Cash & Investments"] / fundamental_data["Total Debt"]
    if np.inf in fundamental_data["Cash & Investments to Debt Ratio"].values:
        fundamental_data["Cash & Investments to Debt Ratio"] = fundamental_data["Cash & Investments to Debt Ratio"].replace(np.inf, 99)

        
    fundamental_data["Net Debt"] = fundamental_data["Total Debt"] - fundamental_data["Cash and Short-Term Investments"]
    fundamental_data["Net Debt w/Investments"] = fundamental_data["Net Debt"] - fundamental_data["Investments"]
    fundamental_data["Working Capital"] = fundamental_data["Total Current Assets"] - fundamental_data["Total Current Liabilities"]
    fundamental_data["Current Ratio"] = fundamental_data["Total Current Assets"] / fundamental_data["Total Current Liabilities"]
    fundamental_data["Quick Ratio"] = (fundamental_data["Cash and Cash Equivalents"] - fundamental_data["Accounts Receivable"])/ fundamental_data["Total Current Liabilities"]
    fundamental_data["Cash to Current Assets"] = fundamental_data["Cash and Short-Term Investments"] / fundamental_data["Total Current Assets"]
    fundamental_data["Cash to Assets"] = fundamental_data["Cash and Short-Term Investments"] / fundamental_data["Total Assets"]
    fundamental_data["Debt to Equity"] = fundamental_data["Total Current Liabilities"] / fundamental_data["Total Stockholders Equity"]
    fundamental_data["Debt to Assets"] = fundamental_data["Total Current Liabilities"] / fundamental_data["Total Assets"]
    fundamental_data["Interest Coverage"] = fundamental_data["EBIT"] / fundamental_data["Interest Expense (Gain)"]
    # Ponemos valor 99 para reflejar que la situación es buena
    if np.inf in fundamental_data["Interest Coverage"].values:
        fundamental_data["Interest Coverage"] = fundamental_data["Interest Coverage"].replace(np.inf, 99)
    elif -np.inf in fundamental_data["Interest Coverage"].values:
        fundamental_data["Interest Coverage"] = fundamental_data["Interest Coverage"].replace(-np.inf, np.nan)

    #Current Liability Coverage Ratio
    fundamental_data["Current Liability Coverage Ratio"] = (fundamental_data["Operating Cash Flow"] - fundamental_data["Dividends Paid"])/ fundamental_data["Total Current Liabilities"]
    # Cash ratio
    fundamental_data["Cash Ratio"] = fundamental_data["Cash and Short-Term Investments"] / fundamental_data["Total Current Liabilities"]
    # Net Working Capital to Assets
    fundamental_data["Net Working Capital to Assets"] = fundamental_data["Working Capital"] / fundamental_data["Total Assets"]
    # Long term debt ratio
    fundamental_data["Long Term Debt Ratio"] = fundamental_data["Total Non-Current Liabilities"] / fundamental_data["Total Assets"]
    #Total Debt/ Assets
    fundamental_data["Total Debt/ Assets"] = fundamental_data["Total Debt"] / fundamental_data["Total Assets"]
    #Net Debt/ Assets
    fundamental_data["Net Debt/ Assets"] = fundamental_data["Net Debt"] / fundamental_data["Total Assets"]
    #Total debt / Equity
    fundamental_data["Total Debt/ Equity"] = fundamental_data["Total Debt"] / fundamental_data["Total Stockholders Equity"]
    #Liabilities / Equity
    fundamental_data["Total Liabilities/ Equity"] = fundamental_data["Total Liabilities"] / fundamental_data["Total Stockholders Equity"]
    # Net Debt / Equity
    fundamental_data["Net Debt/ Equity"] = fundamental_data["Net Debt"] / fundamental_data["Total Stockholders Equity"]
    # Equity ratio
    fundamental_data["Equity Ratio"] = fundamental_data["Total Stockholders Equity"] / fundamental_data["Total Assets"]
    # Equity multiplier
    fundamental_data["Equity Multiplier"] = fundamental_data["Total Assets"] / fundamental_data["Total Stockholders Equity"]
    # Debt / Tangible Book value
    fundamental_data["Debt/ Tangible Book Value"] = fundamental_data["Total Liabilities"] / fundamental_data["Tangible Book Value"]
    # Net debt / EBITDA
    fundamental_data["Net Debt/ EBITDA"] = fundamental_data["Net Debt"] / fundamental_data["EBITDA"]
    # Cash to Debt
    fundamental_data["Cash to Debt"] = fundamental_data["Cash and Short-Term Investments"] / fundamental_data["Total Debt"]
    # Cash Flow Coverage Ratio
    fundamental_data["Cash Flow Coverage Ratio"] = fundamental_data["Operating Cash Flow"] / fundamental_data["Total Liabilities"]
    # Free Cash Flow / Long Term Debt
    fundamental_data["Free Cash Flow/ Long Term Debt"] = fundamental_data["Free Cash Flow"] / (fundamental_data["Long-Term Debt"] + fundamental_data["Capital Lease Obligations"])
    # Debt leverage ratio
    fundamental_data["Debt Leverage Ratio"] = fundamental_data["Total Liabilities"] / fundamental_data["EBITDA"]
    # Interest expense to Debt ratio
    fundamental_data["Interest Expense to Debt Ratio"] = fundamental_data["Interest Expense (Gain)"] / fundamental_data["Total Debt"]
    # Cash Sales
    fundamental_data["Cash Sales"] = fundamental_data["Revenue"] - fundamental_data["Accounts Receivable"]
    # Cash revenue adjustment
    fundamental_data["Cash Revenue Adjustment"] = fundamental_data["Accounts Receivable"] / fundamental_data["Deferred Revenue"]
    # CFO / Net income
    fundamental_data["CFO/ Net Income"] = fundamental_data["Operating Cash Flow"] / fundamental_data["Net Income"]


    # =======================================     MÉTRICAS DE RENTABILIDAD       ===============================================
     
    fundamental_data["Return on Equity"] = fundamental_data["Net Income"] / fundamental_data["Common Book Value"]



    fundamental_data["NOPAT"] = fundamental_data["Operating Income"] * (1 - fundamental_data["Tax Rate"])
    fundamental_data["Invested Capital"] = fundamental_data["Total Liabilities And Stockholders Equity"].add(-fundamental_data["Total Current Liabilities"], fill_value=0)
    fundamental_data["Return on Invested Capital"] = fundamental_data["NOPAT"] / fundamental_data["Invested Capital"]
    fundamental_data["Capital Employed"] = fundamental_data["Total Assets"] - fundamental_data["Total Current Liabilities"]

    fundamental_data["ROCE"] = fundamental_data["EBIT"] / fundamental_data["Capital Employed"]
    fundamental_data["CFROI"] = fundamental_data["Operating Cash Flow"] / fundamental_data["Capital Employed"]

    fundamental_data["Asset Turnover Ratio"] = fundamental_data["Revenue"] / fundamental_data["Total Assets"]
    fundamental_data["Inventory Turnover"] = fundamental_data["COGS"] / fundamental_data["Inventory (Balance)"]
    fundamental_data["Receivables Turnover"] = fundamental_data["Revenue"] / fundamental_data["Accounts Receivable"]
    fundamental_data["Cash Turnover Ratio"] = fundamental_data["Revenue"] / fundamental_data["Cash and Cash Equivalents"]
    fundamental_data["Gross Profitability Ratio"] = fundamental_data["Gross Profit"] / fundamental_data["Total Assets"]
    fundamental_data["Tangible Gross Profitability Ratio"] = fundamental_data["Gross Profit"] / fundamental_data["Tangible Assets"]
    fundamental_data["Cash Return on Invested Capital"] = fundamental_data["Free Cash Flow to the Firm"] / fundamental_data["Invested Capital"]
    fundamental_data["Adjusted Return on Capital Employed"] = fundamental_data["Adjusted Operating Income"] / fundamental_data["Capital Employed"]
    fundamental_data["Cash Return on Capital Employed"] = fundamental_data["Free Cash Flow to the Firm"] / fundamental_data["Capital Employed"]
    fundamental_data["EBIT Return on Assets"] = fundamental_data["EBIT"] / fundamental_data["Total Assets"]
    fundamental_data["EBIT Return on Tangible Assets"] = fundamental_data["EBIT"] / fundamental_data["Tangible Assets"]
    fundamental_data["Return on Assets"] = fundamental_data["NOPAT"] / fundamental_data["Total Assets"]
    fundamental_data["Return on Tangible Equity"] = fundamental_data["Net Income"] / fundamental_data["Common Tangible Book Value"]
    # Cash Return on Equity
    fundamental_data["Cash Return on Equity"] = fundamental_data["Operating Cash Flow"] / fundamental_data["Total Stockholders Equity"]
    # Return on Retained Earnings
    fundamental_data["Return on Retained Earnings"] = fundamental_data["Net Income"] / fundamental_data["Retained Earnings"]
    #R&D / Assets
    fundamental_data["R&D / Assets"] = fundamental_data["Research and Development Exp."] / fundamental_data["Total Assets"]
    #R&D / Book
    fundamental_data["R&D / Book"] = fundamental_data["Research and Development Exp."] / fundamental_data["Total Stockholders Equity"]
    # CapEx / Assets
    fundamental_data["CapEx / Assets"] = -fundamental_data["CAPEX"] / fundamental_data["Total Assets"]
    # CapEx / Fixed Assets
    fundamental_data["CapEx / Fixed Assets"] = -fundamental_data["CAPEX"] / fundamental_data["PP&E"]
    # Retained Earnings / Total Assets
    fundamental_data["Retained Earnings / Total Assets"] = fundamental_data["Retained Earnings"] / fundamental_data["Total Assets"]
    #Inventory/ Assets
    fundamental_data["Inventory / Assets"] = fundamental_data["Inventory (Balance)"] / fundamental_data["Total Assets"]
    #Accounts Receivable/ Assets
    fundamental_data["Accounts Receivable / Assets"] = fundamental_data["Accounts Receivable"] / fundamental_data["Total Assets"]

   

    # =======================================     MÉTRICAS DE REINVERSIÓN      ===============================================
    # Calculamos el Plowback Ratio
    fundamental_data["Plowback Ratio"] = (fundamental_data["Net Income"] - fundamental_data["Dividends Paid"])/ fundamental_data["Net Income"]

    # Calculamos el Dividend & Repurchase / FCF
    fundamental_data["Dividend & Repurchase / FCF"] = (fundamental_data["Dividends Paid"] - fundamental_data["Common Stock Repurchased"] - fundamental_data["Common Stock Issued"]) / fundamental_data["Free Cash Flow"]

    # Calculamos el Dividend & Repurchase / EBITDA
    fundamental_data["Dividend & Repurchase / EBITDA"] = (fundamental_data["Dividends Paid"] - fundamental_data["Common Stock Repurchased"] - fundamental_data["Common Stock Issued"]) / fundamental_data["EBITDA"]


 



    # Lo guardamos sin las columnas de crecimiento
    fundamental_data.to_csv("FinalFundamentals\\"+ticker+".csv")


    # =======================================     MÉTRICAS DE CRECIMIENTO      ===============================================
    calculateGrowthMetrics(fundamental_data)

    # Lo guardamos con las columnas de crecimiento
    fundamental_data.to_csv("FinalFundamentalsWithGrowth\\"+ticker+".csv")


if __name__ == '__main__':
    # Información básica de todos los tickers
    basic_data = pd.read_csv("Basic_information_cleaned3.csv", index_col=0)

    pool = multiprocessing.Pool(4)
    pool.map(FundamentalCalculator, basic_data.index.tolist())
    pool.close()

    print("Acabado el arreglo de datos.")

