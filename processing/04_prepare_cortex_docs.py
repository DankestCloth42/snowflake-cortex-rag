import os 
from dotenv import load_dotenv
from snowflake.snowpark import Session
import snowflake.snowpark.functions as F
from snowflake.snowpark.window import Window
from logger_setup import get_logger


# Workaround for the Snowflake Cortex embedding function, which is restricted on Trial accounts.
from sentence_transformers import SentenceTransformer


load_dotenv()

logger = get_logger('04_prepare_cortex_docs')

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


    df_table = session.table("raw_data.fifa_players_raw")

    df_table_adjusted = df_table.withColumn(
        '"player_document"', 
        F.concat_ws(
            F.lit(' '), 
            F.lit('Zawodnikiem jest'), 
            F.col('"player_name"').cast("string"), 
            F.lit('. Reprezentuje drużynę'), 
            F.col('"team"').cast("string"), 
            F.lit('. Gra na pozycji'), 
            F.col('"position"').cast("string"), 
            F.lit('. Podczas turnieju strzelił'), 
            F.col('"total_goals_tournament"').cast("string"), 
            F.lit('goli. i rozegrał'), 
            F.col('"total_minutes_tournament"').cast("string"), 
            F.lit('minut.')
        )
    )

    # test
    # print(df_table_adjusted.select('"player_name"', '"team"', '"goals"', '"player_document"').limit(10).to_pandas())

    # print("Generating vector embedings using Snowflake Cortex...")

    # df_with_vectors = df_table_adjusted.withColumn(
    #     '"player_vector"', 
    #     F.call_builtin(
    #         "snowflake.cortex.embed_text_768", 
    #         F.lit('snowflake-arctic-embed-m'), 
    #         F.col('"player_document"')
    #     )
    # )

    # print("Vectors generated! Writing to the final Cortex table...")

    # df_with_vectors.write.mode("overwrite").save_as_table("cortex_data.fifa_players_cortex")

    # print("Data written successfully to the Cortex table.")

    
    
    # =========================================================================================
    # ARCHITECTURE NOTE: HYBRID APPROACH (LOCAL INFERENCE)
    # =========================================================================================
    # Instead of using the native SNOWFLAKE.CORTEX.EMBED_TEXT_768 function (which is restricted 
    # on Trial accounts and incurs cloud compute costs), we implement a Local AI inference pattern:
    # 
    # 1. Data Extraction: We pull the text documents from Snowflake into local memory (Pandas).
    # 2. Local Compute: We load the exact same open-source model ('snowflake-arctic-embed-m') 
    #    via Hugging Face and compute the 768-dimensional embeddings using the local CPU.
    # 3. Data Load: We push the fully materialized vectors back to the Snowflake data warehouse.
    #
    # This ensures 100% mathematical parity with Cortex results while bypassing trial limitations
    # and demonstrating cost-efficient, edge-computing capabilities.
    # =========================================================================================


    logger.info("Extracting data from Snowflake into local memory...")

    pd_local = df_table_adjusted.to_pandas()

    logger.info("Downloading and loading model AI from Hugging Face (it can take a few minutes)...")

    model = SentenceTransformer('Snowflake/snowflake-arctic-embed-m')

    logger.info("Generating vector embeddings locally using the model...")


    texts = pd_local['player_document'].tolist()

    #test_texts = texts[:100]

    embeddings = model.encode(
        texts,
        batch_size=32, 
        show_progress_bar=True,
        convert_to_numpy=True
    )

    #print(embeddings[:5]) 

    logger.info("Vectors generated! Writing to the final Cortex table in Snowflake...")

    pd_local['player_vector'] = embeddings.tolist()

    # Convert the Pandas DataFrame back to a Snowpark DataFrame
    snowpark_df_with_vectors = session.create_dataframe(pd_local)

    snowpark_df_with_vectors.write.mode("overwrite").save_as_table("cortex_data.fifa_players_cortex")

    logger.info("Final Cortex table written successfully with local embeddings!")


except Exception as e:
    logger.error(f"An error occurred: {e}")



finally:
    logger.info("Closing the Snowflake session...")
    session.close()