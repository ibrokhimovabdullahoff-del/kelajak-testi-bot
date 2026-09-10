"""Small compatibility patches for legacy human-facing copy.

The stable Big Five database key remains `bigfive`; only display text changes.
"""
from locales import STRINGS

if "about" in STRINGS:
    STRINGS["about"] = {
        lang: text.replace("Big Five — shaxsiyat profili", "Big Five — shaxsiyat testi")
        .replace("Big Five — профиль личности", "Big Five — тест личности")
        for lang, text in STRINGS["about"].items()
    }
