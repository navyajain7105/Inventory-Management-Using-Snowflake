# Supply Chain Assistant with Snowflake Intelligence

## Solution Overview

Modern supply chain operations face a critical challenge: efficiently managing raw material inventory across multiple manufacturing facilities. Operations managers must constantly balance inventory levels, deciding whether to transfer materials between plants with excess and shortage, or purchase new materials from suppliers. Making these decisions manually is time-consuming, error-prone, and often results in suboptimal cost outcomes.

This quickstart demonstrates how to build an intelligent supply chain assistant using Snowflake Intelligence and Cortex AI capabilities. By combining natural language querying with semantic search over both structured and unstructured data, I have created a complete solution that helps operations managers make data-driven decisions about inventory management.

Here is a summary of what I have built:

* **Setup Environment**: A comprehensive supply chain database with tables for manufacturing plants, inventory, suppliers, customers, orders, shipments, and weather data
* **Cortex Analyst**: Build semantic models for supply chain operations and weather forecasts that enable natural language text-to-SQL queries
* **Cortex Search**: Index unstructured supply chain documentation for intelligent retrieval using RAG (Retrieval Augmented Generation)
* **Custom Tools**: Integrate web search, web scraping, HTML generation, and email capabilities into your AI agent
* **Snowflake Intelligence**: Create a comprehensive AI agent with 7 tools that intelligently routes user questions and combines multiple data sources
* **Advanced Analytics**: Perform complex multi-domain analysis including supply chain optimization, weather impact analysis, and external research

## The Problem

<img width="1096" height="617" alt="The Problem" src="https://github.com/user-attachments/assets/b8ce12b0-e49e-4aa0-84f7-57b40e4ffc7b" />


Supply chain operations managers face daily challenges managing raw material inventory across manufacturing facilities:

* **Inventory Imbalances**: Some plants have excess raw materials while others face shortages, creating inefficiency
* **Complex Decision Making**: Determining whether to transfer materials between plants or purchase from suppliers requires analyzing multiple factors including material costs, transport costs, lead times, and safety stock levels
* **Manual Analysis**: Traditional approaches require running multiple reports, spreadsheet analysis, and manual cost comparisons
* **Time Sensitivity**: Inventory decisions need to be made quickly to avoid production delays or excess carrying costs

## The Solution

<img width="1095" height="615" alt="The Solution" src="https://github.com/user-attachments/assets/6ea48112-d5d6-4316-84fd-da10477601a7" />

This solution leverages Snowflake Intelligence and Cortex AI capabilities to create an intelligent assistant that:

1. **Answers Ad-Hoc Questions**: Operations managers can ask natural language questions about inventory levels, orders, shipments, and supplier information - the agent automatically converts questions to SQL and executes them
2. **Provides Contextual Information**: The assistant can search and retrieve relevant information from supply chain documentation using semantic search
3. **Intelligent Routing**: Automatically determines whether to query structured data (via Cortex Analyst) or search documents (via Cortex Search) based on the nature of the question
4. **Complex Analysis**: Handles sophisticated multi-table queries like identifying plants with low inventory alongside plants with excess inventory of the same materials, and comparing costs between suppliers and inter-plant transfers
5. **No-Code Agent Creation**: Build and deploy the entire solution using Snowflake Intelligence's visual interface without writing application code


##Can answer Supply Chain Data Questions (Cortex Analyst - Supply Chain Model):**

* "How many orders did we receive in the last month?"
* "Which manufacturing plants have low inventory for which raw materials?"
* "Who are our top 5 customers by order value?"
* "What's the total quantity of finished goods in our manufacturing plants?"
* "Which manufacturing plants have low inventory of raw materials AND which plants have excess inventory of those same materials?"
* "For plants with low inventory of a raw material, compare the cost of replenishing from a supplier vs transferring from another plant with excess inventory"

**Weather Data Questions (Cortex Analyst - Weather Model):**

* "What's the weather forecast for Seattle?"
* "Which cities have the highest precipitation probability?"
* "Show me the temperature forecast for Phoenix"
* "What are the wind conditions in Chicago?"

**Documentation Questions (Cortex Search):**

* "Explain how shipment tracking works in our business"
* "What are our business lines?"
* "How does our supply chain network operate?"

**Web Research Questions (Custom Tools - Web Search & Web Scrape):**

* "Search the web for recent supply chain disruptions"
* "What are the latest trends in supply chain management?"

**Email and Newsletter Creation (Custom Tools):**

* "Create an HTML newsletter summarizing our top customers this month"
* "Draft an email about our current inventory status" (Note: sending requires email integration)

**Cross-Tool Complex Questions:**

* "What's the weather forecast for cities where our manufacturing plants are located?"
* "Compare inventory levels at plants with upcoming severe weather conditions"
