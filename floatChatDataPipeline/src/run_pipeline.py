import os
import hashlib
import logging
import faiss
from sentence_transformers import SentenceTransformer
from src import config
from src import db_utils
from src.data_processor import DataProcessor

# --- Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
DATA_DIR = 'NetCDFDatafile'

def get_file_hash(file_path: str) -> str:
    """Calculates the MD5 hash of a file for tracking changes."""
    hasher = hashlib.md5()
    with open(file_path, 'rb') as f:
        buf = f.read()
        hasher.update(buf)
    return hasher.hexdigest()

def main():
    """The main function to run the entire data pipeline."""
    logging.info("--- Starting Data Pipeline Run ---")

    # --- 1. Initialization Phase ---
    logging.info("Initializing databases, model, and Faiss index...")
    try:
        pg_engine = db_utils.get_postgres_engine()
        db_utils.init_postgres_db(pg_engine)
        chroma_client = db_utils.get_chroma_client()
        chroma_collection = db_utils.get_or_create_chroma_collection(chroma_client)

        embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        dimension = embedding_model.get_sentence_embedding_dimension()
        faiss_index_path = 'output/faiss_index.bin'
        
        if os.path.exists(faiss_index_path):
            logging.info(f"Loading existing Faiss index from {faiss_index_path}")
            faiss_index = faiss.read_index(faiss_index_path)
        else:
            logging.info("Creating new Faiss index.")
            # Use IndexIDMap to map Faiss's internal IDs to our PostgreSQL IDs
            index = faiss.IndexFlatL2(dimension)
            faiss_index = faiss.IndexIDMap(index)

    except Exception as e:
        logging.critical(f"Failed to initialize. Aborting pipeline. Error: {e}")
        return

    # --- 2. File Discovery Phase ---
    logging.info(f"Scanning for .nc files in '{DATA_DIR}'...")
    try:
        all_files = [f for f in os.listdir(DATA_DIR) if f.endswith('.nc')]
    except FileNotFoundError:
        logging.error(f"Data directory '{DATA_DIR}' not found. Aborting.")
        return
        
    with db_utils.get_session(pg_engine) as session:
        processed_files = db_utils.get_processed_files(session)
    files_to_process = [f for f in all_files if f not in processed_files]
    logging.info(f"Found {len(all_files)} total files. {len(files_to_process)} are new.")

    if not files_to_process:
        logging.info("No new files to process. Pipeline run complete.")
        return

    # --- 3. Processing Phase ---
    with db_utils.get_session(pg_engine) as session:
        processor = DataProcessor(session, chroma_collection, embedding_model, faiss_index)

        for filename in files_to_process:
            file_path = os.path.join(DATA_DIR, filename)
            logging.info(f"--- Processing file: {filename} ---")
            
            file_hash = get_file_hash(file_path)
            try:
                db_utils.update_file_status(session, filename, file_hash, 'in_progress')
                session.commit()
                processor.process_file(file_path)
                db_utils.update_file_status(session, filename, file_hash, 'success')
            except Exception as e:
                logging.error(f"An error occurred while processing {filename}: {e}")
                db_utils.update_file_status(session, filename, file_hash, 'failed')
            finally:
                session.commit()

    # --- 4. Finalization Phase ---
    try:
        logging.info(f"Saving Faiss index with {faiss_index.ntotal} vectors to {faiss_index_path}...")
        faiss.write_index(faiss_index, faiss_index_path)
        logging.info("Faiss index saved successfully.")
    except Exception as e:
        logging.error(f"Failed to save Faiss index: {e}")

    logging.info("--- Data Pipeline Run Finished ---")

if __name__ == "__main__":
    main()