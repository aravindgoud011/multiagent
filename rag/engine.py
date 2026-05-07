import os
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_openai import AzureOpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from pinecone import Pinecone
from langchain_pinecone import PineconeVectorStore

load_dotenv()

class RAGEngine:
    def __init__(self):
        print("Initializing Embeddings...")
        if os.getenv("AZURE_OPENAI_API_KEY"):
            print("Using Azure OpenAI Embeddings...")
            self.embeddings = AzureOpenAIEmbeddings(
                azure_deployment=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-3-small"), 
                api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview"),
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                api_key=os.getenv("AZURE_OPENAI_API_KEY")
            )
        else:
            print("Using Gemini Embeddings...")
            self.embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
        
        # Load local FAISS index
        faiss_path = os.path.join(os.path.dirname(__file__), "faiss_index")
        print(f"Loading FAISS from {faiss_path}...")
        if os.path.exists(faiss_path):
            self.local_index = FAISS.load_local(
                faiss_path, 
                self.embeddings, 
                allow_dangerous_deserialization=True
            )
        else:
            self.local_index = None

        # Initialize Pinecone
        print("Initializing Pinecone...")
        try:
            self.pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
            self.index_name = os.getenv("PINECONE_INDEX_NAME")
            print(f"Connecting to Pinecone index: {self.index_name}...")
            self.cloud_index = PineconeVectorStore.from_existing_index(
                index_name=self.index_name,
                embedding=self.embeddings
            )
            print("Pinecone connected.")
        except Exception as e:
            print(f"Pinecone initialization failed: {e}")
            self.cloud_index = None

    def search(self, query, k=5):
        """
        Hybrid-ish search: Combines local FAISS and cloud Pinecone results.
        """
        results = []
        
        # 1. Local search
        if self.local_index:
            local_results = self.local_index.similarity_search(query, k=k)
            results.extend(local_results)

        # 2. Cloud search
        if self.cloud_index:
            cloud_results = self.cloud_index.similarity_search(query, k=k)
            results.extend(cloud_results)

        # Simple deduplication by content
        seen = set()
        unique_results = []
        for doc in results:
            if doc.page_content not in seen:
                unique_results.append(doc)
                seen.add(doc.page_content)

        return unique_results[:k]

# Singleton
rag_engine = RAGEngine()
