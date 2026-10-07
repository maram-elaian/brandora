"""
تقييم لوجوهات Brandora باستخدام CLIP.

الاستخدام:
    from src.clip_eval import evaluate_logo, evaluate_batch
    report = evaluate_logo(logo_pil, package, other_packages)

ملاحظة: يشتغل على CPU عشان ما يتزاحم مع FLUX على الـ GPU.
"""
import torch
from PIL import Image
from transformers import CLIPModel, CLIPProcessor

from src.logo_prompt import _extract_hex

_MODEL_ID = "openai/clip-vit-base-patch32"
_model = None
_proc = None


def _load():
    global _model, _proc
    if _model is None:
        _model = CLIPModel.from_pretrained(_MODEL_ID).to("cpu").eval()
        _proc = CLIPProcessor.from_pretrained(_MODEL_ID)
    return _model, _proc


@torch.inference_mode()
def _similarities(image: Image.Image, texts: list) -> torch.Tensor:
    """cosine similarity بين الصورة وكل نص."""
    model, proc = _load()
    inputs = proc(text=texts, images=image.convert("RGB"),
                  return_tensors="pt", padding=True, truncation=True)
    img = model.get_image_features(pixel_values=inputs["pixel_values"])
    txt = model.get_text_features(input_ids=inputs["input_ids"],
                                  attention_mask=inputs["attention_mask"])
    img = img / img.norm(dim=-1, keepdim=True)
    txt = txt / txt.norm(dim=-1, keepdim=True)
    return (img @ txt.T).squeeze(0)


def _concept_text(pkg: dict) -> str:
    c = pkg.get("logo_concept") or pkg.get("visual_style") or "a simple symbol"
    return f"a minimalist logo of {c}"


def evaluate_logo(logo: Image.Image, package: dict, other_packages=None) -> dict:
    """
    1) concept_score : تطابق اللوجو مع فكرة Qwen (كلما أعلى كان أفضل، عادة 0.20-0.35)
    2) retrieval_ok  : هل اللوجو أقرب لفكرته من أفكار الاقتراحات الأخرى؟ (اختبار تمييز)
    3) text_free     : احتمال إن اللوجو بدون حروف (CLIP zero-shot)
    4) palette_dist  : بعد ألوان اللوجو عن الباليت (0 = مطابق تماماً)
    """
    own = _concept_text(package)
    others = [_concept_text(p) for p in (other_packages or []) if p is not package]

    sims = _similarities(logo, [own] + others)
    concept_score = float(sims[0])
    retrieval_ok = bool(sims[0] == sims.max()) if others else None

    tf = _similarities(logo, ["a logo with no text or letters",
                              "a logo with text and letters"])
    text_free = float(torch.softmax(tf * 100, dim=0)[0])

    return {
        "brand": package.get("brand_name"),
        "concept_score": round(concept_score, 4),
        "retrieval_ok": retrieval_ok,
        "text_free": round(text_free, 3),
        "palette_dist": round(_palette_distance(logo, package), 1),
    }


def _palette_distance(logo: Image.Image, package: dict) -> float:
    """متوسط المسافة بين ألوان اللوجو الغالبة وأقرب لون في الباليت (RGB)."""
    hexes = [_extract_hex(c).lstrip("#") for c in (package.get("color_palette") or [])]
    pal = [tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) for h in hexes] + [(255, 255, 255)]
    small = logo.convert("RGB").resize((64, 64))
    total = 0.0
    for px in small.getdata():
        total += min(sum((a - b) ** 2 for a, b in zip(px, p)) ** 0.5 for p in pal)
    return total / (64 * 64)


def evaluate_batch(items: list) -> dict:
    """items = [(logo_pil, package), ...] ويرجع التقرير + المتوسطات."""
    packages = [p for _, p in items]
    rows = [evaluate_logo(img, pkg, packages) for img, pkg in items]

    n = len(rows)
    ret = [r["retrieval_ok"] for r in rows if r["retrieval_ok"] is not None]
    summary = {
        "avg_concept_score": round(sum(r["concept_score"] for r in rows) / n, 4),
        "retrieval_accuracy": round(sum(ret) / len(ret), 3) if ret else None,
        "avg_text_free": round(sum(r["text_free"] for r in rows) / n, 3),
        "avg_palette_dist": round(sum(r["palette_dist"] for r in rows) / n, 1),
    }
    return {"rows": rows, "summary": summary}
