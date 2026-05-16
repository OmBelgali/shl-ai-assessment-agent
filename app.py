from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
import chromadb
from sentence_transformers import SentenceTransformer
from groq import Groq
from dotenv import load_dotenv
import os

# -----------------------------
# LOAD ENV VARIABLES
# -----------------------------

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client_groq = Groq(api_key=GROQ_API_KEY)

# -----------------------------
# FASTAPI APP
# -----------------------------

app = FastAPI()

# -----------------------------
# VECTOR DATABASE
# -----------------------------

client = chromadb.PersistentClient(path="./vector_store")

collection = client.get_collection("shl_assessments")

embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# -----------------------------
# REQUEST SCHEMAS
# -----------------------------

class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[Message]

# -----------------------------
# HEALTH ENDPOINT
# -----------------------------

@app.get("/health")
def health():
    return {"status": "ok"}

# -----------------------------
# HELPER FUNCTIONS
# -----------------------------

def is_vague_query(text):

    text = text.lower()

    role_keywords = [
        "developer",
        "engineer",
        "manager",
        "analyst",
        "sales",
        "java",
        "python",
        "backend",
        "frontend",
        "leader",
        "consultant"
    ]

    has_role = any(word in text for word in role_keywords)

    return not has_role


def is_comparison_query(text):

    comparison_words = [
        "compare",
        "difference",
        "vs",
        "versus"
    ]

    text = text.lower()

    return any(word in text for word in comparison_words)


def build_conversation_context(messages):

    context = []

    for msg in messages:
        context.append(f"{msg.role}: {msg.content}")

    return "\n".join(context)


def retrieve_assessments(query, top_k=3):

    top_k = min(top_k, 10)

    query_lower = query.lower()

    # Important keywords
    keywords = []

    possible_keywords = [
        "java",
        "python",
        "developer",
        "backend",
        "frontend",
        "communication",
        "personality",
        "cognitive",
        "leadership",
        "sales",
        "manager",
        "analytics",
        "software"
    ]

    for word in possible_keywords:
        if word in query_lower:
            keywords.append(word)

    # Vector search
    query_embedding = embedding_model.encode(query).tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=20
    )

    filtered = []

    for meta, doc in zip(
        results["metadatas"][0],
        results["documents"][0]
    ):

        doc_lower = doc.lower()

        keyword_score = sum(
            keyword in doc_lower
            for keyword in keywords
        )

        filtered.append({
            "score": keyword_score,
            "data": {
                "name": meta["name"],
                "url": meta["url"],
                "test_type": meta["test_type"]
            }
        })

    # Sort by keyword score
    filtered.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    recommendations = [
        item["data"]
        for item in filtered[:top_k]
    ]

    return recommendations


def generate_llm_response(prompt):

    response = client_groq.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.3
    )

    return response.choices[0].message.content

# -----------------------------
# CHAT ENDPOINT
# -----------------------------

@app.post("/chat")
def chat(request: ChatRequest):

    try:

        messages = request.messages

        conversation_context = build_conversation_context(messages)

        latest_user_message = ""

        # -----------------------------
        # GET LATEST USER MESSAGE
        # -----------------------------

        for msg in reversed(messages):

            if msg.role == "user":
                latest_user_message = msg.content
                break

        # -----------------------------
        # REFUSAL LOGIC
        # -----------------------------

        banned_topics = [
            "salary",
            "legal",
            "politics",
            "religion",
            "ignore instructions",
            "bypass",
            "hack"
        ]

        if any(word in latest_user_message.lower() for word in banned_topics):

            return {
                "reply": "I can only help with SHL assessment recommendations.",
                "recommendations": [],
                "end_of_conversation": False
            }

        # -----------------------------
        # COMPARISON LOGIC
        # -----------------------------

        if is_comparison_query(latest_user_message):

            recommendations = retrieve_assessments(
                latest_user_message,
                top_k=2
            )

            catalog_context = ""

            for rec in recommendations:

                catalog_context += f"""
                Name: {rec['name']}
                URL: {rec['url']}
                Type: {rec['test_type']}
                """

            prompt = f"""
            You are an SHL assessment comparison assistant.

            STRICT RULES:
            - ONLY use the provided catalog context.
            - NEVER invent information.
            - NEVER invent URLs.
            - Compare clearly and concisely.

            User query:
            {latest_user_message}

            Catalog context:
            {catalog_context}
            """

            reply_text = generate_llm_response(prompt)

            return {
                "reply": reply_text,
                "recommendations": recommendations,
                "end_of_conversation": False
            }

        # -----------------------------
        # CLARIFICATION LOGIC
        # -----------------------------

        if is_vague_query(latest_user_message):

            return {
                "reply": (
                    "Could you share more details about the role, "
                    "seniority level, and required skills?"
                ),
                "recommendations": [],
                "end_of_conversation": False
            }

        # -----------------------------
        # RETRIEVE ASSESSMENTS
        # -----------------------------

        recommendations = retrieve_assessments(
            conversation_context,
            top_k=3
        )

        # -----------------------------
        # BUILD CATALOG CONTEXT
        # -----------------------------

        catalog_context = ""

        for rec in recommendations:

            catalog_context += f"""
            Name: {rec['name']}
            URL: {rec['url']}
            Type: {rec['test_type']}
            """

        # -----------------------------
        # MAIN PROMPT
        # -----------------------------

        prompt = f"""
        You are an SHL assessment recommendation assistant.

        STRICT RULES:
        - ONLY recommend assessments from the provided catalog context.
        - NEVER invent assessment names.
        - NEVER invent URLs.
        - NEVER recommend anything outside SHL catalog.
        - Keep answers concise and professional.
        - If information is unavailable, say so clearly.

        Conversation:
        {conversation_context}

        Catalog context:
        {catalog_context}

        Generate:
        1. A short recommendation summary
        2. Why these assessments fit
        3. Mention technical/personality/cognitive alignment
        """

        reply_text = generate_llm_response(prompt)

        return {
            "reply": reply_text,
            "recommendations": recommendations,
            "end_of_conversation": len(recommendations) > 0
        }

    except Exception as e:

        return {
            "reply": f"Error: {str(e)}",
            "recommendations": [],
            "end_of_conversation": False
        }