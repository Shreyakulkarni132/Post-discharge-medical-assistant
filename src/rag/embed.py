import os
import PyPDF2
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
from langchain.schema import Document

def load_pdf_text(file_path):
    text = ""
    with open(file_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            text += page.extract_text() + "\n"
    return text

pdf_path = r"C:\Users\shrey\OneDrive\Desktop\Projects\AI_medical_assistant\comprehensive-clinical-nephrology.pdf"

print("Loading PDF...")
pdf_text = load_pdf_text(pdf_path)

# Wrap text in a Document object
documents = [Document(page_content=pdf_text)]

print("Splitting into chunks...")
splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
docs = splitter.split_documents(documents)

print("Generating embeddings...")
embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

persist_directory = "rag_db"
print("Saving embeddings to ChromaDB...")
vectorstore = Chroma.from_documents(docs, embedding_model, persist_directory=persist_directory)
vectorstore.persist()

print("Embedding and storage complete.")
