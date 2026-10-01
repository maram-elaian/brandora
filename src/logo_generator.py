import os
import re

from PIL import Image, ImageDraw, ImageFont


DEFAULT_COLORS = ["#2E5A88", "#D98E35", "#4A5D4E"]

COLOR_RE = re.compile(r"#[0-9A-Fa-f]{6}|#[0-9A-Fa-f]{3}")


def _normalize_hex(hex_value: str) -> str:
    hex_value = hex_value.strip().upper()

    if hex_value.startswith("#") and len(hex_value) == 4:
        short = hex_value[1:]
        return "#" + "".join(ch * 2 for ch in short)

    return hex_value


def _extract_colors(prompt: str):
    matches = COLOR_RE.findall(prompt)
    colors = [_normalize_hex(m) for m in matches]

    # إزالة التكرار مع الحفاظ على الترتيب
    seen = set()
    unique_colors = []

    for c in colors:
        if c not in seen:
            seen.add(c)
            unique_colors.append(c)

    if not unique_colors:
        return DEFAULT_COLORS[:]

    while len(unique_colors) < 3:
        unique_colors.append(DEFAULT_COLORS[len(unique_colors) % len(DEFAULT_COLORS)])

    return unique_colors[:3]


def _extract_brand_name(prompt: str) -> str:
    match = re.search(
        r"for\s+['\"]?([^,'\"\n]+?)['\"]?\s*(?:,|\n|$)",
        prompt,
        flags=re.IGNORECASE
    )

    if match:
        return match.group(1).strip()

    return "Brand"


def _initials(name: str) -> str:
    parts = re.findall(r"[A-Za-z0-9]+", name)

    if not parts:
        return "B"

    return "".join(p[0] for p in parts[:2]).upper()


def _hex_to_rgba(hex_code: str, alpha: int = 255):
    hex_code = _normalize_hex(hex_code).lstrip("#")

    if len(hex_code) == 3:
        hex_code = "".join(ch * 2 for ch in hex_code)

    r = int(hex_code[0:2], 16)
    g = int(hex_code[2:4], 16)
    b = int(hex_code[4:6], 16)

    return (r, g, b, alpha)


def _load_font(size: int):
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "C:\\Windows\\Fonts\\arialbd.ttf",
    ]

    for path in font_paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue

    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def _placeholder_logo(prompt: str, size: int = 1024) -> Image.Image:
    colors = _extract_colors(prompt)
    brand_name = _extract_brand_name(prompt)
    initials = _initials(brand_name)

    base = Image.new("RGBA", (size, size), (255, 255, 255, 255))
    overlay = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw_overlay = ImageDraw.Draw(overlay)

    cx = size // 2
    cy = size // 2

    radius = int(size * 0.22)
    offset = int(size * 0.13)

    positions = [
        (cx - offset, cy - offset),
        (cx + offset, cy - offset),
        (cx, cy + offset),
    ]

    for color, pos in zip(colors, positions):
        x, y = pos
        draw_overlay.ellipse(
            [x - radius, y - radius, x + radius, y + radius],
            fill=_hex_to_rgba(color, alpha=150)
        )

    base = Image.alpha_composite(base, overlay)
    draw = ImageDraw.Draw(base)

    central_radius = int(size * 0.16)
    draw.ellipse(
        [
            cx - central_radius,
            cy - central_radius,
            cx + central_radius,
            cy + central_radius,
        ],
        fill=(255, 255, 255, 255),
        outline=_hex_to_rgba(colors[0], alpha=255),
        width=max(4, int(size * 0.01)),
    )

    font = _load_font(int(size * 0.11))
    bbox = draw.textbbox((0, 0), initials, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]

    draw.text(
        (cx - tw / 2 - bbox[0], cy - th / 2 - bbox[1]),
        initials,
        fill=_hex_to_rgba(colors[0], alpha=255),
        font=font,
    )

    return base.convert("RGB")


def generate_logo(prompt: str, size: int = 1024):
    """
    حالياً placeholder آمن.

    لاحقاً يمكن استبداله بـ:
    - FLUX
    - Qwen-Image 2.1
    - Playground v2.5
    """
    backend = os.getenv("BRANDORA_LOGO_BACKEND", "placeholder").lower()

    if backend == "placeholder":
        return _placeholder_logo(prompt, size=size)

    raise ValueError(
        "Unsupported BRANDORA_LOGO_BACKEND. "
        "Use 'placeholder' or implement your own image backend."
    )