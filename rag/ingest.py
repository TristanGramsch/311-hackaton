"""Ingest static knowledge base docs into ChromaDB for semantic search."""

import os
import re
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

STATIC_DIR = os.path.join(os.path.dirname(__file__), "..", "knowledge-base", "static")
CHROMA_DIR = os.path.join(os.path.dirname(__file__), "chroma_store")
COLLECTION_NAME = "boston_311_kb"
MODEL_NAME = "all-MiniLM-L6-v2"
CHUNK_MAX_CHARS = 500
CHUNK_OVERLAP_CHARS = 50


def chunk_by_headers(text: str, source: str) -> list[dict]:
    """Split markdown by h2/h3 headers, then by paragraph if still too long."""
    sections = re.split(r"(?=^#{2,3} )", text, flags=re.MULTILINE)
    chunks = []
    for section in sections:
        section = section.strip()
        if not section:
            continue
        if len(section) <= CHUNK_MAX_CHARS:
            chunks.append({"text": section, "source": source})
        else:
            # Split by double newline (paragraphs)
            paragraphs = re.split(r"\n\n+", section)
            buffer = ""
            for para in paragraphs:
                para = para.strip()
                if not para:
                    continue
                if len(buffer) + len(para) + 2 <= CHUNK_MAX_CHARS:
                    buffer = f"{buffer}\n\n{para}" if buffer else para
                else:
                    if buffer:
                        chunks.append({"text": buffer, "source": source})
                    # If single paragraph exceeds max, split by sentences
                    if len(para) > CHUNK_MAX_CHARS:
                        sentences = re.split(r"(?<=[.!?])\s+", para)
                        sent_buf = ""
                        for sent in sentences:
                            if len(sent_buf) + len(sent) + 1 <= CHUNK_MAX_CHARS:
                                sent_buf = f"{sent_buf} {sent}" if sent_buf else sent
                            else:
                                if sent_buf:
                                    chunks.append({"text": sent_buf, "source": source})
                                sent_buf = sent
                        if sent_buf:
                            buffer = sent_buf
                        else:
                            buffer = ""
                    else:
                        buffer = para
            if buffer:
                chunks.append({"text": buffer, "source": source})
    return chunks


def ingest():
    ef = SentenceTransformerEmbeddingFunction(model_name=MODEL_NAME)
    client = chromadb.PersistentClient(path=CHROMA_DIR)

    # Delete existing collection if present
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"},
    )

    all_chunks = []
    for filename in sorted(os.listdir(STATIC_DIR)):
        if not filename.endswith(".md"):
            continue
        filepath = os.path.join(STATIC_DIR, filename)
        with open(filepath, "r") as f:
            text = f.read()
        chunks = chunk_by_headers(text, source=filename)
        all_chunks.extend(chunks)
        print(f"  {filename}: {len(chunks)} chunks")

    if not all_chunks:
        print("No chunks to ingest.")
        return

    # Add to ChromaDB in batches
    batch_size = 100
    for i in range(0, len(all_chunks), batch_size):
        batch = all_chunks[i : i + batch_size]
        collection.add(
            ids=[f"chunk_{i + j}" for j in range(len(batch))],
            documents=[c["text"] for c in batch],
            metadatas=[{"source": c["source"]} for c in batch],
        )

    print(
        f"\nIngested {len(all_chunks)} chunks into ChromaDB collection '{COLLECTION_NAME}'"
    )


if __name__ == "__main__":
    ingest()
