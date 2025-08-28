"""
import エラーをデバッグするスクリプト
"""
import sys
import os

print("=== Python Path Debug ===")
for i, path in enumerate(sys.path):
    print(f"{i}: {path}")

print("\n=== Working Directory ===")
print(f"Current: {os.getcwd()}")
print(f"Files: {os.listdir('.')}")

print("\n=== Backend Directory ===")
try:
    print(f"Backend files: {os.listdir('backend')}")
    print(f"Backend/src files: {os.listdir('backend/src')}")
except Exception as e:
    print(f"Backend error: {e}")

print("\n=== Import Tests ===")
try:
    from backend.src.main import app
    print("✅ main.py import success")
except Exception as e:
    print(f"❌ main.py import failed: {e}")
    import traceback
    traceback.print_exc()

try:
    from backend.src.services.lazy_service_manager import lazy_service_manager
    print("✅ lazy_service_manager import success") 
except Exception as e:
    print(f"❌ lazy_service_manager import failed: {e}")
    import traceback
    traceback.print_exc()

if __name__ == "__main__":
    pass