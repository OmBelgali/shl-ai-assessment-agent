# SHL Conversational Assessment Recommender

AI-powered conversational recommendation system for SHL assessments.

## Features

- Conversational assessment recommendations
- Multi-turn conversation handling
- Semantic retrieval using ChromaDB
- FastAPI backend
- Groq LLM integration
- Comparison support
- Clarification handling
- Off-topic refusal handling

---

## Tech Stack

- FastAPI
- ChromaDB
- Sentence Transformers
- Groq API
- Python

---

## API Endpoints

### Health Check

GET /health

### Chat Endpoint

POST /chat

Example request:

```json
{
  "messages": [
    {
      "role": "user",
      "content": "Hiring Java developer"
    }
  ]
}
```
