import re
from src.evaluator import contrast_ratio, passes_wcag_aa

BANNED_WORDS = [
    "fresh", "pure", "smart", "prime", "elite", "nova", "zen",
    "co.", "hub", "studio", "quality you can trust", "journey starts"
]

GENERIC_TAGLINE_PATTERNS = [
    "quality", "trust", "journey", "experience the", "best in",
    "your way", "made for you", "come and",
]


def evaluate_text(package: dict, industry: str) -> dict:
    name = package.get("brand_name", "").lower()
    tagline = package.get("tagline", "").lower()
    colors = package.get("color_palette", [])
    typography = package.get("typography", "")
    visual_style = package.get("visual_style", "")
    traits = package.get("personality_traits", [])

    results = {}

    # 1. خالي من الكلمات الممنوعة
    results["no_banned_words"] = not any(w in f"{name} {tagline}" for w in BANNED_WORDS)

    # 2. الاسم مش حرفي من اسم الصناعة
    industry_words = industry.lower().split()
    results["not_literal_industry"] = not any(w in name for w in industry_words if len(w) > 3)

    # 3. الشعار مش قالب عام (فحص تقريبي، مش قاطع)
    results["tagline_not_generic"] = not any(p in tagline for p in GENERIC_TAGLINE_PATTERNS)

    # 4. اكتمال JSON
    required = ["brand_name", "tagline", "color_palette", "typography", "visual_style", "personality_traits"]
    results["json_complete"] = all(package.get(f) for f in required)

    score = sum(results.values())
    results["text_score"] = f"{score}/4"
    return results


def evaluate_colors(colors: list) -> dict:
    hexes = []
    for c in colors:
        match = re.search(r'#[0-9A-Fa-f]{6}', str(c))
        hexes.append(match.group(0) if match else None)

    results = {"all_valid_hex": all(h is not None for h in hexes)}

    if results["all_valid_hex"] and len(hexes) >= 2:
        results["contrast_1_2"] = contrast_ratio(hexes[0], hexes[1])
        results["passes_wcag_1_2"] = passes_wcag_aa(hexes[0], hexes[1])
    if results["all_valid_hex"] and len(hexes) >= 3:
        results["contrast_1_3"] = contrast_ratio(hexes[0], hexes[2])
        results["passes_wcag_1_3"] = passes_wcag_aa(hexes[0], hexes[2])

    score = sum([
        results.get("all_valid_hex", False),
        results.get("passes_wcag_1_2", False),
        results.get("passes_wcag_1_3", False),
    ])
    results["color_score"] = f"{score}/3"
    return results


def print_report(package: dict, industry: str):
    print(f"\n{'='*50}")
    print(f"الاسم: {package.get('brand_name')}")
    print(f"الشعار: {package.get('tagline')}")
    print(f"{'='*50}")

    text_results = evaluate_text(package, industry)
    print("\n📝 تقييم النص (آلي):")
    for k, v in text_results.items():
        print(f"   {k}: {v}")

    color_results = evaluate_colors(package.get("color_palette", []))
    print("\n🎨 تقييم الألوان (آلي):")
    for k, v in color_results.items():
        print(f"   {k}: {v}")

    print("\n🖼️ تقييم اللوجو (يدوي — عبّيه بعينك):")
    print("   نظافة الشكل (0/1): ___")
    print("   بساطة/قابلية التمييز (0/1): ___")
    print("   خلو من نص عشوائي (0/1): ___")
    print("   اتساق مع visual_style (0/1): ___")
