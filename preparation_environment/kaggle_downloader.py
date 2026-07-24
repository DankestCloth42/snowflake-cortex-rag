import os
import kagglehub
from dotenv import load_dotenv

load_dotenv()


def main():
    try:
        dataset_dir = kagglehub.dataset_download("rauffauzanrambe/fifa-world-cup-2026-player-performance-dataset")
        print(f"Success! Data downloaded to folder: {dataset_dir}")
        files = os.listdir(dataset_dir)
        print(f"Found files: {files}")
        if files:
            csv_path = os.path.join(dataset_dir, files[0])
            print(f"Ready path to load: {csv_path}")
    except Exception as e:
        print("An error occurred:", e)


if __name__ == "__main__":
    main()
