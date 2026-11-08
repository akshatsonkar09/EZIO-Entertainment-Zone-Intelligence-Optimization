import re
import unicodedata
import contractions
import nltk


def normalize_title(text: str) -> str:
    """
    Deterministic, conservative title normalization:
    1. Unicode NFKD decomposition separates base letters from diacritical marks.
    2. Strips combining diacritical marks (e.g. 'Amélie' -> 'Amelie', 'Pokémon' -> 'Pokemon').
    3. Standardizes curly apostrophes, quotes, and grave accents to standard single quote (').
    4. Standardizes subtitle delimiters (':', '-', '–', '—', ';', '_') to whitespace.
    5. Retains alphanumeric characters, spaces, and single quotes; lowercases.
    6. Collapses repeated whitespace and strips leading/trailing spaces.
    Preserves all numbers, roman numerals, installment titles, and distinct words.
    """
    if not text:
        return ""
    nfkd = unicodedata.normalize("NFKD", str(text))
    no_diacritics = "".join(c for c in nfkd if not unicodedata.combining(c))
    cleaned = (
        no_diacritics.replace("\u2019", "'")
        .replace("\u2018", "'")
        .replace("`", "'")
        .replace("\u00b4", "'")
    )
    cleaned = re.sub(r"[\:\-\–\—\_\;]", " ", cleaned)
    cleaned = re.sub(r"[^a-zA-Z0-9\s\']", " ", cleaned).lower()
    return " ".join(cleaned.split())


def normalize_title_key(text: str) -> str:
    """
    Canonical compact key for exact equality comparisons:
    Strips remaining spaces and apostrophes from normalize_title(text).
    Used in exact title filtering and similar_to seed resolution.
    """
    norm = normalize_title(text)
    return re.sub(r"[^a-zA-Z0-9]", "", norm)


class Text_Normalization:
    def normalize(self, text):
        text = self.expand_contractions(text)
        text = self.lowercase(text)
        text = self.remove_spec_char(text)
        text = self.removewhitespace(text)
        return text

    def removewhitespace(self, text):
        text = " ".join(text.split())
        return text

    def lowercase(self, text):
        text = text.lower()
        return text

    def remove_spec_char(self, text):
        text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
        return text

    def expand_contractions(self, text):
        text = contractions.fix(text)
        return text
