"""
Language configuration for multilingual agent simulation.
Supports Hinglish, Hindi, and regional Indian language mixing.
"""

LANGUAGE_TEMPLATES = {
    "english": {
        "instruction": "Communicate in English.",
        "example_style": "Standard English communication"
    },
    "hinglish": {
        "instruction": (
            "Communicate in Hinglish (a natural mix of Hindi and English commonly used "
            "on Indian social media). Mix Hindi words written in Roman script with English. "
            "Examples: 'Yaar ye toh bahut interesting hai!', 'Kya scene hai bro?', "
            "'Main toh shocked hu with this news', 'Acha so basically what happened is...'"
        ),
        "example_style": "Natural Hindi-English code-switching in Roman script"
    },
    "hindi": {
        "instruction": (
            "Communicate primarily in Hindi using Devanagari script. "
            "You may occasionally use common English words that are naturally used in Hindi conversation. "
            "Examples: '\u092f\u0939 \u092c\u0939\u0941\u0924 \u0905\u091a\u094d\u091b\u0940 \u0916\u092c\u0930 \u0939\u0948!', '\u092e\u0941\u091d\u0947 \u0932\u0917\u0924\u093e \u0939\u0948 \u0915\u093f \u092f\u0939 \u0938\u0939\u0940 decision \u0939\u0948'"
        ),
        "example_style": "Hindi in Devanagari with occasional English loanwords"
    },
    "tamil": {
        "instruction": "Communicate in Tamil, using Tamil script. You may use common English loanwords.",
        "example_style": "Tamil with English loanwords"
    },
    "telugu": {
        "instruction": "Communicate in Telugu, using Telugu script. You may use common English loanwords.",
        "example_style": "Telugu with English loanwords"
    },
    "bengali": {
        "instruction": "Communicate in Bengali, using Bengali script. You may use common English loanwords.",
        "example_style": "Bengali with English loanwords"
    },
    "marathi": {
        "instruction": "Communicate in Marathi, using Devanagari script. You may use common English loanwords.",
        "example_style": "Marathi with English loanwords"
    },
    "spanish": {
        "instruction": "Communicate in Spanish.",
        "example_style": "Standard Spanish"
    },
    "mandarin": {
        "instruction": "Communicate in Simplified Chinese (Mandarin).",
        "example_style": "Standard Simplified Chinese"
    }
}

# Social media platform language tendencies
PLATFORM_LANGUAGE_BIAS = {
    "twitter": {"code_switching_likelihood": 0.8},   # Twitter encourages informal mixing
    "reddit": {"code_switching_likelihood": 0.5},     # Reddit more formal
    "whatsapp": {"code_switching_likelihood": 0.9},   # WhatsApp very informal
    "instagram": {"code_switching_likelihood": 0.7},  # Instagram moderate mixing
    "youtube": {"code_switching_likelihood": 0.6},    # YouTube comments moderate
}


def get_language_instruction(language: str, platform: str = "twitter") -> str:
    """Get the language instruction for an agent based on their language and platform"""
    template = LANGUAGE_TEMPLATES.get(language, LANGUAGE_TEMPLATES["english"])
    instruction = template["instruction"]

    bias = PLATFORM_LANGUAGE_BIAS.get(platform, {})
    if bias.get("code_switching_likelihood", 0) > 0.7 and language in ["hinglish", "hindi"]:
        instruction += " Feel free to use slang, abbreviations, and informal expressions natural to social media."

    return instruction


def assign_language_to_agent(agent_profile: dict, language_config: dict) -> str:
    """Assign a language to an agent based on their profile and config distribution"""
    import random

    # If agent has explicit language preference, use it
    lang_pref = agent_profile.get("language_preference", "")
    if lang_pref and lang_pref.lower() in LANGUAGE_TEMPLATES:
        return lang_pref.lower()

    # Otherwise use weighted random from distribution
    distribution = language_config.get("language_distribution", {"english": 1.0})
    languages = list(distribution.keys())
    weights = list(distribution.values())

    return random.choices(languages, weights=weights, k=1)[0]
