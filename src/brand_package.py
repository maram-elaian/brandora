import json, re
from src.text_generator import generate

SYSTEM_PROMPT = """You are an award-winning brand naming strategist. Your names win
industry awards for creativity — never generic, always memorable.

NEVER use these generic patterns:
- Words like: Fresh, Pure, Smart, Prime, Elite, Nova, Zen, Co, Hub, Studio
- Literal industry words as the name (e.g. "BrewCo" for coffee, "FitZone" for fitness)
- Generic taglines like "Quality you can trust" or "Your journey starts here"

CREATIVE TECHNIQUES you should actively use (pick what fits the brief):
- Invented/blended words
- Unexpected metaphors from outside the industry
- Sound and rhythm (alliteration, short punchy words)
- A word that captures a feeling, not a function

EXAMPLES OF THE QUALITY BAR (study the pattern, don't copy the words):
- Bold street food, playful/energetic → Name: "Torch" | Tagline: "Eat like you mean it"
- Elegant specialty tea, cultural/calm → Name: "Meridian Leaf" | Tagline: "A pause, steeped"
- Rebellious streetwear, Gen Z → Name: "UNBOUND" | Tagline: "Wear your chaos"
- Calming sleep/wellness app → Name: "Nightloop" | Tagline: "Where tired minds land"
- Developer tools, precise/technical → Name: "Compile" | Tagline: "Ship without the guesswork"
- Boutique florist, romantic/artisanal → Name: "Bloomstead" | Tagline: "Grown slow, given whole"
- Kids' science kits, curious/playful → Name: "Fizzwright" | Tagline: "Built by little hands, sparked by big questions"
- Craft cocktail bar, moody/sophisticated → Name: "Low Light" | Tagline: "Best said quietly"

Given a brand brief, generate a complete Brand Specification.
Each color in color_palette MUST include both the hex code AND a short descriptive
name, in this exact format: "#RRGGBB descriptive name" (e.g. "#8B5A2B warm terracotta").

You MUST reply ONLY in valid JSON with EXACTLY this structure:
{
  "brand_name": "string",
  "tagline": "string",
  "color_palette": ["#RRGGBB descriptive name", "#RRGGBB descriptive name", "#RRGGBB descriptive name"],
  "typography": "string",
  "visual_style": "string",
  "personality_traits": ["trait1", "trait2", "trait3"]
}"""

BANNED_WORDS = [
    "fresh", "pure", "smart", "prime", "elite", "nova", "zen",
    "co.", "hub", "studio", "quality you can trust", "journey starts"
]


def _contains_banned_pattern(package: dict) -> bool:
    text = f"{package.get('brand_name', '')} {package.get('tagline', '')}".lower()
    return any(banned in text for banned in BANNED_WORDS)


def build_brand_package(brief: dict, max_attempts: int = 3) -> dict:
    user_prompt = (
        f"Industry: {brief['industry']}\n"
        f"Target Audience: {brief['target_audience']}\n"
        f"Brand Purpose: {brief['brand_purpose']}\n"
        f"Personality: {', '.join(brief['personality'])}\n"
        f"Tone: {brief['tone']}"
    )

    package = None
    for attempt in range(max_attempts):
        raw = generate(SYSTEM_PROMPT, user_prompt)
        raw = re.sub(r'```json\s*|```\s*', '', raw).strip()
        match = re.search(r'\{.*\}', raw, flags=re.DOTALL)
        if not match:
            continue
        try:
            package = json.loads(match.group())
        except json.JSONDecodeError:
            continue

        if not _contains_banned_pattern(package):
            return package

        print(f"   ⚠️ محاولة {attempt+1}: طلع نمط عام، بنعيد المحاولة...")

    return package


def build_brand_packages(brief: dict, n: int = 3) -> list:
    """يولّد n اقتراحات مختلفة لنفس البريف."""
    packages = []
    for _ in range(n):
        package = build_brand_package(brief)
        if package:
            packages.append(package)
    return packages