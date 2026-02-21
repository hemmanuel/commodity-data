@echo off
powershell -NoProfile -ExecutionPolicy Bypass -Command ".venv\Scripts\Activate.ps1; python scripts/query_db.py"
