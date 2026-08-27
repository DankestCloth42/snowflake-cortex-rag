import os
import json
from dotenv import load_dotenv
from snowflake.snowpark import Session
from sentence_transformers import SentenceTransformer
from google import genai
from google.genai import types
from src.utils.logger_setup import get_logger

logger = get_logger(__name__)

load_dotenv()

# Load model globally so it's not reloaded on every function call
logger.info("Loading AI vector model from Hugging Face...")
vector_model = SentenceTransformer('Snowflake/snowflake-arctic-embed-m')
logger.info("Model loaded successfully!")


def get_snowflake_session() -> Session:
    """
    Creates and returns a Snowflake Snowpark session using credentials from .env.
    """
    connection_parameters = {
        "account": os.getenv("SNOWFLAKE_ACCOUNT"),
        "user": os.getenv("SNOWFLAKE_USER"),
        "password": os.getenv("SNOWFLAKE_PASSWORD"),
        "role": os.getenv("SNOWFLAKE_ROLE"),
        "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE"),
        "database": os.getenv("SNOWFLAKE_DATABASE"),
        "schema": os.getenv("SNOWFLAKE_SCHEMA"),
    }
    return Session.builder.configs(connection_parameters).create()


def run_basic_rag(user_query: str) -> str:
    """
    Executes a pure Vector Search (RAG) against Snowflake and generates an answer using Gemini.
    """
    logger.info(f"Starting basic RAG process for query: '{user_query}'")
    session = None
    
    try:
        logger.info("Connecting to Snowflake...")
        session = get_snowflake_session()
        logger.info("Successfully connected to Snowflake!")

        logger.info("Encoding user query into vector...")
        vector = vector_model.encode(user_query).tolist()
        vector_json_string = json.dumps(vector)

        # Pure vector search (no hardcoded text filters like '%France%')
        logger.info("Running vector similarity search in Snowflake...")
        sql_query = f"""
            SELECT 
                "player_document", 
                VECTOR_COSINE_SIMILARITY(
                    "player_vector"::VECTOR(FLOAT, 768), 
                    PARSE_JSON('{vector_json_string}')::VECTOR(FLOAT, 768)
                ) as similarity_result
            FROM cortex_data.fifa_players_cortex
            ORDER BY similarity_result DESC
            LIMIT 3;
        """

        results_df = session.sql(sql_query).to_pandas()

        if results_df.empty:
            logger.warning("No context retrieved from the database.")
            return "🤖 AI Response: I couldn't find any relevant information."

        # Concatenate the retrieved documents into a single string
        retrieval_results = "\n\n---\n\n".join(results_df['player_document'].tolist())
        logger.info("Context successfully retrieved from database.")

        # Client initialization (matching the env variable naming convention)
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

        rag_prompt = f"""
        You are a sports assistant and football expert.
        Answer the user's question based EXCLUSIVELY on the context provided below.
        If the context does not contain enough information to answer, say honestly that you do not know. Do not make things up (do not hallucinate).

        DATABASE CONTEXT:
        {retrieval_results}

        USER QUESTION:
        {user_query}
        """

        logger.info("Sending prompt and context to Gemini AI for response generation...")
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=rag_prompt,
            config=types.GenerateContentConfig(
                temperature=0.1,  # Low temperature minimizes hallucination risk
            ),
        )

        logger.info("Basic RAG search completed successfully.")
        return response.text

    except Exception as e:
        logger.error(f"An error occurred during RAG pipeline: {e}")
        return "🛠️ Sorry, our AI system is currently experiencing technical difficulties."

    finally:
        if session:
            logger.info("Closing the Snowflake session...")
            session.close()


if __name__ == "__main__":
    # Smoke test
    test_query = "Which striker from the French national team played great and scored many goals?"
    answer = run_basic_rag(test_query)
    
    print("\n" + "="*60)
    print("🤖 RESPONSE FROM GEMINI AI:")
    print("="*60)
    print(answer)
    print("="*60 + "\n")