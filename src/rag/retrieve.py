from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma

persist_directory = "rag_db"
embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
db = Chroma(persist_directory=persist_directory, embedding_function=embedding_model)

def query_knowledge_base(query_text, top_k=3):
    print(f"Querying: {query_text}")
    results = db.similarity_search(query_text, k=top_k)
    return results
