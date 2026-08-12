import os 
from dotenv import load_dotenv
from snowflake.snowpark import Session
import snowflake.snowpark.functions as F
import json
from sentence_transformers import SentenceTransformer
from logger_setup import get_logger
from google import genai
from google.genai import types

load_dotenv()

logger = get_logger('05_rag_search')

# config 
connection_parameters = {
    "account": os.getenv("SNOWFLAKE_ACCOUNT"),
    "user": os.getenv("SNOWFLAKE_USER"),
    "password": os.getenv("SNOWFLAKE_PASSWORD"),
    "role": os.getenv("SNOWFLAKE_ROLE"),
    "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE"),
    "database": os.getenv("SNOWFLAKE_DATABASE"),
    "schema": os.getenv("SNOWFLAKE_SCHEMA"),
}



try:
    logger.info("Connecting to Snowflake...")
    session = Session.builder.configs(connection_parameters).create()
    logger.info("Successfully connected to Snowflake!")

    logger.info("Loading AI model from Hugging Face...")
    model = SentenceTransformer('Snowflake/snowflake-arctic-embed-m')
    logger.info("Model loaded successfully!")

    user_query: str = "Jaki napastnik reprezentacji Francji grał świetnie i strzelił dużo goli?"
    logger.info(f"Encoding user query: '{user_query}'...")

    vector = model.encode(user_query).tolist()
    logger.info("Query encoded into vector successfully!")

    vector_json_string = json.dumps(vector)

    logger.info("Running vector similarity search in Snowflake...")
    sql_query = f"""
    select 
        "player_document", 
        vector_cosine_similarity("player_vector"::VECTOR(FLOAT, 768), PARSE_JSON('{vector_json_string}')::VECTOR(FLOAT, 768)) as similarity_result
    from cortex_data.fifa_players_cortex
    WHERE "team" ILIKE '%France%'
    ORDER BY vector_cosine_similarity("player_vector"::VECTOR(FLOAT, 768), PARSE_JSON('{vector_json_string}')::VECTOR(FLOAT, 768)) DESC
    LIMIT 3;
    """

    results_df = session.sql(sql_query).to_pandas()

    # Concatenate the retrieved documents into a single string
    retrieval_results = "\n".join(results_df['player_document'].tolist())

    logger.info("Context successfully retrieved from database.")

    logger.info("Sending context and query to OpenAI for generation...")


    client = genai.Client(api_key=os.getenv("GENAI_API_KEY"))


    rag_prompt = f"""
    Jesteś asystentem sportowym, ekspertem od piłki nożnej. 
    Odpowiedz na pytanie użytkownika opierając się WYŁĄCZNIE na dostarczonym poniżej kontekście.
    Jeśli w kontekście nie ma informacji pozwalających na odpowiedź, powiedz szczerze, że nie wiesz. Nie zmyślaj (nie halucynuj).

    KONTEKST Z BAZY DANYCH:
    {retrieval_results}

    PYTANIE UŻYTKOWNIKA:
    {user_query}
    """

    logger.info("Sending prompt to Gemini AI for response generation...")
    response = client.models.generate_content(
        model='gemini-3.6-flash',
        contents=rag_prompt,
        config=types.GenerateContentConfig(
            temperature=0.1,  # Niska temperatura minimalizuje ryzyko halucynacji
        ),
    )

    # 4. Wyświetlenie odpowiedzi
    print("\n" + "="*60)
    print("🤖 RESPONSE FROM GEMINI AI:")
    print("="*60)
    print(response.text)
    print("="*60 + "\n")


    logger.info("Process RAG search completed successfully.")


except Exception as e:
    logger.error(f"An error occurred: {e}")



finally:
    logger.info("Closing the Snowflake session...")
    session.close()



