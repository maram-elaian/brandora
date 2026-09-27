import json, re
from src.text_generator import generate

SYSTEM_PROMPT = """You are a senior brand strategist known for bold, unexpected naming —
never generic corporate names.

NEVER use these generic patterns:
- Words like: Fresh, Pure, Smart, Prime, Elite, Nova, Zen, Co, Hub, Studio
- Literal industry words as the name (e.g. "BrewCo" for coffee)
- Generic taglines like "Quality you can trust"

Given a brand brief, generate a complete Brand Specification.
You MUST reply ONLY in valid JSON with EXACTLY this structure:
{
  "brand_name": "string",
  "tagline": "string",
  "color_palette": ["color1", "color2", "color3"],
  "typography": "string",
  "visual_style": "string",
  "personality_traits": ["trait1", "trait2", "trait3"]
}"""

def build_brand_package(brief: dict) -> dict:
    user_prompt = (
        f"Industry: {brief['industry']}\n"
        f"Target Audience: {brief['target_audience']}\n"
        f"Brand Purpose: {brief['brand_purpose']}\n"
        f"Personality: {', '.join(brief['personality'])}\n"
        f"Tone: {brief['tone']}"
    )
    raw = generate(SYSTEM_PROMPT, user_prompt)
    raw = re.sub(r'```json\s*|```\s*', '', raw).strip()
    match = re.search(r'\{.*\}', raw, flags=re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group())
    except json.JSONDecodeError:
        return None
