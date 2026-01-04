-- Set up environment
USE SUPPLY_CHAIN_ASSISTANT_DB.ENTITIES;
USE WAREHOUSE SUPPLY_CHAIN_ASSISTANT_WH;
USE ROLE SUPPLY_CHAIN_ASSISTANT_ROLE;

-- Scale up warehouse for PDF parsing (compute-intensive operation)
ALTER WAREHOUSE SUPPLY_CHAIN_ASSISTANT_WH SET WAREHOUSE_SIZE = 'X-LARGE';

-- Parse all PDFs from the stage using Cortex PARSE_DOCUMENT
-- Extracts text content with layout information from each PDF
CREATE OR REPLACE TABLE PARSE_PDFS AS 
SELECT RELATIVE_PATH, SNOWFLAKE.CORTEX.PARSE_DOCUMENT(@SUPPLY_CHAIN_ASSISTANT_DB.ENTITIES.SUPPLY_CHAIN_ASSISTANT_PDF_STAGE,RELATIVE_PATH,{'mode':'LAYOUT'}) AS DATA
    FROM DIRECTORY(@SUPPLY_CHAIN_ASSISTANT_DB.ENTITIES.SUPPLY_CHAIN_ASSISTANT_PDF_STAGE);

-- Chunk the parsed PDF content into searchable segments
-- Split into 1800-character chunks with 300-character overlap for context continuity
-- Generate presigned URLs for clickable links to source PDFs (valid for 7 days)
CREATE OR REPLACE TABLE PARSED_PDFS AS (
    WITH TMP_PARSED AS (SELECT
        RELATIVE_PATH,
        SNOWFLAKE.CORTEX.SPLIT_TEXT_RECURSIVE_CHARACTER(TO_VARIANT(DATA):content, 'MARKDOWN', 1800, 300) AS CHUNKS
    FROM PARSE_PDFS WHERE TO_VARIANT(DATA):content IS NOT NULL)
    SELECT
        TO_VARCHAR(C.value) AS PAGE_CONTENT,                              -- The searchable text content
        REGEXP_REPLACE(RELATIVE_PATH, '\\.pdf$', '') AS TITLE,             -- Document title (filename without .pdf)
        'SUPPLY_CHAIN_ASSISTANT_DB.ENTITIES.SUPPLY_CHAIN_ASSISTANT_PDF_STAGE' AS INPUT_STAGE,
        RELATIVE_PATH AS RELATIVE_PATH,                                    -- Original file path
        GET_PRESIGNED_URL(@SUPPLY_CHAIN_ASSISTANT_DB.ENTITIES.SUPPLY_CHAIN_ASSISTANT_PDF_STAGE, RELATIVE_PATH, 604800) AS PRESIGNED_URL  -- Clickable URL (expires in 7 days)
    FROM TMP_PARSED P, LATERAL FLATTEN(INPUT => P.CHUNKS) C
);

-- Scale warehouse back down after heavy processing is complete
ALTER WAREHOUSE SUPPLY_CHAIN_ASSISTANT_WH SET WAREHOUSE_SIZE = 'SMALL';

-- Create Cortex Search Service for semantic search over PDF content
-- PAGE_URL maps to the presigned URL for clickable source links in Snowflake Intelligence
CREATE OR REPLACE CORTEX SEARCH SERVICE SUPPLY_CHAIN_ASSISTANT_DB.ENTITIES.SUPPLY_CHAIN_INFO
ON PAGE_CONTENT                                      -- Primary search field
WAREHOUSE = SUPPLY_CHAIN_ASSISTANT_WH
TARGET_LAG = '1 hour'                                -- Refresh interval for new documents
AS (
    SELECT PRESIGNED_URL AS PAGE_URL, PAGE_CONTENT, TITLE, RELATIVE_PATH
    FROM PARSED_PDFS
);

-- Create scheduled task to refresh presigned URLs before they expire
-- Presigned URLs expire after 7 days, so refresh daily to ensure links remain valid
CREATE OR REPLACE TASK SUPPLY_CHAIN_ASSISTANT_DB.ENTITIES.REFRESH_PRESIGNED_URLS_TASK
  WAREHOUSE = SUPPLY_CHAIN_ASSISTANT_WH
  SCHEDULE = 'USING CRON 0 1 * * * America/Los_Angeles'  -- Runs daily at 1:00 AM PST
AS
UPDATE SUPPLY_CHAIN_ASSISTANT_DB.ENTITIES.PARSED_PDFS
SET PRESIGNED_URL = GET_PRESIGNED_URL(@SUPPLY_CHAIN_ASSISTANT_DB.ENTITIES.SUPPLY_CHAIN_ASSISTANT_PDF_STAGE, RELATIVE_PATH, 604800);

-- Activate the task to start automatic URL refresh
ALTER TASK SUPPLY_CHAIN_ASSISTANT_DB.ENTITIES.REFRESH_PRESIGNED_URLS_TASK RESUME;