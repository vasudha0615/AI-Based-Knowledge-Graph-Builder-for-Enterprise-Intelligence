from rag_pipeline import rag_search

query = input("Enter your question: ")

answer = rag_search(query)

print("\nGenerated Answer:\n")
print(answer)