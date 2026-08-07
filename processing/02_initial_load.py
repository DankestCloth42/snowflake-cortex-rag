import os 
from dotenv import load_dotenv
from snowflake.snowpark import Session
import snowflake.snowpark.functions as F
from snowflake.snowpark.window import Window
from logger_setup import get_logger


load_dotenv()

logger = get_logger('02_initial_load')

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

source_to_stage: str = "@my_stage/fifa_world_cup_2026_player_performance.csv"


try:
    logger.info("Connecting to Snowflake...")
    session = Session.builder.configs(connection_parameters).create()
    logger.info("Successfully connected to Snowflake!")
    logger.info(f"Loading files from stage {source_to_stage}...")
    
    # Używamy obiektu DataFrameReader
    df_data = session.read.options({
        "PARSE_HEADER": True,
        "INFER_SCHEMA": True,
        "FIELD_OPTIONALLY_ENCLOSED_BY": '"' 
    }).csv(f"{source_to_stage}")


    logger.info("Data loaded successfully. Performing calculations...")

    window_spec = Window.partitionBy('"team"')

    df_data_with_calculations = df_data.withColumn('"Team_Max_Goals"', F.max('"goals"').over(window_spec))

    columns_to_hash = [F.col(c).cast("string") for c in df_data_with_calculations.columns if c != '"player_name"' and c != '"match_id"']

    df_data_with_calculations = df_data_with_calculations.withColumn(
    '"row_sk"', 
    F.hash(F.col('"player_name"'), F.col('"match_id"'))
    )

    df_data_with_calculations = df_data_with_calculations.withColumn(
        '"row_hash"', 
        F.hash(*columns_to_hash)
    )

    logger.info("Calculations performed successfully. Writing to Snowflake table...")


    df_data_with_calculations.write.mode("overwrite").save_as_table("raw_data.fifa_players_raw")

    row_count = session.sql("""
        SELECT ROW_COUNT 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_SCHEMA = 'RAW_DATA' 
        AND TABLE_NAME = 'FIFA_PLAYERS_RAW'
    """).collect()[0][0]

    logger.info(f"Data written to Snowflake table successfully. Rows written: {row_count}")


except Exception as e:
    logger.error(f"An error occurred: {e}")


finally:
    logger.info("Closing the Snowflake session...")
    session.close()