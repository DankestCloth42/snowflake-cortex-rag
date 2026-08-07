import os 
from dotenv import load_dotenv
from snowflake.snowpark import Session
import snowflake.snowpark.functions as F
import json
from sentence_transformers import SentenceTransformer
from logger_setup import get_logger

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
    print("Connecting to Snowflake...")
    session = Session.builder.configs(connection_parameters).create()
    print("Successfully connected to Snowflake!")

    print("Loading AI model from Hugging Face...")
    model = SentenceTransformer('Snowflake/snowflake-arctic-embed-m')
    print("Model loaded successfully!")

    user_query: str = "Jaki napastnik reprezentacji Francji grał świetnie i strzelił dużo goli?"
    logger.info(f"Encoding user query: '{user_query}'...")

    vector = model.encode(user_query).tolist()
    logger.info("Query encoded into vector successfully!")

    vector_json_string = json.dumps(vector)

    logger.info("Running vector similarity search in Snowflake...")
    sql_query = f"""
    select 
        "player_name", 
        "team", 
        "position", 
        "total_goals_tournament", 
        "total_minutes_tournament", 
        "player_document", 
        vector_cosine_similarity("player_vector"::VECTOR(FLOAT, 768), PARSE_JSON('{vector_json_string}')::VECTOR(FLOAT, 768)) as similarity_result
    from cortex_data.fifa_players_cortex
    ORDER BY vector_cosine_similarity("player_vector"::VECTOR(FLOAT, 768), PARSE_JSON('{vector_json_string}')::VECTOR(FLOAT, 768)) DESC
    LIMIT 3;
    """

    results_df = session.sql(sql_query).to_pandas()

    print("Search completed! Top results:")
    logger.info(f"\n{results_df.to_string()}")



except Exception as e:
    logger.error(f"An error occurred: {e}")



finally:
    logger.info("Closing the Snowflake session...")
    session.close()



