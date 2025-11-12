import sys
import os
from crewai_tools import BaseTool
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(parent_dir)
from patient_data.database_tool import PatientDatabaseRetrievalTool
import requests
import json
from pydantic import Field
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
from pydantic import PrivateAttr

class WebSearchTool(BaseTool):
    name: str = "Web Search Tool"
    description: str = (
        "Performs web search queries via SerpAPI for clinical or general questions. "
        "Indicates that the information is from a web search."
    )

    api_key: str = Field(default=None, description="SerpAPI key for authentication")
    endpoint: str = Field(default="https://serpapi.com/search.json")

    def _run(self, query: str) -> str:
        """Perform a web search using SerpAPI."""
        try:
            params = {
                "q": query,
                "api_key": self.api_key,
                "num": 5
            }
            response = requests.get(self.endpoint, params=params)
            data = response.json()

            if "error" in data:
                return json.dumps({"status": "error", "message": data["error"]}, indent=2)

            results = [
                {
                    "title": item.get("title"),
                    "link": item.get("link"),
                    "snippet": item.get("snippet")
                }
                for item in data.get("organic_results", [])[:5]
            ]

            return json.dumps({
                "status": "success",
                "source": "web_search",
                "query": query,
                "results": results,
                "note": "Information fetched via SerpAPI web search"
            }, indent=2)

        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Web search failed: {str(e)}"
            }, indent=2)

serp_api_key = os.getenv("SERP_API_KEY", "")



class KnowledgeBaseTool(BaseTool):
    name: str = "RAG Knowledge Base Tool"
    description: str = (
        "Queries the hospital's document knowledge base (vector DB) "
        "to retrieve relevant information for patient care and clinical queries."
    )

    top_k: int = Field(default=3, description="Number of top results to return")

    _db: Chroma = PrivateAttr()  # <-- declare as private

    def __init__(self):
        super().__init__()
        embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        persist_directory = "rag_db"
        self._db = Chroma(persist_directory=persist_directory, embedding_function=embedding_model)

    def _run(self, query_text: str) -> str:
        results = self._db.similarity_search(query_text, k=self.top_k)
        output = "\n\n".join([res.page_content[:500] for res in results])
        return output  


rag_tool = KnowledgeBaseTool()
database_tool = PatientDatabaseRetrievalTool()
web_search_tool = WebSearchTool(api_key=serp_api_key)



__all__ = ["database_tool", "web_search_tool", "rag_tool"]
