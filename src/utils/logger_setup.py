import os
import logging 
from datetime import datetime


def get_logger(script_name: str) -> logging.Logger:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_directory = f'./logs/{timestamp}'
    os.makedirs(log_directory, exist_ok=True)

    log_file_path = f'{log_directory}/{script_name}_{timestamp}.log'

    logger = logging.getLogger(script_name)
    logger.setLevel(logging.INFO)


    if not logger.handlers:

        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')


        # Create a file handler to write logs to a file
        file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
        file_handler.setFormatter(formatter)

        # Create a file handler to wirte log to a file
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)


        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger
