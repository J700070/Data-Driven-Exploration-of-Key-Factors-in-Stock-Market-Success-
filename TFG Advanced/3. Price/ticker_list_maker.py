
import pathlib
import pandas as pd

df = pd.DataFrame(columns=["Ticker"])
print(df)
for path in pathlib.Path("C:\\Users\\juani\\OneDrive\\Escritorio\\Code\\TFG\\TFG Advanced\\3. Price\\HistoricalPrices").iterdir():
    if path.is_file():
        old_name = path.stem
        df.loc[df.shape[0]] = [path.stem]
print(df)
df.to_csv("3. Price\\ticker_list.csv")