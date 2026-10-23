from project_black_knight.query_parser import make_groq_strict_schema, SYSTEM_PROMPT
from project_black_knight.query_schema import BlackKnightQuery


def test_system_prompt_rules():
    assert "BlackKnightQuery" in SYSTEM_PROMPT
    assert "semantic_query" in SYSTEM_PROMPT
    assert "genres_include" in SYSTEM_PROMPT
    assert "genres_exclude" in SYSTEM_PROMPT


def test_make_groq_strict_schema():
    pydantic_schema = BlackKnightQuery.model_json_schema()
    groq_schema = make_groq_strict_schema(pydantic_schema)

    # In strict mode, objects must specify additionalProperties: False
    assert groq_schema.get("additionalProperties") is False
    assert "required" in groq_schema
    assert set(groq_schema["properties"].keys()) == set(groq_schema["required"])
