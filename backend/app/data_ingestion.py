"""
Data ingestion and preprocessing.
Loads documents from resources/data/ and prepares them for RAG + SQL queries.

This module handles:
1. Loading MD files from 5 departments
2. Splitting text with LangChain
3. Creating embeddings
4. Storing in ChromaDB with RBAC metadata
5. Loading hr_data.csv into SQLite
"""
import os
import sys
from pathlib import Path
from typing import List, Dict, Any
import pandas as pd

from langchain_community.document_loaders import DirectoryLoader, UnstructuredMarkdownLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
import chromadb
from sqlalchemy import create_engine, text
from tqdm import tqdm

from config import settings
from logger import log_info, log_error, setup_logging

# Setup logging for ingestion
setup_logging(
    service_name="data-ingestion",
    environment="development",
    log_level="INFO"
)


class DataIngestion:
    """Handles all data ingestion and preprocessing."""
    
    def __init__(self):
        self.resources_path = Path("resources/data")
        self.departments = ["engineering", "finance", "general", "hr", "marketing"]
        
        # Initialize ChromaDB
        self.chroma_client = chromadb.PersistentClient(path=settings.CHROMADB_PATH)
        self.collection = self.chroma_client.get_or_create_collection(
            name="documents",
            metadata={"hnsw:space": "cosine"}
        )
        
        # Initialize embeddings model
        log_info("Loading embedding model", model=settings.EMBEDDING_MODEL)
        self.embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        log_info("Data ingestion initialized")
    
    def load_markdown_documents(self, department: str) -> List[Dict[str, Any]]:
        """
        Load all markdown files from a department folder.
        
        Args:
            department: Department name (engineering, finance, etc.)
            
        Returns:
            List of document dicts with content and metadata
        """
        dept_path = self.resources_path / department
        
        if not dept_path.exists():
            log_error(f"Department folder not found: {dept_path}")
            return []
        
        log_info(f"Loading documents from {department}", path=str(dept_path))
        
        # Use LangChain DirectoryLoader for MD files
        loader = DirectoryLoader(
            str(dept_path),
            glob="**/*.md",
            loader_cls=UnstructuredMarkdownLoader,
            show_progress=True,
            use_multithreading=True,
        )
        
        try:
            documents = loader.load()
            log_info(
                f"Loaded {len(documents)} documents from {department}",
                count=len(documents)
            )
            return documents
        
        except Exception as e:
            log_error(
                f"Failed to load documents from {department}",
                exc_info=True,
                department=department
            )
            return []
    
    def split_documents(self, documents: List[Any]) -> List[Dict[str, Any]]:
        """
        Split documents into chunks using LangChain splitter.
        
        Args:
            documents: List of LangChain Document objects
            
        Returns:
            List of chunk dicts with content and metadata
        """
        log_info("Splitting documents into chunks")
        
        all_chunks = []
        
        for doc in tqdm(documents, desc="Splitting"):
            # Split using RecursiveCharacterTextSplitter
            chunks = self.text_splitter.split_documents([doc])
            
            for idx, chunk in enumerate(chunks):
                all_chunks.append({
                    "content": chunk.page_content,
                    "metadata": {
                        **chunk.metadata,
                        "chunk_id": f"{doc.metadata.get('source', 'unknown')}_{idx}",
                    }
                })
        
        log_info(f"Created {len(all_chunks)} chunks", total_chunks=len(all_chunks))
        return all_chunks
    
    def add_rbac_metadata(
        self,
        chunks: List[Dict[str, Any]],
        department: str
    ) -> List[Dict[str, Any]]:
        """
        Add RBAC metadata to chunks.
        
        Args:
            chunks: List of chunk dicts
            department: Department name
            
        Returns:
            Chunks with RBAC metadata added
        """
        for chunk in chunks:
            chunk["metadata"]["department"] = department
            
            # Extract filename from source
            source = chunk["metadata"].get("source", "")
            chunk["metadata"]["filename"] = Path(source).name
        
        return chunks
    
    def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Create embeddings using sentence-transformers.
        
        Args:
            texts: List of text strings
            
        Returns:
            List of embedding vectors
        """
        log_info(f"Creating embeddings for {len(texts)} texts")
        
        # Batch encoding for efficiency
        embeddings = self.embedding_model.encode(
            texts,
            batch_size=32,
            show_progress_bar=True,
            convert_to_numpy=True
        )
        
        return embeddings.tolist()
    
    def store_in_chromadb(self, chunks: List[Dict[str, Any]]) -> None:
        """
        Store chunks in ChromaDB with embeddings.
        
        Args:
            chunks: List of chunk dicts with content and metadata
        """
        if not chunks:
            log_error("No chunks to store")
            return
        
        log_info(f"Storing {len(chunks)} chunks in ChromaDB")
        
        # Extract texts for embedding
        texts = [chunk["content"] for chunk in chunks]
        
        # Create embeddings
        embeddings = self.create_embeddings(texts)
        
        # Generate IDs
        ids = [chunk["metadata"]["chunk_id"] for chunk in chunks]
        
        # Extract metadata
        metadatas = [chunk["metadata"] for chunk in chunks]
        
        # Add to ChromaDB
        try:
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas
            )
            log_info("Successfully stored in ChromaDB", count=len(chunks))
        
        except Exception as e:
            log_error("Failed to store in ChromaDB", exc_info=True)
            raise
    
    def ingest_department(self, department: str) -> None:
        """
        Complete ingestion pipeline for one department.
        
        Args:
            department: Department name
        """
        log_info(f"Starting ingestion for {department}")
        
        # Step 1: Load MD files
        documents = self.load_markdown_documents(department)
        
        if not documents:
            log_error(f"No documents found for {department}")
            return
        
        # Step 2: Split into chunks
        chunks = self.split_documents(documents)
        
        # Step 3: Add RBAC metadata
        chunks = self.add_rbac_metadata(chunks, department)
        
        # Step 4: Store in ChromaDB
        self.store_in_chromadb(chunks)
        
        log_info(f"Completed ingestion for {department}")
    
    def ingest_all_departments(self) -> None:
        """Ingest documents from all departments."""
        log_info("Starting ingestion for all departments")
        
        for dept in self.departments:
            self.ingest_department(dept)
        
        # Get collection stats
        total_docs = self.collection.count()
        log_info(
            "Completed ingestion for all departments",
            total_documents=total_docs
        )
    
    def load_hr_data_csv(self) -> None:
        """
        Load hr_data.csv into SQLite database.
        Creates employees table with structured data.
        """
        log_info("Loading hr_data.csv into SQLite")
        
        csv_path = self.resources_path / "hr" / "hr_data.csv"
        
        if not csv_path.exists():
            log_error(f"hr_data.csv not found at {csv_path}")
            return
        
        try:
            # Read CSV
            df = pd.read_csv(csv_path)
            log_info(f"Loaded CSV with {len(df)} rows", rows=len(df))
            
            # Create SQLite connection
            engine = create_engine(settings.DATABASE_URL.replace("aiosqlite", "sqlite"))
            
            # Load into SQLite
            df.to_sql(
                "employees",
                engine,
                if_exists="replace",
                index=False
            )
            
            log_info("Successfully loaded hr_data.csv into SQLite")
            
            # Verify
            with engine.connect() as conn:
                result = conn.execute(text("SELECT COUNT(*) FROM employees"))
                count = result.scalar()
                log_info(f"Verified {count} employees in database", count=count)
        
        except Exception as e:
            log_error("Failed to load hr_data.csv", exc_info=True)
            raise
    
    def run_full_ingestion(self) -> None:
        """Run complete data ingestion pipeline."""
        log_info("=" * 60)
        log_info("STARTING FULL DATA INGESTION")
        log_info("=" * 60)
        
        try:
            # Step 1: Ingest all markdown documents
            self.ingest_all_departments()
            
            # Step 2: Load CSV data
            self.load_hr_data_csv()
            
            log_info("=" * 60)
            log_info("DATA INGESTION COMPLETED SUCCESSFULLY")
            log_info("=" * 60)
        
        except Exception as e:
            log_error("Data ingestion failed", exc_info=True)
            sys.exit(1)
    
    def reset_data(self) -> None:
        """Reset all data (ChromaDB + SQLite). Use with caution!"""
        log_info("RESETTING ALL DATA")
        
        # Delete ChromaDB collection
        try:
            self.chroma_client.delete_collection("documents")
            log_info("Deleted ChromaDB collection")
        except Exception as e:
            log_error("Failed to delete ChromaDB collection", error=str(e))
        
        # Delete SQLite database
        db_path = Path("data/app.db")
        if db_path.exists():
            db_path.unlink()
            log_info("Deleted SQLite database")
        
        log_info("Data reset complete")


def main():
    """Main entry point for data ingestion."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Data ingestion for RBAC Chatbot")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset all data before ingestion"
    )
    parser.add_argument(
        "--department",
        type=str,
        help="Ingest only specific department"
    )
    
    args = parser.parse_args()
    
    ingestion = DataIngestion()
    
    if args.reset:
        log_info("Reset flag detected")
        ingestion.reset_data()
    
    if args.department:
        log_info(f"Ingesting single department: {args.department}")
        ingestion.ingest_department(args.department)
    else:
        ingestion.run_full_ingestion()


if __name__ == "__main__":
    main()
