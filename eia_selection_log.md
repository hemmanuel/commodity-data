# EIA Bulk Data Selection Log

This document outlines the selection criteria for the initial bulk download of EIA datasets. The selection is based on the mission to map physical commodity supply chains to financial market impacts, focusing on global macro dynamics, regional constraints, and firm valuations.

| Dataset Identifier | Status | Justification |
| :--- | :--- | :--- |
| **AEO.2014** | EXCLUDE | Historical forecast; prioritizing current baseline (AEO.2025) for initial system state. |
| **AEO.2015** | EXCLUDE | Historical forecast; prioritizing current baseline (AEO.2025) for initial system state. |
| **AEO.2016** | EXCLUDE | Historical forecast; prioritizing current baseline (AEO.2025) for initial system state. |
| **AEO.2017** | EXCLUDE | Historical forecast; prioritizing current baseline (AEO.2025) for initial system state. |
| **AEO.2018** | EXCLUDE | Historical forecast; prioritizing current baseline (AEO.2025) for initial system state. |
| **AEO.2019** | EXCLUDE | Historical forecast; prioritizing current baseline (AEO.2025) for initial system state. |
| **AEO.2020** | EXCLUDE | Historical forecast; prioritizing current baseline (AEO.2025) for initial system state. |
| **AEO.2021** | EXCLUDE | Historical forecast; prioritizing current baseline (AEO.2025) for initial system state. |
| **AEO.2022** | EXCLUDE | Historical forecast; prioritizing current baseline (AEO.2025) for initial system state. |
| **AEO.2023** | EXCLUDE | Historical forecast; prioritizing current baseline (AEO.2025) for initial system state. |
| **AEO.2025** | **INCLUDE** | Provides the current long-term baseline for firm valuations and forward curve modeling. |
| **AEO.IEO2** | EXCLUDE | Redundant or superseded by the more comprehensive `IEO` dataset for international outlooks. |
| **COAL** | **INCLUDE** | Critical for analyzing alternative baseloads and fuel-switching economics in power generation. |
| **EBA** | **INCLUDE** | Essential for mapping physical grid constraints (e.g., ERCOT dispatch) and real-time market impacts. |
| **ELEC** | **INCLUDE** | Fundamental supply/demand data for power markets, essential for utility firm valuation. |
| **EMISS** | **INCLUDE** | Key for modeling regulatory risk pricing (carbon tax) and ESG-driven capital flows. |
| **IEO** | **INCLUDE** | Provides global macro context and international energy trade flow projections. |
| **INTL** | **INCLUDE** | Granular country-level data essential for mapping global supply chains and geopolitical risk. |
| **NG** | **INCLUDE** | Core commodity dataset for natural gas forward curves, basis differentials, and storage dynamics. |
| **NUC_STATUS** | **INCLUDE** | High-impact supply shock data for nuclear baseload availability, affecting regional power prices. |
| **PET** | **INCLUDE** | Core commodity dataset for liquid fuels, refining margins, and global petroleum market dynamics. |
| **PET_IMPORTS** | **INCLUDE** | Critical for tracking physical trade flows, port-level bottlenecks, and supply chain shifts. |
| **SEDS** | **INCLUDE** | Provides regional granularity for state-level policy impact and consumption analysis. |
| **STEO** | **INCLUDE** | Market-moving short-term forecasts essential for near-term curve trading and liquidity event analysis. |
| **TOTAL** | **INCLUDE** | Macro-level energy balance data for broad economic outlooks and cross-commodity correlation. |
