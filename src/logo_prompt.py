import re
import random

COLOR_RE = re.compile(r"#[0-9A-Fa-f]{6}|#[0-9A-Fa-f]{3}")


def _extract_hex(color) -> str:
    if isinstance(color, dict):
        color = (
            color.get("hex")
            or color.get("value")
            or color.get("code")
            or ""
        )

    color_str = str(color).strip()
    match = COLOR_RE.search(color_str)

    if match:
        return match.group(0).upper()

    return "#CCCCCC"


def _extract_color_label(color) -> str:
    if isinstance(color, dict):
        label = (
            color.get("name")
            or color.get("label")
            or color.get("description")
            or ""
        )
        return str(label).strip() or "—"

    color_str = str(color).strip()
    match = COLOR_RE.search(color_str)

    if match:
        label = color_str[match.end():].strip(" -,|;:/")
        return label or match.group(0).upper()

    return color_str or "—"


STYLE_VARIANTS = [
    "bold geometric mark with solid shapes and a strong silhouette",
    "clever negative space design with a hidden shape, two-tone",
    "continuous single line art mark",
    "modern symmetrical emblem with thick clean outlines",
    "friendly rounded symbol, simple and memorable",
    "abstract symbol built from basic geometric forms",
]


def build_logo_prompt(package: dict, include_text: bool = False) -> str:
    concept = (package.get("logo_concept") or "").strip()
    if not concept:
        concept = (package.get("visual_style") or "a simple memorable symbol").strip()

    shapes = (package.get("logo_shape_language") or "geometric").strip()

    # أسماء الألوان فقط، بدون hex
    raw_colors = package.get("color_palette") or []
    if isinstance(raw_colors, (str, dict)):
        raw_colors = [raw_colors]

    color_names = []
    for c in raw_colors[:3]:
        label = _extract_color_label(c)
        if label and label != "—" and not label.startswith("#"):
            color_names.append(label)

    color_phrase = ", ".join(color_names) if color_names else "two harmonious colors"

    style = random.choice(STYLE_VARIANTS)

    # أهم شي في أول 200 حرف (حد CLIP)
    prompt = (
        f"A professional logo symbol: {concept}. "
        f"{shapes}, {style}. "
        f"Colors: {color_phrase}. "
        f"Vector illustration on a plain white background, centered, "
        f"one single wordless emblem with generous empty space around it, "
        f"award-winning logo design, Paul Rand style simplicity."
    )

    if include_text:
        brand_name = package.get("brand_name") or ""
        prompt += f" Include the wordmark '{brand_name}' in clean typography."

    return prompt