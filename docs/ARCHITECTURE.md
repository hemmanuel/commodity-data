# Hybrid GraphRAG Architecture

## Overview
This project uses a **Hybrid Graph** approach, combining deterministic structured data (SQL) with probabilistic unstructured insights (LLM/GraphRAG). **LangGraph** serves as the orchestrator, managing agents that can query both the structured backbone and the unstructured vector store.

## Layer 1: The Skeleton (Structured Backbone)
*   **Status:** ✅ Mostly Complete
*   **Tech:** DuckDB, SQL
*   **Data Sources:** EIA (API), FERC (Forms 1, 2, 552, 714).
*   **Entities:**
    *   **Companies:** (Canonical IDs from FERC/EIA crosswalk)
    *   **Plants:** (Power plants, refineries, processing plants)
    *   **Locations:** (States, Counties, Coordinates)
*   **Relationships:**
    *   `OWNS` (Company -> Plant)
    *   `OPERATES` (Company -> Plant)
    *   `AFFILIATE_OF` (Company -> Company)
    *   `LOCATED_IN` (Plant -> Location)
*   **Purpose:** Provides the "Ground Truth" and canonical IDs to prevent entity duplication.

## Layer 2: The Flesh (Unstructured Enrichment)
*   **Status:** 🚧 Next Phase
*   **Tech:** LangChain / LlamaIndex, Vector Store (Chroma/FAISS), OpenAI/Anthropic.
*   **Data Sources:**
    *   PDFs (Annual Reports, 10-K, 10-Q)
    *   Earnings Call Transcripts
    *   News Articles
    *   Spreadsheets (unstructured/messy)
*   **New Relationships (inferred by LLM):**
    *   `PLANNING_EXPANSION` (Company -> Project)
    *   `FACING_LITIGATION` (Company -> LegalCase)
    *   `SUPPLY_CHAIN_RISK` (Company -> Region)
    *   `MENTIONED_IN` (Entity -> Document)
*   **Purpose:** Adds context, sentiment, and "soft" relationships that don't exist in structured databases.

## Layer 3: The Orchestrator (LangGraph)
*   **Status:** 📅 Planned
*   **Role:** The "Brain" of the application.
*   **Workflow:**
    1.  **User Query:** "How is the hurricane risk affecting Duke Energy's coastal assets?"
    2.  **Router Agent:** Decomposes the query.
        *   *Sub-task A (Structured):* "Find all plants owned by Duke Energy in coastal counties." (Executes SQL Tool)
        *   *Sub-task B (Unstructured):* "Search news/reports for 'hurricane damage' or 'risk' related to these plants." (Executes Vector Search Tool)
    3.  **Synthesis:** Combines the hard data (Plant Capacities, Locations) with soft data (News reports of damage) to generate a comprehensive answer.

## Entity Resolution Strategy
To avoid "graph mess," the ingestion pipeline for unstructured data will:
1.  Extract an entity (e.g., "Dominion Energy").
2.  **Fuzzy Match** against the `dim_companies` table in DuckDB.
3.  If Match > 90%: Link to existing `company_id`.
4.  If No Match: Create new node (flagged for review) or ignore.

## Deployment Plan
1.  **Initialize LangGraph:** Set up the state graph and basic agent nodes.
2.  **Tool Creation:** Wrap our existing Python scripts/SQL queries as `LangChain Tools`.
3.  **Vector Store Setup:** Create a pipeline to ingest a sample PDF, chunk it, and store embeddings.
4.  **GraphRAG Integration:** Connect the vector store to the LangGraph agent.
