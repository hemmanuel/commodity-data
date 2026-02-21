@echo off
powershell -NoProfile -ExecutionPolicy Bypass -Command ".venv\Scripts\Activate.ps1; python scripts/ingestion/monitor_db.py"
