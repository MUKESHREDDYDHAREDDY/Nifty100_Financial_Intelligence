import pandas as pd
from pathlib import Path

DATA_DIR = Path("data/raw")

files = list(DATA_DIR.glob("*.xlsx"))

print(f"Found {len(files)} Excel files\n")

for file in files:
    print("=" * 70)
    print(f"File: {file.name}")

    df = pd.read_excel(file)

    print("Rows:", df.shape[0])
    print("Columns:", df.shape[1])
    print("Missing values:", df.isna().sum().sum())
    print("Column names:")
    print(list(df.columns))
    print()

   # Load and inspect each file
for file in files:
    print("\n" + "=" * 60)
    print(f"File: {file.name}")

    df = pd.read_excel(file)

    print("Rows:", df.shape[0])
    print("Columns:", df.shape[1])
    print("Missing values:", df.isnull().sum().sum())

    print("Column names:")
    print(list(df.columns))

    print("Data types:")
    print(df.dtypes)

    print("First 5 rows:")
    print(df.head())