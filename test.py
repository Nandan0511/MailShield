import traceback

try:
    from ui import multi_insights
    print("OK")
except Exception:
    traceback.print_exc()