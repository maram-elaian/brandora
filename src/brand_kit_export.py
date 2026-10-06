from PIL import Image, ImageDraw, ImageFont
import textwrap
from matplotlib import font_manager
from src.logo_prompt import _extract_hex, _extract_color_label


def draw_wrapped(draw, x, y, text, font, fill, width=55, line_h=50):
    for line in textwrap.wrap(str(text), width=width):
        draw.text((x, y), line, font=font, fill=fill)
        y += line_h
    return y


def export_brand_kit(package: dict, logo_image):
    W, H = 1800, 2400

    card = Image.new("RGB", (W, H), "white")
    draw = ImageDraw.Draw(card)

    font_regular = font_manager.findfont(
        font_manager.FontProperties(family="DejaVu Sans", weight="normal")
    )
    font_bold = font_manager.findfont(
        font_manager.FontProperties(family="DejaVu Sans", weight="bold")
    )

    font_title = ImageFont.truetype(font_bold, 96)
    font_body = ImageFont.truetype(font_regular, 48)
    font_small = ImageFont.truetype(font_regular, 28)

    # Logo
    y = 80
    if logo_image is not None:
        logo_resized = logo_image.resize((600, 600), Image.Resampling.LANCZOS)
        card.paste(logo_resized, ((W - 600) // 2, y))
        y += 680

    # Brand Name
    name = package.get("brand_name", "—")
    draw.text((W // 2, y), name, font=font_title, fill="black", anchor="mm")
    y += 120

    # Tagline
    tagline = package.get("tagline", "—")
    draw.text((W // 2, y), tagline, font=font_body, fill="#666666", anchor="mm")
    y += 120

    # Color Palette
    colors = package.get("color_palette", [])
    box_size = 120
    gap = 40

    color_data = []
    for c in colors[:5]:
        color_data.append((_extract_hex(c), _extract_color_label(c)))

    total_width = len(color_data) * box_size + max(0, len(color_data) - 1) * gap
    x_start = (W - total_width) // 2

    for i, (hex_code, label) in enumerate(color_data):
        x = x_start + i * (box_size + gap)

        draw.rounded_rectangle(
            [x, y, x + box_size, y + box_size],
            radius=20, fill=hex_code, outline="#dddddd", width=3,
        )
        draw.text((x + box_size // 2, y + box_size + 35), label,
                  font=font_small, fill="black", anchor="ma")
        draw.text((x + box_size // 2, y + box_size + 80), hex_code,
                  font=font_small, fill="#666666", anchor="ma")

    y += 300

    # Typography (مع لفّ النص)
    y = draw_wrapped(draw, 100, y, f"Font: {package.get('typography', '—')}",
                     font_small, "black")
    y += 30

    # Visual Style (مع لفّ النص)
    draw_wrapped(draw, 100, y, f"Style: {package.get('visual_style', '—')}",
                 font_small, "black")

    return card