import os
import chromadb
from chromadb.utils import embedding_functions

INDEX_PATH = os.getenv("INDEX_PATH", "./data/index")
EMBED_MODEL = os.getenv("EMBED_MODEL", "all-MiniLM-L6-v2")

# Use the same embedding function that built the collection to avoid Chroma errors
emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=EMBED_MODEL)
client = chromadb.PersistentClient(path=INDEX_PATH)
col = client.get_or_create_collection("amazon2020", embedding_function=emb_fn)


def normalize_filters(filters: dict | None) -> dict:
    """Convert simple dicts into Chroma's expected $and format when needed."""
    if not filters:
        return {}
    # If already using an operator, pass through
    if len(filters) == 1 and next(iter(filters)).startswith("$"):
        return filters

    clauses = []
    for key, value in filters.items():
        if key.startswith("$"):
            return filters
        clauses.append({key: value})

    if len(clauses) == 1:
        return clauses[0]
    return {"$and": clauses}

def rag_search(query, top_k=5, filters=None):
    where = normalize_filters(filters)
    res = col.query(query_texts=[query], n_results=top_k, where=where)
    out = []
    if not res["ids"] or not res["ids"][0]:
        return out
    for i in range(len(res["ids"][0])):
        meta = res["metadatas"][0][i] or {}
        out.append({
            "doc_id": res["ids"][0][i],
            "sku": meta.get("sku"),
            "title": res["documents"][0][i][:220],
            "price": meta.get("price"),
            "rating": meta.get("rating"),
            "brand": meta.get("brand"),
            "ingredients": meta.get("ingredients"),
        })
    return out
