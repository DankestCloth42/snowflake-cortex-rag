import os 
from dotenv import load_dotenv
from snowflake.snowpark import Session
import snowflake.snowpark.functions as F
from snowflake.snowpark.window import Window


load_dotenv()

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


    df_table = session.table("raw_data.fifa_players_raw")

    df_table_adjusted = df_table.withColumn('"player_document"', F.concat_ws(F.lit(' '), F.lit('Zawodnikiem jest'), F.col('"player_name"').cast("string"), F.lit('. Reprezentuje drużynę'), F.col('"team"').cast("string"), F.lit('. Gra na pozycji'), F.col('"position"').cast("string"), F.lit('. Podczas turnieju strzelił'), F.col('"total_goals_tournament"').cast("string"), F.lit('goli. i rozegrał'), F.col('"total_minutes_tournament"').cast("string"), F.lit('minut.')))

    # print(df_table_adjusted.select('"player_name"', '"team"', '"goals"', '"player_document"').limit(10).to_pandas())

    print("Generating vector embedings using Snowflake Cortex...")

    df_with_vectors = df_table_adjusted.withColumn(
        '"player_vector"', 
        F.call_builtin(
            "snowflake.cortex.embed_text_768", 
            F.lit('snowflake-arctic-embed-m'), 
            F.col('"player_document"')
        )
    )

    print("Vectors generated! Writing to the final Cortex table...")

    df_with_vectors.write.mode("overwrite").save_as_table("cortex_data.fifa_players_cortex")

    print("Data written successfully to the Cortex table.")


except Exception as e:
    print(f"An error occurred: {e}")



finally:
    print("Closing the Snowflake session...")
    session.close()