from backend.app.services.parser import IBKRParser
import os

files = os.listdir("backend/data")
csv_files = [f for f in files if f.endswith(".csv")]

if not csv_files:
    print("No CSVs found")
else:
    fpath = os.path.join("backend/data", csv_files[0])
    print(f"Inspecting {fpath}...")
    
    parser = IBKRParser()
    data = parser.parse_csv(fpath)
    
    if "Trades" in data:
        print("\n--- Trades Columns ---")
        print(list(data["Trades"].columns))
        print("Sample Row:")
        print(data["Trades"].iloc[0].to_dict())
    else:
        print("Trades section not found")

    if "Open Positions" in data: # Section name might vary
        print("\n--- Open Positions Columns ---")
        print(list(data["Open Positions"].columns))
    else:
        print("Open Positions section not found (checking keys...)")
        print(data.keys())
