import faiss
import numpy as np
from embeddings import create_embeddings
from documents import documents

# Create embeddings
doc_embeddings = create_embeddings(documents)

dimension = doc_embeddings.shape[1]

index = faiss.IndexFlatL2(dimension)

index.add(np.array(doc_embeddings))

def search(query_embedding, k=3):
    distances, indices = index.search(query_embedding, k)
    return indices