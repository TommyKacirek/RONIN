import pandas as pd
from backend.app.services.reconstructor import PortfolioReconstructor
from datetime import datetime

# Mock Trade similar to user request:
# "Bought 100 EVO on 2023-05-01 at 900 SEK"
mock_data = {
    'DataDiscriminator': ['Order'],
    'Symbol': ['EVO'],
    'Date/Time': ['2023-05-01 10:00:00'],
    'Quantity': [100.0],
    'T. Price': [900.0],
    'Currency': ['SEK'],
    'Asset Category': ['Stocks']
}

df = pd.DataFrame(mock_data)

print("--- Running Reconstruction Test ---")
reconstructor = PortfolioReconstructor()
# Force cache check or ensure rate is what we expect?
# We saw rate was ~2.0704 previously.

result = reconstructor.reconstruct(df)

if 'EVO' in result:
    pos = result['EVO']
    qty = pos['quantity']
    cost_czk = pos['cost_basis_czk']
    print(f"Position: {qty} EVO")
    print(f"Cost Basis CZK: {cost_czk:.2f}")
    
    # Expected: 100 * 900 * 2.0704 = 186336
    expected_rate = 2.0704
    expected_cost = 100 * 900 * expected_rate
    print(f"Expected (approx): {expected_cost:.2f}")
    
    if abs(cost_czk - expected_cost) < 500: # Allow slight diff in rate
        print("SUCCESS: Calculation matches expected logic.")
    else:
        print("FAILURE: Major discrepancy.")
else:
    print("FAILURE: EVO not found in result.")
