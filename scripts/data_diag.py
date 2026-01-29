
import os
import sys
sys.path.append(os.getcwd())
from backend.app.services.parser import IBKRParser

data_dir = "backend/data"
found_files = [os.path.join(data_dir, f) for f in os.listdir(data_dir) if f.endswith('.csv')]
parser = IBKRParser()

for f in found_files:
    print(f"File: {f}")
    data = parser.parse_csv(f)
    for section, df in data.items():
        print(f" Section: {section}, Rows: {len(df)}")
        print(f" Cols: {list(df.columns)}")
        if not df.empty:
            print(f" Categories: {df['Asset Category'].unique() if 'Asset Category' in df.columns else 'N/A'}")
    print("-" * 20)
