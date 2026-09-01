import json
import os
from google import genai
from google.genai import types
from dotenv import load_dotenv
from src.utils.logger_setup import get_logger

logger = get_logger(__name__)

load_dotenv()


def extract_search_filters(user_query: str) -> dict:
    logger.info(f"Extracting filters from query: '{user_query}'")
    
    client = genai.Client(
        api_key=os.getenv("GEMINI_API_KEY") 
    )

    response_schema = types.Schema(
        type=types.Type.OBJECT,
        properties={
            "hard_keywords": types.Schema(
                type=types.Type.ARRAY,
                items=types.Schema(
                    type=types.Type.STRING
                ),
                description="Proper names, countries, dates, or key nouns that MUST appear in the text."
            ),
            "semantic_query": types.Schema(
                type=types.Type.STRING,
                description="The rest of the query describing the general meaning or intent (for vectorization)."
            )
        },
        required=["hard_keywords", "semantic_query"]
    )

    prompt = f"""
    You are a database assistant. Analyze the user's query.
    Extract hard keywords from it (e.g., country names, company names, dates),
    and keep the rest as a semantic query.
    
    Query: "{user_query}"
    """

    response = client.models.generate_content(
        model='gemini-3.6-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=response_schema,
            temperature=0.1
        ),
    )

    filters = json.loads(response.text)
    logger.info(f"Successfully extracted filters: {filters}")
    return filters


if __name__ == "__main__":
    logger.info("Running smoke test for hybrid search extraction...")
    test_query = "Find players from Brazil who scored more than 10 goals in 2022"
    result = extract_search_filters(test_query)
    print("\n--- TEST RESULT ---")
    print(json.dumps(result, indent=2))