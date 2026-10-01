import re


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


def build_logo_prompt(package: dict, include_text: bool = False) -> str:
    brand_name = package.get("brand_name") or "Brand"
    visual_style = package.get("visual_style") or "minimalist modern brand identity"
    typography = package.get("typography") or "clean geometric typography mood"
    traits = package.get("personality_traits") or []

    if isinstance(traits, str):
        traits = [t.strip() for t in traits.split(",") if t.strip()]

    raw_colors = package.get("color_palette") or []

    if isinstance(raw_colors, str):
        raw_colors = [raw_colors]

    if isinstance(raw_colors, dict):
        raw_colors = [raw_colors]

    color_parts = []

    for c in raw_colors:
        hex_code = _extract_hex(c)
        label = _extract_color_label(c)
        color_parts.append(f"{hex_code} {label}")

    color_phrase = ", ".join(color_parts[:5]) if color_parts else "balanced professional palette"

    trait_phrase = ", ".join(traits[:5]) if traits else "modern, memorable, professional"

    prompt = (
        f"Professional logo mark for {brand_name}, "
        f"{visual_style}, "
        f"brand personality: {trait_phrase}, "
        f"use color palette: {color_phrase}, "
        f"typography mood: {typography}, "
        f"minimalist iconic symbol, flat vector, clean geometry, centered composition, "
        f"white background, high contrast, scalable brand identity, ad-ready, "
        f"no watermark, no mockup, no realistic photo, no 3d render"
    )

    if include_text:
        prompt += f", include the brand name {brand_name} as clean readable typography"
    else:
        prompt += ", no text, no letters, no words"

    return prompt