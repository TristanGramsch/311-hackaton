"""Semantic search over the Boston 311 knowledge base."""

import os
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

CHROMA_DIR = os.path.join(os.path.dirname(__file__), "chroma_store")
COLLECTION_NAME = "boston_311_kb"
MODEL_NAME = "all-MiniLM-L6-v2"


def get_collection():
    ef = SentenceTransformerEmbeddingFunction(model_name=MODEL_NAME)
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    return client.get_collection(name=COLLECTION_NAME, embedding_function=ef)


def search(query: str, n_results: int = 5) -> list[dict]:
    """Search the knowledge base. Returns list of {text, source, distance}."""
    collection = get_collection()
    results = collection.query(query_texts=[query], n_results=n_results)
    output = []
    for i in range(len(results["documents"][0])):
        output.append(
            {
                "text": results["documents"][0][i],
                "source": results["metadatas"][0][i]["source"],
                "distance": results["distances"][0][i],
            }
        )
    return output


if __name__ == "__main__":
    import sys

    q = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "How do I report a pothole?"
    print(f"Query: {q}\n")
    for i, result in enumerate(search(q), 1):
        print(
            f"--- Result {i} (distance: {result['distance']:.4f}, source: {result['source']}) ---"
        )
        print(result["text"][:300])
        print()
