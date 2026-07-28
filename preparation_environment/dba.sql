USE ROLE ACCOUNTADMIN

-- 1. Creation of a role for the RAG engineer
CREATE ROLE rag_engineer_role;
GRANT ROLE rag_engineer_role TO USER "OSKARGUSTAW";

-- 2. Creating a warehouse for the RAG engineer
CREATE WAREHOUSE rag_wh 
  WITH WAREHOUSE_SIZE = 'XSMALL' 
  AUTO_SUSPEND = 60 
  AUTO_RESUME = TRUE;
GRANT USAGE ON WAREHOUSE rag_wh TO ROLE rag_engineer_role;

-- 3. Creating the database and schema
CREATE DATABASE rag_project_db;
GRANT OWNERSHIP ON DATABASE rag_project_db TO ROLE rag_engineer_role;

USE ROLE rag_engineer_role;
CREATE SCHEMA rag_project_db.raw_data;


--utils stuff

create schema rag_project_db.util;


CREATE OR REPLACE FILE FORMAT util.myformat
TYPE = CSV
PARSE_HEADER = TRUE;
