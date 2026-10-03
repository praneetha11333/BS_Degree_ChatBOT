import os
import uuid
import openai
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from chunk_stratergy import chunk_source_by_section
from chunk_splitter import split_large_chunks

load_dotenv()

chunks = split_large_chunks(chunk_source_by_section("source1.txt"))

oai = openai.OpenAI(
    api_key=os.environ["AIPIPE_API_KEY"],
    base_url="https://aipipe.org/openai/v1",
)

client = QdrantClient("http://localhost:6333")

client.recreate_collection(
    collection_name="BS-DOCS",
    vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
)

points = []
for i, chunk in enumerate(chunks):
    parts = []
    if "content" in chunk:
        parts.append(chunk["content"])
    for table in chunk.get("tables", []):
        rows_text = "\n".join(
            ", ".join(f"{h}: {v}" for h, v in zip(table["headers"], row))
            for row in table["rows"]
        )
        parts.append(f"Headers: {', '.join(table['headers'])}\n{rows_text}")
    text = "\n\n".join(parts)

    emb = oai.embeddings.create(input=text, model="text-embedding-3-small").data[0].embedding
    points.append(PointStruct(
        id=str(uuid.uuid4()),
        vector=emb,
        payload={"text": text, "section": chunk["section"], "types": chunk["types"]},
    ))
    print(f"[{i+1}/{len(chunks)}] embedded: {chunk['section']}")

BATCH_SIZE = 100
for i in range(0, len(points), BATCH_SIZE):
    client.upsert(collection_name="BS-DOCS", points=points[i:i + BATCH_SIZE])
    print(f"Upserted {min(i + BATCH_SIZE, len(points))}/{len(points)}")
