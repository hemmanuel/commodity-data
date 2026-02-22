# Commodity Data Dashboard (v2)

This is a modern, client-side application for viewing and exploring commodity data (EIA, FERC).

## Architecture

- **Frontend:** React (Vite) + Tailwind CSS + Recharts
- **Backend:** Python (FastAPI) + DuckDB
- **Database:** DuckDB (Snapshot-based access to avoid file locks)

## Prerequisites

- Python 3.12+
- Node.js (Installed automatically via `winget` if missing, or manually)

## Running the App

Simply run the `launch_app.bat` script in the root directory.

This will open two terminal windows:
1. **Backend:** Running on `http://localhost:8000`
2. **Frontend:** Running on `http://localhost:5173` (Open this in your browser)

## Features

- **Dashboard:** Real-time ingestion status and system overview.
- **EIA Browser:** Search and visualize historical time-series data.
- **FERC Browser:** Browse and filter FERC Form 2 respondent data.
