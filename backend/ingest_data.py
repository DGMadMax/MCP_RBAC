"""
Data Ingestion Script - One-Time Document and HR Data Loading
Run this script once to ingest all documents and HR data into the database
"""

import asyncio
import pandas as pd
from pathlib import Path
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceInferenceAPIEmbeddings

from app.config import settings
from app.database import SessionLocal, engine
from app.models import Employee
from app.logger import get_logger

logger = get_logger(__name__)


async def ingest_documents():
    """
    Ingest all Markdown documents from data/ folders into ChromaDB
    One-time operation with idempotency check
    """
    logger.info("=" * 80)
    logger.info("Starting document ingestion...")
    logger.info("=" * 80)
    
    DATA_DIR = Path(settings.data_dir)
    
    if not DATA_DIR.exists():
        logger.error(f"Data directory not found: {DATA_DIR}")
        return
    
    # Initialize HuggingFace Inference API embeddings (NOT local!)
    logger.info("Initializing HuggingFace Inference API embeddings...")
    embeddings = HuggingFaceInferenceAPIEmbeddings(
        api_key=settings.huggingface_api_key,
        model_name=settings.embedding_model
    )
    
    # Initialize ChromaDB
    logger.info(f"Initializing ChromaDB at: {settings.chromadb_path}")
    vectorstore = Chroma(
        collection_name="rbac_documents",
        embedding_function=embeddings,
        persist_directory=settings.chromadb_path
    )
    
    # Check if already ingested (idempotency)
    existing_count = vectorstore._collection.count()
    if existing_count > 0:
        logger.warning(f"⚠️  ChromaDB already contains {existing_count} documents")
        logger.warning("Skipping ingestion to avoid duplicates.")
        logger.warning("To re-ingest, delete the chromadb/ folder and run again.")
        return
    
    # Text splitter
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap
    )
    
    total_chunks = 0
    total_files = 0
    
    # Process each department folder
    for dept_folder in DATA_DIR.iterdir():
        if not dept_folder.is_dir():
            continue
        
        department = dept_folder.name.lower()
        logger.info(f"\n📁 Processing department: {department}")
        logger.info("-" * 80)
        
        md_files = list(dept_folder.glob("*.md"))
        
        if not md_files:
            logger.warning(f"  No Markdown files found in {department}")
            continue
        
        for md_file in md_files:
            try:
                with open(md_file, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Split into chunks
                chunks = splitter.split_text(content)
                
                # Add to vectorstore with metadata
                vectorstore.add_texts(
                    texts=chunks,
                    metadatas=[
                        {
                            "department": department,
                            "file_path": str(md_file),
                            "file_name": md_file.name,
                            "chunk_id": i
                        }
                        for i in range(len(chunks))
                    ]
                )
                
                total_chunks += len(chunks)
                total_files += 1
                
                logger.info(f"  ✓ {md_file.name}: {len(chunks)} chunks")
                
            except Exception as e:
                logger.error(f"  ✗ Failed to process {md_file.name}: {str(e)}")
    
    logger.info("=" * 80)
    logger.info(f"✅ Document ingestion complete!")
    logger.info(f"   Total files processed: {total_files}")
    logger.info(f"   Total chunks created: {total_chunks}")
    logger.info("=" * 80)


def ingest_hr_data():
    """
    Load HR data from CSV into SQLite employees table
    One-time operation
    """
    logger.info("=" * 80)
    logger.info("Starting HR data ingestion...")
    logger.info("=" * 80)
    
    DATA_DIR = Path(settings.data_dir)
    hr_csv_path = DATA_DIR / "HR" / "hr_data.csv"
    
    if not hr_csv_path.exists():
        logger.error(f"HR CSV not found: {hr_csv_path}")
        return
    
    # Check if already loaded
    db = SessionLocal()
    existing_count = db.query(Employee).count()
    db.close()
    
    if existing_count > 0:
        logger.warning(f"⚠️  Database already contains {existing_count} employees")
        logger.warning("Skipping HR data ingestion to avoid duplicates.")
        return
    
    # Load CSV
    logger.info(f"Loading CSV from: {hr_csv_path}")
    df = pd.read_csv(hr_csv_path)
    
    # Convert date columns
    date_columns = ['date_of_birth', 'date_of_joining', 'last_review_date']
    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
    
    # Insert into database
    logger.info("Inserting employee records into database...")
    df.to_sql("employees", engine, if_exists="append", index=False)
    
    logger.info("=" * 80)
    logger.info(f"✅ HR data ingestion complete!")
    logger.info(f"   Total employees loaded: {len(df)}")
    logger.info("=" * 80)


async def main():
    """Main execution"""
    from app.database import init_database
    
    # Initialize database tables
    logger.info("Initializing database tables...")
    init_database()
    
    # Ingest documents
    await ingest_documents()
    
    # Ingest HR data
    ingest_hr_data()
    
    logger.info("\n✅ All data ingestion complete!")
    logger.info("You can now start the application.")


if __name__ == "__main__":
    asyncio.run(main())
