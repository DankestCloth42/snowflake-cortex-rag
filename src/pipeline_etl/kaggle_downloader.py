import os
import kagglehub
from dotenv import load_dotenv
from src.utils.logger_setup import get_logger

load_dotenv()

# 2. Initialize the logger for this specific module
logger = get_logger(__name__)

def download_dataset() -> str:
    """
    Downloads the dataset from Kaggle and returns the absolute path to the CSV file.
    """
    try:
        logger.info("Starting Kaggle dataset download...")
        dataset_dir = kagglehub.dataset_download("rauffauzanrambe/fifa-world-cup-2026-player-performance-dataset")
        logger.info(f"Success! Data downloaded to folder: {dataset_dir}")
        
        files = os.listdir(dataset_dir)
        logger.info(f"Found files: {files}")
        
        if files:
            csv_path = os.path.join(dataset_dir, files[0])
            csv_path = csv_path.replace("\\", "/")
            
            logger.info(f"Ready path to load: {csv_path}")
            return csv_path
        else:
            raise FileNotFoundError("No files found in the downloaded dataset directory.")
            
    except Exception as e:
        logger.error(f"An error occurred during download: {e}")
        return ""

if __name__ == "__main__":
    # Smoke test
    logger.info("Running smoke test for Kaggle downloader...")
    path = download_dataset()
    logger.info(f"Returned path: {path}")