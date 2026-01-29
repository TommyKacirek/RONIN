import requests
import json

r = requests.get("http://localhost:8000/api/portfolio")
data = r.json()
kpi = data['kpi']

print("Current KPI Data Structure:")
print("=" * 60)
for key, value in kpi.items():
    if isinstance(value, (int, float)):
        print(f"{key}: {value:,.2f}")
    else:
        print(f"{key}: {value}")
