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

def main():
    try:
        session = Session.builder.configs(connection_parameters).create()
        current_version = session.sql("SELECT CURRENT_VERSION()").collect()[0][0]
        current_role = session.sql("SELECT CURRENT_ROLE()").collect()[0][0]
        current_warehouse = session.sql("SELECT CURRENT_WAREHOUSE()").collect()[0][0]
        current_database = session.sql("SELECT CURRENT_DATABASE()").collect()[0][0]
        current_schema = session.sql("SELECT CURRENT_SCHEMA()").collect()[0][0]
        print(f"Successfully connected to Snowflake!\nCurrent version: {current_version},\nCurrent role: {current_role},\nCurrent warehouse: {current_warehouse},\nCurrent database: {current_database},\nCurrent schema: {current_schema}")
        session.close()
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
