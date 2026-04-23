# FinChat - Backend (FastAPI & AI Core)

This repository contains the backend service for **FinChat**, an AI-powered financial assistant capable of fetching real-time cryptocurrency data and generating insightful market analyses.

🔗 **Frontend Repository:** https://github.com/YakupEmreCelebi/FinChat-Frontend

🌍 **Live Deployment:** https://finchat-ochre.vercel.app/

## 🏗️ Architecture & Technologies
- **Framework:** Python, FastAPI, HTTPX
- **AI Integration:** OpenAI API (gpt-4o-mini with Function Calling)
- **Data Source:** CoinGecko API (Crypto Prices & Historical Data)
- **Streaming:** Implementation of Server-Sent Events (`text/event-stream`) for real-time typewriter effects without proxy buffering.

---

## ⚙️ Environment Variables

Create a `.env` file in the root of this repository based on the provided `.env.example`:

```env
OPENAI_API_KEY=your_openai_api_key
COINGECKO_API_KEY=your_coingecko_api_key
```

---

## 🚀 How to Run Locally (Docker - Level 3 Production Ready)

This project is fully containerized using a lightweight Python environment. To spin up both the Backend and Frontend simultaneously with a single command, you need to set up a parent directory orchestrator.

### 1. Directory Structure
Create a parent folder and clone both repositories inside it so they sit side-by-side. Make sure the folder names match the compose file:
```text
parent-folder/
 ├── FinChatPhyton/       # (This Backend Repository)
 └── FinChat-Frontend/    # (Frontend Repository)
```

### 2. Create the Orchestrator
Create a `docker-compose.yml` file directly inside the `parent-folder/` and paste the following configuration:

```yaml
version: '3.8'

services:
  backend:
    build: ./FinChatPhyton
    ports:
      - "8000:8000"
    env_file:
      - ./FinChatPhyton/.env
    networks:
      - finchat-network

  frontend:
    build: ./FinChat-Frontend
    ports:
      - "3000:80"
    depends_on:
      - backend
    networks:
      - finchat-network

networks:
  finchat-network:
    driver: bridge
```

### 3. Run the Application
Open your terminal in the `parent-folder/` and run:
```bash
docker compose up --build
```
Once the build is complete, the Backend API will be available at `http://localhost:8000` (You can visit `http://localhost:8000/docs` for Swagger UI).

---

## 💻 How to Run Locally (Manual Mode)

If you prefer not to use Docker, you can run the backend server manually:

1. **Navigate to the backend directory:**
   ```bash
   cd FinChatPhyton
   ```

2. **Install dependencies:**
   It is recommended to use a virtual environment.
   ```bash
   pip install -r requirements.txt
   ```

3. **Start the FastAPI server:**
   ```bash
   uvicorn main:app --reload
   ```

4. The API will be running at `http://127.0.0.1:8000`.

---

*This project was developed as a Software Engineering Internship submission for Beyond Tech.*
