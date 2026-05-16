# SHL Conversational Assessment Recommender

AI-powered conversational recommendation system for SHL assessments.

## Features
- Conversational recommendations
- SHL catalog retrieval
- ChromaDB semantic search
- FastAPI backend
- Groq LLM integration

## API Endpoints

### Health Check
GET /health

### Chat Endpoint
POST /chat

## Run Locally

```bash
pip install -r requirements.txt
python embeddings.py
python -m uvicorn app:app --reload
```
