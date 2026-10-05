from PIL import Image, ImageDraw, ImageFont
import re


def export_brand_kit(package: dict, logo_image):
    W, H = 900, 1200
    card = Image.new("RGB", (W, H), "white")
    draw = ImageDraw.Draw(card)

    font_title = ImageFont.load_default()
    font_body = ImageFont.load_default()
    font_small = ImageFont.load_default()

    y = 40
    if logo_image:
        logo_resized = logo_image.resize((300, 300))
        card.paste(logo_resized, (W // 2 - 150, y))
        y += 320

    name = package.get("brand_name", "—")
    draw.text((W // 2, y), name, font=font_title, fill="black", anchor="mm")
    y += 70

    tagline = package.get("tagline", "—")
    draw.text((W // 2, y), tagline, font=font_body, fill="#666666", anchor="mm")
    y += 60

    colors = package.get("color_palette", [])
    x_start = W // 2 - (len(colors) * 70) // 2
    for i, c in enumerate(colors):
        match = re.search(r'#[0-9A-Fa-f]{6}', str(c))
        hex_code = match.group(0) if match else "#CCCCCC"
        draw.rectangle([x_start + i * 70, y, x_start + i * 70 + 60, y + 60], fill=hex_code, outline="#ddd")
    y += 90

    draw.text((60, y), f"الخط: {package.get('typography', '—')}", font=font_small, fill="black")
    y += 35
    draw.text((60, y), f"الستايل: {package.get('visual_style', '—')}", font=font_small, fill="black")

    return card