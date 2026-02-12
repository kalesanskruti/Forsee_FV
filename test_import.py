import sys
import os
sys.path.insert(0, os.getcwd()) # Ensure cwd is in path
print(f"CWD: {os.getcwd()}")
try:
    from api.api import api_router
    print("✅ Import successful")
except Exception as e:
    print("❌ Import failed")
    import traceback
    traceback.print_exc()
