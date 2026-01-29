import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

print("Attempting to import backend.app.main...")
try:
    from backend.app.main import app
    print("Import successful!")
except Exception as e:
    print(f"Import failed: {e}")
    import traceback
    traceback.print_exc()
