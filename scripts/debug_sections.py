import os
import sys
# Logic to simplify imports: ensure we can import 'app'
# We assume this script is run from project root or backend dir
current = os.getcwd()
if os.path.basename(current) == 'RONIN' or os.path.basename(current) == 'P2':
    sys.path.append(os.path.join(current, 'backend'))
elif os.path.basename(current) == 'backend':
    sys.path.append(current)
    
from app.services.parser import IBKRParser

def inspect_sections():
    parser = IBKRParser()
    data_dir = os.path.join("backend", "data")
    
    if not os.path.exists(data_dir):
        print("No data dir")
        return

    csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
    if not csv_files:
        print("No CSV files found")
        return

    print(f"Found files: {csv_files}")

    for f in csv_files:
        path = os.path.join(data_dir, f)
        print(f"\n--- Parsing {f} ---")
        sections = parser.parse_csv(path)
        print(f"Sections found: {list(sections.keys())}")
        
        # Look for likely candidates
        candidates = ['Forex Balances', 'Cash Report', 'Net Asset Value', 'Cash']
        for key in sections:
            if any(c in key for c in candidates):
                print(f"!!! FOUND CANDIDATE: {key} !!!")
                df = sections[key]
                print(df.head().to_string())
                print(f"Columns: {df.columns.tolist()}")

if __name__ == "__main__":
    inspect_sections()
