import os 
from dotenv import load_dotenv
from snowflake.snowpark import Session

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

sf_stage_name:str = "my_stage"
upload_file_path:str = "C:/Users/ogus/.cache/kagglehub/datasets/rauffauzanrambe/fifa-world-cup-2026-player-performance-dataset/versions/1/*.csv"

try:
    print("Connecting to Snowflake...")
    session = Session.builder.configs(connection_parameters).create()
    print("Successfully connected to Snowflake!")
    print("Creating stage if it does not exist...")
    session.sql(f"CREATE STAGE IF NOT EXISTS {sf_stage_name}").collect()
    print(f"Stage {sf_stage_name} is ready.")

    print(f"Uploading file {upload_file_path} to stage {sf_stage_name}...")
    put_results = session.file.put(local_file_name = upload_file_path, stage_location = f"@{sf_stage_name}", overwrite=True, auto_compress = False)

    for result in put_results:
        print(f"File {result.source} uploaded to {result.target} with status: {result.status}")

    print(f"Files from {upload_file_path} uploaded successfully.")

    session.close()


except Exception as e:
    print(f"An error occurred: {e}")