import sys
from dotenv import load_dotenv
from src.utils.logger_setup import get_logger
from src.pipeline_etl.kaggle_downloader import download_dataset
from src.pipeline_etl.data_uploader_internal_stage import upload_to_snowflake
from src.pipeline_etl.initial_load import initial_load
from src.pipeline_etl.delta_load import delta_load
from src.pipeline_etl.prepare_cortex_docs import prepare_cortex_docs

load_dotenv()
logger = get_logger(__name__)

def main():
    logger.info("🚀 STARTING FULL ETL PIPELINE 🚀")
    
    try:
        logger.info("--- STEP 1: Downloading Data from Kaggle ---")
        file_path = download_dataset()
        if not file_path:
            raise RuntimeError("Pipeline stopped: Data download failed.")
            
        logger.info("--- STEP 2: Uploading to Snowflake Stage ---")
        upload_to_snowflake(file_path)
        
        logger.info("--- STEP 3: Loading Data into Raw Tables ---")
        initial_load()
        delta_load()
        
        logger.info("--- STEP 4: Creating Cortex Documents & Vectors ---")
        prepare_cortex_docs()
        
        logger.info("✅ FULL ETL PIPELINE COMPLETED SUCCESSFULLY! ✅")
        
    except Exception as e:
        logger.critical(f"❌ PIPELINE FAILED: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()