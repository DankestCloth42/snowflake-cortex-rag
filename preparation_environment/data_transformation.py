import os 
from dotenv import load_dotenv
from snowflake.snowpark import Session
from snowflake.snowpark.functions import col, max
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

    df_data_with_calculations = df_data.withColumn('"Team_Max_Goals"', max('"goals"').over(window_spec))


    print("Calculations performed successfully. Writing to Snowflake table...")


    df_data_with_calculations.write.mode("overwrite").save_as_table("raw_data.fifa_players_raw")
    #print(df_data_with_calculations.select('"player_name"', '"team"', '"goals"', '"Team_Max_Goals"').limit(10).to_pandas()) ##testing


    print("Data written to Snowflake table successfully.")

except Exception as e:
    print(f"An error occurred: {e}")


finally:
    print("Closing the Snowflake session...")
    session.close()