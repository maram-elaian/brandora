from PIL import Image, ImageDraw, ImageFont
import textwrap
from matplotlib import font_manager
from src.logo_prompt import _extract_hex, _extract_color_label


def draw_wrapped(draw, x, y, text, font, fill, width=85, line_h=42):
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
    font_label = ImageFont.truetype(font_regular, 30)
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
    box_size = 150

    color_data = []
    for c in colors[:5]:
        color_data.append((_extract_hex(c), _extract_color_label(c)))

    n = max(1, len(color_data))
    slot_w = min(340, (W - 200) // n)  # عرض الخانة لكل لون
    x_start = (W - slot_w * n) // 2

    label_line_h = 42
    label_y = y + box_size + 45  # مسافة بين المربع والاسم
    hex_y = label_y + label_line_h * 2 + 20  # مسافة بين الاسم والـ HEX

    for i, (hex_code, label) in enumerate(color_data):
        cx = x_start + i * slot_w + slot_w // 2  # مركز الخانة
        x = cx - box_size // 2

        # Color swatch
        draw.rounded_rectangle(
            [x, y, x + box_size, y + box_size],
            radius=24, fill=hex_code, outline="#dddddd", width=3,
        )

        # Color name (سطرين كحد أقصى)
        lines = textwrap.wrap(label, width=14)[:2]
        for j, line in enumerate(lines):
            draw.text((cx, label_y + j * label_line_h), line,
                      font=font_label, fill="black", anchor="ma")

        # HEX code
        draw.text((cx, hex_y), hex_code,
                  font=font_label, fill="#666666", anchor="ma")

    y = hex_y + 150  # مسافة قبل قسم Typography
    # Typography (مع لفّ النص)
    y = draw_wrapped(draw, 100, y, f"Font: {package.get('typography', '—')}",
                     font_small, "black")
    y += 30

    # Visual Style (مع لفّ النص)
    draw_wrapped(draw, 100, y, f"Style: {package.get('visual_style', '—')}",
                 font_small, "black")

    return card