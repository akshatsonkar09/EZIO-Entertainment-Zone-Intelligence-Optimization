import os
from copy import deepcopy
from dotenv import load_dotenv
from groq import Groq
try:
    from .query_schema import BlackKnightQuery
except ImportError:
    from query_schema import BlackKnightQuery


_client: Groq | None = None


def get_groq_client(api_key: str | None = None) -> Groq:
    """Return a Groq client instance, loading from environment or .env file."""
    global _client
    if api_key:
        return Groq(api_key=api_key)
    if _client is not None:
        return _client
    load_dotenv()
    env_key = os.getenv("GROQ_API_KEY")
    if not env_key or not env_key.strip():
        raise RuntimeError("GROQ_API_KEY is not set. Please set the environment variable or pass a client.")
    _client = Groq(api_key=env_key.strip())
    return _client


def __getattr__(name: str):
    """Provide backward compatibility for module-level `client` attribute."""
    if name == "client":
        return get_groq_client()
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")



SYSTEM_PROMPT = """
You are the query-understanding module of Project Black Knight,
an AI entertainment discovery system.

Your job is to convert a user's natural-language entertainment request
into the provided structured BlackKnightQuery schema.

You are NOT responsible for finding recommendations.
You are NOT responsible for ranking results.
You only understand and structure the user's request.

Rules:
1. Identify the top two relevant media types from: movie, anime, book.
   - Rank them by relevance to the user's request.
   - Put the most relevant media type first.
   - If only one media type is clearly relevant, return only that one.
2. Put general constraints (title, genres, release year) into the common section.
3. Put media-specific constraints into the appropriate domain section.
4. Use genres_include for genres the user wants.
5. Use genres_exclude for genres the user explicitly does NOT want.
6. Put subjective concepts ("dark", "mind-bending", "emotional", etc.) into semantic_query.
7. Put explicit similarity requests ("like Death Note") into similar_to.
8. Do not invent information that the user did not specify.
9. If a field is not mentioned, use null or an empty list according to the schema.
10. semantic_query should preserve important semantic meaning.
11. media_types must be ordered by relevance.
12. Descriptive concepts remain in semantic_query unless explicitly represented as a genre.
13. For domain-specific numeric constraints, use the appropriate domain field when units are explicitly specified.

Return only the structured result matching the schema.
"""


# 3. CONVERT PYDANTIC SCHEMA TO GROQ STRICT SCHEMA

def make_groq_strict_schema(schema: dict) -> dict:
    """
    Recursively transform a JSON Schema into Groq strict-mode format.
    Requires `additionalProperties: False` and `required` arrays on all objects.
    """
    schema = deepcopy(schema)

    def process_node(node):
        if not isinstance(node, dict):
            return

        # Handle object schemas
        is_object = node.get("type") == "object" or "properties" in node
        if is_object:
            node["additionalProperties"] = False
            properties = node.get("properties", {})
            if properties:
                node["required"] = list(properties.keys())
                for value in properties.values():
                    process_node(value)

        # Handle array items
        if "items" in node:
            process_node(node["items"])

        # Handle composite keywords
        for keyword in ("anyOf", "oneOf", "allOf"):
            if keyword in node and isinstance(node[keyword], list):
                for subschema in node[keyword]:
                    process_node(subschema)

        # Handle schema definition dictionaries
        for def_key in ("$defs", "definitions"):
            if def_key in node and isinstance(node[def_key], dict):
                for subschema in node[def_key].values():
                    process_node(subschema)

    process_node(schema)
    return schema



import time
from groq import RateLimitError, APIError


# 4. PARSE USER QUERY

MODELS_TO_TRY = ["openai/gpt-oss-20b", "qwen/qwen3.8-27b", "openai/gpt-oss-120b"]


def parse_query(
    user_query: str,
    max_retries: int = 3,
    client: Groq | None = None,
) -> BlackKnightQuery:
    if client is None:
        client = get_groq_client()

    pydantic_schema = BlackKnightQuery.model_json_schema()
    groq_schema = make_groq_strict_schema(pydantic_schema)

    last_error = None
    for model_name in MODELS_TO_TRY:
        for attempt in range(max_retries):
            try:
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_query},
                    ],
                    response_format={
                        "type": "json_schema",
                        "json_schema": {
                            "name": "BlackKnightQuery",
                            "schema": groq_schema,
                            "strict": True,
                        },
                    },
                )

                choice = response.choices[0] if response.choices else None
                raw_output = choice.message.content if choice and choice.message else None
                if not raw_output:
                    raise ValueError("Model returned an empty content payload.")

                return BlackKnightQuery.model_validate_json(raw_output)

            except RateLimitError as e:
                last_error = e
                if attempt < max_retries - 1:
                    time.sleep(1.5 * (attempt + 1))
                    continue
                # Try next model if retries exhausted
                break
            except Exception as e:
                last_error = e
                break

    if last_error:
        raise last_error
    raise RuntimeError("Failed to parse query.")