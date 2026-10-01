import sys
import os
import json


# تقليل الضوضاء في stdout/stderr
os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.brand_package import build_brand_packages


def main():
    if len(sys.argv) < 2:
        print("RESULT_JSON:[]")
        return

    try:
        brief = json.loads(sys.argv[1])
    except Exception as e:
        print(f"ERROR parsing brief: {e}", file=sys.stderr)
        print("RESULT_JSON:[]")
        return

    try:
        packages = build_brand_packages(brief, n=3)
    except Exception as e:
        print(f"ERROR generating packages: {e}", file=sys.stderr)
        packages = []

    print("RESULT_JSON:" + json.dumps(packages, ensure_ascii=False))


if __name__ == "__main__":
    main()