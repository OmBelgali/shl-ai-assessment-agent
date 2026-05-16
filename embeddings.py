import json
import chromadb
from sentence_transformers import SentenceTransformer

# Load embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

# Create ChromaDB client
client = chromadb.PersistentClient(path="./vector_store")

# Create collection
collection = client.get_or_create_collection(
    name="shl_assessments"
)

# Load catalog data
with open("catalog.json", "r", encoding="utf-8") as f:
    catalog = json.load(f)

documents = []
metadatas = []
ids = []

for idx, item in enumerate(catalog):

    # Combine important fields into searchable text
    combined_text = f"""
    Assessment Name: {item.get('name', '')}

    Description:
    {item.get('description', '')}

    Job Level:
    {item.get('job_level', '')}

    Languages:
    {item.get('languages', '')}

    Assessment Length:
    {item.get('assessment_length', '')}

    Test Type:
    {item.get('test_type', '')}

    Skills:
    Java
    Python
    Software Development
    Programming
    Problem Solving
    Communication
    Leadership
    Stakeholder Management
    Technical Skills
    Cognitive Ability
    Personality Assessment
    """

    documents.append(combined_text)

    metadatas.append({
        "name": item.get("name", ""),
        "url": item.get("url", ""),
        "test_type": item.get("test_type", "")
    })

    ids.append(str(idx))

# Generate embeddings
embeddings = model.encode(documents).tolist()

# Store in ChromaDB
collection.add(
    documents=documents,
    embeddings=embeddings,
    metadatas=metadatas,
    ids=ids
)

print(f"Stored {len(documents)} assessments in vector DB!")