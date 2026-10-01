import sys, json, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.brand_package import build_brand_packages

brief = json.loads(sys.argv[1])
packages = build_brand_packages(brief, n=3)
print("RESULT_JSON:" + json.dumps(packages))