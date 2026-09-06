import pandas as pd

CSV_PATH = "hasil statistic.csv"

df = pd.read_csv(CSV_PATH)

if "Histogram" in df.columns:
    df = df.drop(columns=["Histogram"])

df = df.round(4)

cols = df.columns.tolist()
print("| " + " | ".join(cols) + " |")
print("|" + "|".join(["---"] * len(cols)) + "|")
for _, row in df.iterrows():
    print("| " + " | ".join(str(v) for v in row.values) + " |")
