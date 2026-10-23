from project_black_knight.text_normalizer import (
    Text_Normalization,
    normalize_title,
    normalize_title_key,
)


def test_text_normalization():
    normalizer = Text_Normalization()

    # Contractions
    assert "cannot" in normalizer.expand_contractions("can't") or "can not" in normalizer.expand_contractions("can't")

    # Lowercase
    assert normalizer.lowercase("InCePtIoN") == "inception"

    # Whitespace
    assert normalizer.removewhitespace("  Interstellar   2014   ") == "Interstellar 2014"

    # Special characters
    assert normalizer.remove_spec_char("Hello, World! @#$ 123") == "Hello World  123"

    # Full normalize pipeline
    result = normalizer.normalize("  You aren't ready... for THIS!! ")
    assert "are not" in result or "arent" in result
    assert "this" in result
    assert "!" not in result


def test_normalize_title_diacritics_and_unicode():
    """Verify Unicode NFKD decomposition and diacritic removal."""
    assert normalize_title("Amélie") == "amelie"
    assert normalize_title("Amelie") == "amelie"
    assert normalize_title_key("Amélie") == normalize_title_key("Amelie")

    assert normalize_title("Pokémon") == "pokemon"
    assert normalize_title("Pokemon") == "pokemon"
    assert normalize_title_key("Pokémon") == normalize_title_key("Pokemon")

    assert normalize_title_key("WALL·E") == normalize_title_key("WALL-E") == "walle"


def test_normalize_title_apostrophes_and_punctuation():
    """Verify straight, curly apostrophes and punctuation variations."""
    # Straight vs curly apostrophes
    assert normalize_title_key("Ender's Game") == normalize_title_key("Ender’s Game")
    assert normalize_title_key("Dude, Where's My Car?") == normalize_title_key("Dude, Where’s My Car?")
    assert normalize_title_key("The Spider's Web") == normalize_title_key("The Spider’s Web")

    # Leading, trailing, and repeated whitespace
    assert normalize_title("   Cowboy    Bebop   ") == "cowboy bebop"
    assert normalize_title_key("   Cowboy    Bebop   ") == "cowboybebop"


def test_normalize_title_subtitle_delimiters():
    """Verify subtitle delimiters (colons, hyphens, em-dashes, semicolons)."""
    assert normalize_title_key("Fullmetal Alchemist: Brotherhood") == normalize_title_key("Fullmetal Alchemist - Brotherhood")
    assert normalize_title_key("Steins;Gate") == normalize_title_key("Steins Gate")
    assert normalize_title_key("Star Wars: Episode IV - A New Hope") == normalize_title_key("Star Wars - Episode IV: A New Hope")


def test_distinct_titles_remain_distinct():
    """Ensure normalization does not conflate distinct installments, editions, or works."""
    distinct_pairs = [
        ("Iron Man", "Iron Man 2"),
        ("Iron Man 2", "Iron Man 3"),
        ("The Way of Kings", "The Way of Kings, Part 1"),
        ("The Way of Kings, Part 1", "The Way of Kings, Part 2"),
        ("Avatar", "Avatar: The Last Airbender"),
        ("One Punch Man", "One Punch Man Specials"),
        ("One Punch Man", "One Punch Man: Road to Hero"),
        ("One Punch Man", "One Punch Man 2nd Season"),
        ("Dune", "Dune Messiah"),
    ]
    for t1, t2 in distinct_pairs:
        k1 = normalize_title_key(t1)
        k2 = normalize_title_key(t2)
        assert k1 != k2, f"Collision detected between '{t1}' and '{t2}': {k1}"
