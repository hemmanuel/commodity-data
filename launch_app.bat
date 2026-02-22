@echo off
echo Starting Commodity Data App...

:: Start Backend
start "Commodity Data Backend" cmd /k "call .venv\Scripts\activate && uvicorn backend.api:app --reload --port 8000"

:: Start Frontend
:: We need to ensure node is in path.
start "Commodity Data Frontend" cmd /k "set PATH=%PATH%;C:\Program Files\nodejs && cd frontend && npm run dev"

echo App is starting...
echo Backend: http://localhost:8000
echo Frontend: http://localhost:5173
pause
