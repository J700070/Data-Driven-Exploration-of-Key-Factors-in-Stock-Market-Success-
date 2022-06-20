
import pathlib
import pandas as pd

read_path="7. Data Preparation\\CleanedFundamentals"
write_path="7. Data Preparation\\ticker_list.csv"

df = pd.DataFrame(columns=["Ticker"])
for path in pathlib.Path(read_path).iterdir():
    if path.is_file():
        old_name = path.stem
        df.loc[df.shape[0]] = [path.stem]

df.to_csv(write_path)