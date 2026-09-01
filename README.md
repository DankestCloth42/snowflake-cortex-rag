# ⚽ FIFA '26 AI Scout (Snowflake RAG)

A production-grade, automated Retrieval-Augmented Generation (RAG) pipeline and chatbot interface. This project ingests football player performance data, vectorizes it using Snowflake Cortex, and serves it through a hybrid search engine powered by Google Gemini.

## 🏗️ Architecture & Features

This repository is built with scalability, data engineering best practices, and DevOps standards in mind:

* **Modular Architecture:** Fully structured `src/` directory separating ETL, utilities, RAG engine, and application layers.
* **Automated ETL Orchestration:** A centralized orchestrator (`run_etl_pipeline.py`) manages data extraction from Kaggle, staging, and loading.
* **SCD Type 1 Delta Loads:** Implements Snowflake `MERGE` operations utilizing calculated hashes (`row_sk`, `row_hash`) to optimize compute costs.
* **Hybrid RAG Engine:** Combines exact SQL filtering (extracted via LLM) with Vector Cosine Similarity for highly accurate context retrieval.
* **Containerized Deployment:** Fully dockerized environment (`Dockerfile`, `docker-compose`) ensuring consistent execution across different platforms.

## ⚙️ Configuration (.env)

Before running the project (either locally or via Docker), you must create a `.env` file in the root directory with the following credentials:

```ini
# Snowflake Credentials
SNOWFLAKE_ACCOUNT=your_account
SNOWFLAKE_USER=your_user
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_ROLE=your_role
SNOWFLAKE_WAREHOUSE=your_warehouse
SNOWFLAKE_DATABASE=your_database
SNOWFLAKE_SCHEMA=your_schema

# AI Providers
GEMINI_API_KEY=your_gemini_api_key

# Kaggle API
KAGGLE_USERNAME=your_kaggle_username
KAGGLE_KEY=your_kaggle_key


## 🚀 How to Run

### Option A: Using Docker (Recommended)
The easiest way to run the Streamlit interface without worrying about local dependencies is using Docker Compose.

```bash
# Build and run the container
docker-compose up --build

The Streamlit app will be available at http://localhost:8501.

### Option B: Local Environment
If you prefer running the code locally, ensure you have Python 3.9+ installed.
    ```bash 
    # 1. Install Dependencies:
    
    pip install -r requirements.txt

    # 2. Run the ETL Pipeline: (Executes data extraction, delta loads, and vector embeddings)

    python run_etl_pipeline.py

    # 3. Launch the AI Scout Interface:

    python -m streamlit run src/app/chat_interface.py