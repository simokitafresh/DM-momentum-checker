# Dual Momentum Calculator MVP

A minimal FastAPI app that computes simple momentum for up to 5 tickers across common anchor dates. Includes a single HTML page frontend and a tiny API client.

## Features
- Unit-based momentum: month, week, day
- Common anchor dates across all symbols
- Saturday rounding for weekly unit
- Graceful handling of missing data (returns None)

## Tech Stack
- Python 3.12+
- FastAPI, Starlette
- Pydantic v2
- requests, python-dotenv, python-dateutil

## Local Development
1. Change into the project directory:
   - `cd dual-momentum-mvp`
2. (Optional) Create a virtual environment:
   - `python -m venv .venv && .venv\\Scripts\\activate` (Windows)
3. Install dependencies:
   - `pip install -r requirements.txt`
4. Create an environment file:
   - Copy `.env.example` to `.env` and adjust if needed
5. Run the app:
   - `uvicorn main:app --reload --port 8000`
6. Open in browser:
   - `http://localhost:8000/` (frontend)
   - `http://localhost:8000/health` (health check)

## API
- `GET /` → Serves `static/index.html`
- `GET /health` → `{ status, api_base }`
- `POST /compute` → Calculate momentum
  - Request JSON:
    ```json
    { "tickers": ["AAPL"], "unit": "month", "n": 3, "as_of_period": "2025-09" }
    ```
  - Response JSON:
    ```json
    {
      "results": [0.034],
      "summary": {"tickers": ["AAPL"], "unit": "month", "n": 3, "as_of_period": "2025-09"},
      "anchors": {"current": "2025-08-30", "past": "2025-05-31"}
    }
    ```

## Deployment Notes (Render)
- Service type: Web Service (Python)
- Environment variables:
  - `STOCK_API_BASE` (default provided)
  - `API_KEY` (optional)
  - `PYTHON_VERSION` (recommended) e.g., `3.12.5`

## License
This MVP is intended for internal evaluation and testing.
