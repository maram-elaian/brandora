import sys, json, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.brand_package import build_brand_package

brief = json.loads(sys.argv[1])
package = build_brand_package(brief)
print("RESULT_JSON:" + json.dumps(package))
