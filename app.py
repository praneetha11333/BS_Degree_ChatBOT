import os
import openai
import streamlit as st
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from rank_bm25 import BM25Okapi
from semantic_cache import SemanticCache

load_dotenv()

oai = openai.OpenAI(
    api_key=os.environ["AIPIPE_API_KEY"],
    base_url="https://aipipe.org/openai/v1",
)
client = QdrantClient("http://localhost:6333")

@st.cache_resource
def load_index():
    points = client.scroll(collection_name="BS-DOCS", with_payload=True, limit=10000)[0]
    texts = [p.payload["text"] for p in points]
    ids = [str(p.id) for p in points]
    bm25 = BM25Okapi([t.lower().split() for t in texts])
    id_to_text = {pid: text for pid, text in zip(ids, texts)}
    return bm25, ids, id_to_text

def retrieve(query, q_emb, k=5):
    bm25, ids, id_to_text = load_index()

    dense_ids = [str(r.id) for r in client.query_points(collection_name="BS-DOCS", query=q_emb, limit=k * 2).points]

    scores = bm25.get_scores(query.lower().split())
    sparse_ids = [ids[i] for i in sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k * 2]]

    fused = {}
    for rank, did in enumerate(dense_ids):
        fused[did] = fused.get(did, 0) + 1 / (60 + rank)
    for rank, did in enumerate(sparse_ids):
        fused[did] = fused.get(did, 0) + 1 / (60 + rank)

    top_ids = sorted(fused, key=fused.get, reverse=True)[:k]
    return [id_to_text[did] for did in top_ids if did in id_to_text]

def answer(query, contexts):
    context_text = "\n\n".join(contexts)
    resp = oai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant for the IITM BS Degree programme. Answer only based on the provided context."},
            {"role": "user", "content": f"Context:\n{context_text}\n\nQuestion: {query}"},
        ],
    )
    return resp.choices[0].message.content

cache = SemanticCache()

st.title("BS Degree Query Engine")
st.write("Ask me anything about the BS degree!")

ask = st.text_input("Enter your question here:")
if st.button("Submit") and ask:
    q_emb = oai.embeddings.create(input=ask, model="text-embedding-3-small").data[0].embedding
    cached = cache.get(q_emb)
    if cached:
        st.markdown(cached)
        st.caption("⚡ answered from cache")
    else:
        with st.spinner("Retrieving..."):
            contexts = retrieve(ask, q_emb)
        with st.spinner("Generating answer..."):
            response = answer(ask, contexts)
        cache.set(ask, response, q_emb)
        st.markdown(response)
      