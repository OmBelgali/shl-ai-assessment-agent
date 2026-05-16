import chromadb
from sentence_transformers import SentenceTransformer

# Load model
model = SentenceTransformer("all-MiniLM-L6-v2")

# Load vector DB
client = chromadb.PersistentClient(path="./vector_store")

collection = client.get_collection("shl_assessments")

query = "Java developer with communication skills"

query_embedding = model.encode(query).tolist()

results = collection.query(
    query_embeddings=[query_embedding],
    n_results=5
)

print("\nTop Matching Assessments:\n")

for meta in results["metadatas"][0]:
    print(meta["name"])
    print(meta["url"])
    print()