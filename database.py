from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct,
    Filter, FieldCondition, MatchValue
)
import uuid
import openai

client = QdrantClient("http://localhost:6333")

# Create collection
client.recreate_collection(
    collection_name="Bs_docs",
    vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
)

# Insert vectors (in production, use batch mode)
import openai

client = openai.OpenAI(
    api_key=os.environ["OPENAI_API_KEY"],
    base_url="https://aipipe.org/openai/v1",
)


texts = [
    "Qdrant is written in Rust for high performance.",
    "Vector databases power semantic search in RAG.",
    "Cosine similarity measures angle between vectors.",
]

embeddings = client.embeddings.create(
    input=texts, model="text-embedding-3-small"
).data

points = [
    PointStruct(
        id=str(uuid.uuid4()),
        vector=e.embedding,
        payload={"text": t, "week": 4}
    )
    for t, e in zip(texts, embeddings)
]

client.upsert(collection_name="bs_docs", points=points)

# Search with payload filter
'''query_embedding = client.embeddings.create(
    input=["what is qdrant?"], model="text-embedding-3-small"
).data[0].embedding

results = client.search(
    collection_name="bs_docs",
    query_vector=query_embedding,
    limit=3,
    query_filter=Filter(
        must=[FieldCondition(key="week", match=MatchValue(value=4))]
    )
)

for r in results:
    print(f"Score: {r.score:.3f} | {r.payload['text']}")'''