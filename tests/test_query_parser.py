from project_black_knight.query_parser import make_groq_strict_schema, SYSTEM_PROMPT, get_groq_client
from project_black_knight.query_schema import BlackKnightQuery
import pytest


def test_system_prompt_rules(monkeypatch):
    assert "BlackKnightQuery" in SYSTEM_PROMPT
    assert "semantic_query" in SYSTEM_PROMPT
    assert "genres_include" in SYSTEM_PROMPT
    assert "genres_exclude" in SYSTEM_PROMPT

    # Verify missing GROQ_API_KEY raises RuntimeError
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    import project_black_knight.query_parser as qp
    monkeypatch.setattr(qp, "_client", None)
    with pytest.raises(RuntimeError, match="GROQ_API_KEY is not set"):
        get_groq_client()

    # Verify explicit key initializes without environment variable
    client = get_groq_client(api_key="gsk_dummy_test_key_for_unit_tests_only")
    assert client is not None
    assert client.api_key == "gsk_dummy_test_key_for_unit_tests_only"


def test_make_groq_strict_schema():
    pydantic_schema = BlackKnightQuery.model_json_schema()
    groq_schema = make_groq_strict_schema(pydantic_schema)

    # In strict mode, objects must specify additionalProperties: False
    assert groq_schema.get("additionalProperties") is False
    assert "required" in groq_schema
    assert set(groq_schema["properties"].keys()) == set(groq_schema["required"])
