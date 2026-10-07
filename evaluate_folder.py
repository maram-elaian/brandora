"""
يقرأ مجلد results/ ويقيّم كل اللوجوهات بـ CLIP، ثم يكتب:
    results/report.csv   (نتيجة كل لوجو)
    results/summary.md   (ملخص جاهز للتقرير)

التشغيل:
    python evaluate_folder.py
    python evaluate_folder.py results        # مجلد مختلف
"""
import csv
import json
import os
import sys

import torch
from PIL import Image

from src.clip_eval import evaluate_logo, _similarities, _concept_text

ROOT = sys.argv[1] if len(sys.argv) > 1 else "results"


def load_items():
    """يرجع قائمة عناصر: dict فيها brief و package و الصورتين."""
    items = []
    for brief_dir in sorted(os.listdir(ROOT)):
        bpath = os.path.join(ROOT, brief_dir)
        if not os.path.isdir(bpath):
            continue
        for n in sorted(os.listdir(bpath)):
            folder = os.path.join(bpath, n)
            pkg_file = os.path.join(folder, "package.json")
            if not os.path.exists(pkg_file):
                continue
            with open(pkg_file, encoding="utf-8") as f:
                data = json.load(f)
            items.append({
                "brief": brief_dir,
                "id": n,
                "package": data["package"],
                "raw": Image.open(os.path.join(folder, "logo_raw.png")),
                "final": Image.open(os.path.join(folder, "logo.png")),
            })
    return items


def margin(logo, package, all_packages):
    """فرق تشابه اللوجو مع فكرته عن متوسط تشابهه مع أفكار البراندات الأخرى."""
    others = [p for p in all_packages if p is not package]
    sims = _similarities(logo, [_concept_text(package)] + [_concept_text(p) for p in others])
    return float(sims[0] - sims[1:].mean())


def avg(rows, key):
    vals = [r[key] for r in rows if r[key] is not None]
    return sum(vals) / len(vals) if vals else float("nan")


def main():
    items = load_items()
    if not items:
        print("ما لقيت نتائج في", ROOT)
        return

    all_packages = [it["package"] for it in items]
    chance = 1 / len(all_packages)
    rows = []

    for it in items:
        for version in ("raw", "final"):
            img = it[version]
            r = evaluate_logo(img, it["package"], all_packages)
            r["margin"] = round(margin(img, it["package"], all_packages), 4)
            r["retrieval_ok"] = int(r["retrieval_ok"])
            r.update({"brief": it["brief"], "id": it["id"], "version": version})
            rows.append(r)
        print("evaluated:", it["brief"], it["id"], it["package"].get("brand_name"))

    fields = ["brief", "id", "version", "brand", "concept_score", "margin",
              "retrieval_ok", "text_free", "palette_dist"]
    with open(os.path.join(ROOT, "report.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r[k] for k in fields})

    lines = [
        "# Brandora: CLIP Evaluation Summary",
        "",
        f"- Number of logos: **{len(items)}**",
        f"- Random-chance retrieval accuracy: **{chance:.3f}**",
        "",
        "| Version | Concept score | Margin | Retrieval acc. | Text-free | Palette dist. |",
        "|---|---|---|---|---|---|",
    ]
    for version, label in (("raw", "FLUX raw"), ("final", "After palette")):
        sub = [r for r in rows if r["version"] == version]
        lines.append(
            f"| {label} | {avg(sub, 'concept_score'):.3f} | {avg(sub, 'margin'):+.3f} | "
            f"{avg(sub, 'retrieval_ok'):.3f} | {avg(sub, 'text_free'):.3f} | "
            f"{avg(sub, 'palette_dist'):.1f} |"
        )

    lines += [
        "",
        "## How to read",
        "- **Retrieval acc.** must be well above random chance.",
        "- **Margin** above 0 means the logo matches its own concept more than other brands' concepts.",
        "- **Text-free** close to 1 means no accidental letters.",
        "- **Palette dist.** close to 0 means the logo uses Qwen's colors.",
    ]

    with open(os.path.join(ROOT, "summary.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print("\n".join(lines))


if __name__ == "__main__":
    main()
