import numpy as np
import ollama
from embeddings import create_embeddings
from vector import search
from documents import documents

def rag_search(query):

    query_embedding = create_embeddings([query])

    indices = search(np.array(query_embedding))

    retrieved_docs = [documents[i] for i in indices[0]]

    context = "\n".join(retrieved_docs)

    prompt = f"""
Context:
{context}

Question:
{query}

Answer the question using the context.
"""

    response = ollama.chat(
        model="mistral",
        messages=[{"role":"user","content":prompt}]
    )

    return response["message"]["content"]