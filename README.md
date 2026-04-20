# FinChat - Backend (FastAPI & AI Core)

This repository contains the backend service for **FinChat**, an AI-powered financial assistant capable of fetching real-time cryptocurrency data and generating insightful market analyses.

🔗 **Frontend Repository:** [https://github.com/YakupEmreCelebi/FinChat-Frontend]
🌍 **Live Deployment:** [https://finchat-fxjj2bcnb-yakupemrecelebis-projects.vercel.app/]

## Architecture & Technologies
- Python, FastAPI, HTTPX
- OpenAI API (gpt-4o-mini with Function Calling)
- CoinGecko API (Crypto Prices & Historical Data)
- **Streaming:** Implementation of Server-Sent Events (`text/event-stream`) for real-time typewriter effects without proxy buffering.

## Environment Variables
Create a `.env` file in the root of this repository based on the provided `.env.example`:
```env
OPENAI_API_KEY=your_openai_api_key
COINGECKO_API_KEY=your_coingecko_api_key
