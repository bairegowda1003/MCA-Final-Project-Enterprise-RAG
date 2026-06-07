import chromadb
from chromadb.utils import embedding_functions
import os

CHROMA_PATH = os.path.join(os.path.dirname(__file__), "..", "chroma_db")

sentence_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

client = chromadb.PersistentClient(path=CHROMA_PATH)
collection = client.get_or_create_collection(
    name="enterprise_rag",
    embedding_function=sentence_ef,
    metadata={"hnsw:space": "cosine"}
)


def add_chunks(document_id: str, filename: str, chunks: list[dict]):
    ids = [f"{document_id}_chunk_{i}" for i in range(len(chunks))]
    texts = [c["text"] for c in chunks]
    metadatas = [
        {"document_id": document_id, "filename": filename, "page_number": c["page_number"]}
        for c in chunks
    ]
    collection.add(ids=ids, documents=texts, metadatas=metadatas)


def query_chunks(query: str, n_results: int = 20) -> list[dict]:
    results = collection.query(query_texts=[query], n_results=n_results)
    chunks = []
    for i, doc in enumerate(results["documents"][0]):
        chunks.append({
            "text": doc,
            "metadata": results["metadatas"][0][i],
            "distance": results["distances"][0][i],
        })
    return chunks


def delete_document(document_id: str):
    existing = collection.get(where={"document_id": document_id})
    if existing["ids"]:
        collection.delete(ids=existing["ids"])


def list_documents() -> list[dict]:
    all_data = collection.get()
    seen = {}
    for meta in all_data["metadatas"]:
        did = meta["document_id"]
        if did not in seen:
            seen[did] = {"document_id": did, "filename": meta["filename"]}
    return list(seen.values())


def get_total_chunks() -> int:
    return collection.count()
