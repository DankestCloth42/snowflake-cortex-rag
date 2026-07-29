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

source_to_stage: str = "@my_stage/fifa_world_cup_2026_player_performance.csv"


try:
    print("Connecting to Snowflake...")
    session = Session.builder.configs(connection_parameters).create()
    print("Successfully connected to Snowflake!")
    print(f"Loading files from stage {source_to_stage}...")
    
    # Używamy obiektu DataFrameReader
    df_data = session.read.options({
        "PARSE_HEADER": True,
        "INFER_SCHEMA": True,
        "FIELD_OPTIONALLY_ENCLOSED_BY": '"' 
    }).csv(f"{source_to_stage}")


    print("Data loaded successfully. Performing calculations...")

    window_spec = Window.partitionBy('"team"')

    df_data_with_calculations = df_data.withColumn('"Team_Max_Goals"', F.max('"goals"').over(window_spec))

    print("Executing MERGE operation...")
    target_table = session.table("raw_data.fifa_players_raw")

    # listing columns to generate hash in list format for the merge operation
    columns_to_hash = [F.col(c).cast("string") for c in df_data_with_calculations.columns if c != '"player_name"' and c != '"match_id"']

    df_data_with_calculations = df_data_with_calculations.withColumn(
    '"row_sk"', 
    F.hash(F.col('"player_name"'), F.col('"match_id"'))
    )

    df_data_with_calculations = df_data_with_calculations.withColumn(
        '"row_hash"', 
        F.hash(*columns_to_hash)
    )

    # listing columns to update in dictionary format for the merge operation

    column_mapping = {col: df_data_with_calculations[col] for col in df_data_with_calculations.columns}



    merge_result = target_table.merge(
        source=df_data_with_calculations,
        join_expr=target_table['"row_sk"'] == df_data_with_calculations['"row_sk"'],
        clauses=[
            F.when_matched(target_table['"row_hash"'] != df_data_with_calculations['"row_hash"']).update(column_mapping),
            F.when_not_matched().insert(column_mapping)
        ]
    )
   

    print(f"MERGE SUCCESSFUL! Rows inserted: {merge_result.rows_inserted}, Rows updated: {merge_result.rows_updated}")

except Exception as e:
    print(f"An error occurred: {e}")


finally:
    print("Closing the Snowflake session...")
    session.close()