import json
import re

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

Given a brand brief, generate ONE complete Brand Specification.
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


def _parse_json_response(raw: str):
    raw = re.sub(r"```json\s*|```\s*", "", raw).strip()

    try:
        data = json.loads(raw)
        if isinstance(data, list) and data and isinstance(data[0], dict):
            return data[0]
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", raw, flags=re.DOTALL)
    if not match:
        return None

    try:
        return json.loads(match.group())
    except json.JSONDecodeError:
        return None


def _normalize_package(package):
    if not isinstance(package, dict):
        return None

    package.setdefault("brand_name", "")
    package.setdefault("tagline", "")
    package.setdefault("color_palette", [])
    package.setdefault("typography", "")
    package.setdefault("visual_style", "")
    package.setdefault("personality_traits", [])

    raw_colors = package.get("color_palette") or []

    if isinstance(raw_colors, str):
        raw_colors = [c.strip() for c in raw_colors.split(",") if c.strip()]

    if isinstance(raw_colors, dict):
        raw_colors = [raw_colors]

    normalized_colors = []

    for c in raw_colors:
        if isinstance(c, dict):
            hex_value = (
                c.get("hex")
                or c.get("value")
                or c.get("code")
                or ""
            )
            name = (
                c.get("name")
                or c.get("label")
                or c.get("description")
                or ""
            )
            normalized_colors.append(f"{hex_value} {name}".strip())
        else:
            normalized_colors.append(str(c).strip())

    package["color_palette"] = [x for x in normalized_colors if x]

    if isinstance(package.get("personality_traits"), str):
        package["personality_traits"] = [
            t.strip() for t in package["personality_traits"].split(",") if t.strip()
        ]

    return package


def build_brand_package(
    brief: dict,
    max_attempts: int = 2,
    avoid_names=None,
    seed=None,
) -> dict:
    avoid_names = avoid_names or set()

    personality = brief.get("personality") or []
    if isinstance(personality, str):
        personality = [p.strip() for p in personality.split(",") if p.strip()]

    base_user_prompt = (
        f"Industry: {brief.get('industry', '')}\n"
        f"Target Audience: {brief.get('target_audience', '')}\n"
        f"Brand Purpose: {brief.get('brand_purpose', '')}\n"
        f"Personality: {', '.join(personality)}\n"
        f"Tone: {brief.get('tone', '')}"
    )

    avoid_text = ""
    if avoid_names:
        avoid_list = ", ".join(sorted(avoid_names))
        avoid_text = (
            f"\n\nCRITICAL DIVERSITY RULE:\n"
            f"Do NOT use any of these brand names or close variants: {avoid_list}.\n"
            f"Invent a completely different concept, name, tagline, color mood, "
            f"typography direction, and visual style."
        )

    variant_number = len(avoid_names) + 1
    last_package = None

    for attempt in range(max_attempts):
        user_prompt = (
            base_user_prompt
            + avoid_text
            + f"\n\nThis is creative variant {variant_number}."
            + f"\nAttempt {attempt + 1}."
            + "\nBe original. Avoid obvious industry clichés."
        )

        raw = generate(
            SYSTEM_PROMPT,
            user_prompt,
            max_new_tokens=900,
            temperature=0.95,
            top_p=0.95,
            repetition_penalty=1.06,
            seed=seed,
        )

        package = _normalize_package(_parse_json_response(raw))

        if not package:
            continue

        last_package = package

        if _contains_banned_pattern(package):
            continue

        brand_name = package.get("brand_name", "").strip().lower()

        if brand_name and brand_name in avoid_names:
            continue

        return package

    return last_package


def build_brand_packages(brief: dict, n: int = 3) -> list:
    packages = []
    used_names = set()
    used_keys = set()

    for i in range(n + 2):
        if len(packages) >= n:
            break

        package = build_brand_package(
            brief,
            max_attempts=2,
            avoid_names=used_names,
            seed=i * 1000 + 7,
        )

        if not package:
            continue

        if _contains_banned_pattern(package):
            continue

        brand_name = package.get("brand_name", "").strip().lower()
        tagline = package.get("tagline", "").strip().lower()
        key = (brand_name, tagline)

        if key in used_keys:
            continue

        used_keys.add(key)

        if brand_name:
            used_names.add(brand_name)

        packages.append(package)

    return packages