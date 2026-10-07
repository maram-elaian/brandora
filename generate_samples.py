"""
يولّد عينة من البراندات ويحفظها في results/ لتقييمها لاحقاً.

التشغيل (من جذر المشروع، على Kaggle):
    python generate_samples.py

الناتج:
    results/<brief>/<n>/package.json
    results/<brief>/<n>/prompt.txt
    results/<brief>/<n>/logo_raw.png   (مخرجات FLUX الأصلية)
    results/<brief>/<n>/logo.png       (بعد تطبيق ألوان Qwen)
"""
import os
os.environ["PYTORCH_ALLOC_CONF"] = "expandable_segments:True"

import json
import re

from src.brand_package import build_brand_packages
from src.logo_prompt import build_logo_prompt
from src.logo_generator import generate_logo, apply_palette

OUT_DIR = "results"

BRIEFS = [
    {"industry": "coffee shop", "target_audience": "university students",
     "brand_purpose": "comfortable place for studying and socializing",
     "personality": ["warm", "friendly"], "tone": "casual"},
    {"industry": "streetwear", "target_audience": "Gen Z urban creatives",
     "brand_purpose": "express individuality through bold designs",
     "personality": ["bold", "rebellious"], "tone": "bold"},
    {"industry": "meditation app", "target_audience": "busy professionals",
     "brand_purpose": "help people unwind and sleep better",
     "personality": ["calm", "minimalist"], "tone": "friendly"},
    {"industry": "law firm", "target_audience": "small business owners",
     "brand_purpose": "clear and trustworthy legal advice",
     "personality": ["trustworthy", "elegant"], "tone": "formal"},
    {"industry": "children's toy store", "target_audience": "young parents",
     "brand_purpose": "toys that spark curiosity and creativity",
     "personality": ["playful", "friendly"], "tone": "playful"},
    {"industry": "fitness gym", "target_audience": "young adults",
     "brand_purpose": "build strength and community",
     "personality": ["energetic", "bold"], "tone": "bold"},
    {"industry": "luxury perfume", "target_audience": "affluent women",
     "brand_purpose": "signature scents that feel timeless",
     "personality": ["luxurious", "elegant"], "tone": "sophisticated"},
    {"industry": "organic bakery", "target_audience": "families",
     "brand_purpose": "fresh handmade bread from local ingredients",
     "personality": ["warm", "trustworthy"], "tone": "friendly"},
]


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def main():
    for brief in BRIEFS:
        name = slug(brief["industry"])
        print(f"\n=== {name} ===")
        done = [os.path.join(OUT_DIR, name, str(i), "package.json") for i in (1, 2, 3)]

        if all(os.path.exists(p) for p in done):
            print("skip (already done):", name)
            continue
        packages = build_brand_packages(brief, n=3)

        for i, pkg in enumerate(packages, start=1):
            folder = os.path.join(OUT_DIR, name, str(i))
            os.makedirs(folder, exist_ok=True)

            prompt = build_logo_prompt(pkg)

            raw = generate_logo(prompt)
            logo = apply_palette(raw, pkg.get("color_palette"))

            raw.save(os.path.join(folder, "logo_raw.png"))
            logo.save(os.path.join(folder, "logo.png"))

            with open(os.path.join(folder, "package.json"), "w", encoding="utf-8") as f:
                json.dump({"brief": brief, "package": pkg}, f,
                          ensure_ascii=False, indent=2)
            with open(os.path.join(folder, "prompt.txt"), "w", encoding="utf-8") as f:
                f.write(prompt)

            print("saved:", folder, "|", pkg.get("brand_name"))


if __name__ == "__main__":
    main()
