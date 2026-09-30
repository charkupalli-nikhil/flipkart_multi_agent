"""
Flipkart Sales Intelligence System - RAG Tools
Provides functions for retrieving unstructured knowledge from documents.
"""

import os
from typing import Dict, Any, List

def query_knowledge_base(query: str, top_k: int = 2) -> Dict[str, Any]:
    """
    Queries the unstructured knowledge base (e.g., return policies, discount rules).
    """
    try:
        import chromadb
        from sentence_transformers import SentenceTransformer
    except ImportError:
        return {"error": "chromadb or sentence-transformers not installed. Run pip install chromadb sentence-transformers"}

    kb_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "knowledge_base.txt")
    if not os.path.exists(kb_path):
        return {"error": "knowledge_base.txt not found."}

    # Simple in-memory client for demonstration purposes
    client = chromadb.Client()
    collection_name = "flipkart_kb"
    
    # Check if we already created it in this session
    try:
        collection = client.get_collection(name=collection_name)
    except Exception:
        # Create it if it doesn't exist
        collection = client.create_collection(name=collection_name)
        
        # Load and chunk the document
        with open(kb_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Simple splitting by sections
        sections = [s.strip() for s in content.split("##") if s.strip()]
        
        # Load embedding model
        model = SentenceTransformer("all-MiniLM-L6-v2")
        
        embeddings = model.encode(sections).tolist()
        ids = [f"doc_{i}" for i in range(len(sections))]
        
        collection.add(
            documents=sections,
            embeddings=embeddings,
            ids=ids
        )
        
    # Query the collection
    model = SentenceTransformer("all-MiniLM-L6-v2")
    query_embedding = model.encode([query]).tolist()
    
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=min(top_k, collection.count())
    )
    
    retrieved_docs = results["documents"][0] if results["documents"] else []
    
    return {
        "query": query,
        "retrieved_information": retrieved_docs
    }
