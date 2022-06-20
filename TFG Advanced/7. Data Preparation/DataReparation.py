import pandas as pd
import multiprocessing
from DataReparationAuxFunctions import reconstructDf
import os

# Arregla los fundamentales.
# Requiere las funciones auxiliares de DataReparationAuxFunctions.py

def multiprocess_reconstructDf(ticker):

    fundamental_data = pd.read_csv("7. Data Preparation\\CleanedFundamentals\\"+ticker+".csv", index_col=0)

    if not reconstructDf(fundamental_data.copy(), ticker, trivial_fix=True).empty:
        # Solo aplicamos fix normal si después del fix trivial el dataframe no está vacío
        reconstructDf(fundamental_data.copy(), ticker, trivial_fix=False)
    

if __name__ == '__main__':
    # Información básica de todos los tickers
    basic_data = pd.read_csv("7. Data Preparation\\Basic_information.csv", index_col=0)

    pool = multiprocessing.Pool(4)
    # Repara -> Aplica fix trivial -> Vuelve a reparar
    pool.map(multiprocess_reconstructDf, basic_data["Ticker"].tolist())
    pool.close()

    print("Acabado el arreglo de datos.")

    
    print("Comenzando eliminación de tickers sin datos en 'basic_data' ...")

    # Eliminamos de basic data los tickers que ya no tienen datos
    for index, row in basic_data.iterrows():
        ticker = row["Ticker"]

        if not os.path.exists("7. Data Preparation\\CleanedFundamentalsNormal&TrivialFix\\"+ticker+".csv"):
            basic_data = basic_data.drop(index)
            print("Se ha eliminado el ticker {}".format(ticker))

    
    basic_data.to_csv("7. Data Preparation\\Basic_information_repaired.csv", index=False)




    