import os
import traceback
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from snowflake.snowpark import Session
from snowflake.snowpark.exceptions import SnowparkSQLException
from google import genai
from src.utils.logger_setup import get_logger
from src.rag_engine.hybrid_search import extract_search_filters

# Initialize the logger for this module
logger = get_logger(__name__)

# Load environment variables from .env file
load_dotenv()

logger.info("Loading local vector model...")
vector_model = SentenceTransformer('Snowflake/snowflake-arctic-embed-m')
logger.info("Vector model loaded successfully.")


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


def build_hybrid_query(user_query: str) -> str:
    """
    Builds a hybrid SQL query combining hard WHERE filters and vector similarity.
    """
    # 1. Extract filters using LLM
    filters = extract_search_filters(user_query)
    logger.info(f"LLM extracted filters: {filters}")

    # 2. Vectorize ONLY the semantic part of the query
    question_vector_list = vector_model.encode(
        filters["semantic_query"], convert_to_numpy=True
    ).tolist()

    # 3. Build secure WHERE clauses preventing SQL injection
    where_clauses = []
    for word in filters["hard_keywords"]:
        safe_word = word.replace("'", "")
        where_clauses.append(f'"player_document" ILIKE \'%{safe_word}%\'')

    where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"

    # 4. Construct the final SQL query
    sql_query = f"""
        SELECT 
            "player_document",
            VECTOR_COSINE_SIMILARITY(
                "player_vector"::VECTOR(FLOAT, 768), 
                {question_vector_list}::VECTOR(FLOAT, 768)
            ) AS similarity
        FROM 
            cortex_data.fifa_players_cortex
        WHERE 
            {where_clause}
        ORDER BY 
             VECTOR_COSINE_SIMILARITY(
                            "player_vector"::VECTOR(FLOAT, 768), 
                            {question_vector_list}::VECTOR(FLOAT, 768)
                        ) DESC
        LIMIT 5
    """
    return sql_query


def run_hybrid_rag(user_query: str) -> str:
    """
    Main orchestration function: extracts intent, queries Snowflake, and generates final answer.
    Returns a string meant to be displayed in the Streamlit UI.
    """
    logger.info(f"Starting RAG process for query: '{user_query}'")
    session = None
    
    try:
        # Step A: Build Query
        sql_query = build_hybrid_query(user_query)
        logger.info("Hybrid SQL query generated successfully.")

        # Step B: Execute in Snowflake
        session = get_snowflake_session()
        logger.info("Connected to Snowflake. Executing query...")
        
        results = session.sql(sql_query).collect()
        
        if not results:
            logger.warning("No matching documents found in the database.")
            return "🤖 AI Response: I couldn't find any relevant information in the database."

        # Combine texts with clear separators for the LLM context
        context = "\n\n---\n\n".join([row["player_document"] for row in results])
        logger.info(f"Retrieved {len(results)} matching documents.")

        # Step C: Final LLM Generation
        logger.info("Sending context to Gemini for final generation...")
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        
        # Professional prompt in English
        prompt = f"""
        You are a professional sports data analyst. Answer the user's question based EXCLUSIVELY on the provided context below.
        If the answer cannot be found in the context, simply state: "I don't have this data in my knowledge base."
        
        Database Context (best matches):
        {context}
        
        User Question: {user_query}
        """
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        
        logger.info("RAG pipeline completed successfully.")
        
        return response.text

    # Error Handling Block
    except SnowparkSQLException as db_err:
        logger.error("Database error occurred (e.g., syntax issue or missing table).")
        logger.error(f"Snowflake details: {db_err}")
        logger.error(f"Query: {sql_query}")
        return "🛠️ Sorry, we encountered a technical issue with the database."

    except Exception as e:
        logger.critical(f"Critical system failure: {e}")
        logger.debug(traceback.format_exc()) 
        return "🛠️ Sorry, our AI system is currently experiencing technical difficulties."

    finally:
        if session:
            # Always close the session to prevent memory leaks and billing issues
            session.close()
            logger.info("Snowflake session safely closed.")


if __name__ == "__main__":
    logger.info("Running smoke test for Hybrid RAG...")
    test_query = "Find players from Brazil who scored more than 10 goals in 2022"
    result = run_hybrid_rag(test_query)
    print("\n--- TEST RESULT ---")
    print(result)