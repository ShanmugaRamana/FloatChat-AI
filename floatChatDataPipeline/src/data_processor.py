import logging
import numpy as np
import pandas as pd
import xarray as xr
import faiss
from sqlalchemy.orm import Session
from sentence_transformers import SentenceTransformer
from src import db_utils

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DataProcessor:
    """
    Processes NetCDF files and loads data into PostgreSQL, ChromaDB, and Faiss.
    """
    def __init__(self, pg_session: Session, chroma_collection, embedding_model, faiss_index):
        self.pg_session = pg_session
        self.chroma_collection = chroma_collection
        self.embedding_model = embedding_model
        self.faiss_index = faiss_index
        logging.info("DataProcessor initialized for PG, Chroma, and Faiss.")

    def _extract_data_from_nc(self, file_path: str) -> pd.DataFrame:
        """Opens a NetCDF file and returns a cleaned pandas DataFrame."""
        logging.info(f"Extracting data from {file_path}")
        with xr.open_dataset(file_path) as ds:
            df = ds.to_dataframe()
            valid_vars = [var for var in ['PSAL', 'TEMP'] if var in df.columns]
            if valid_vars:
                df.dropna(subset=valid_vars, inplace=True)
            df.reset_index(inplace=True)
            float_id = ds.attrs.get('platform_id') or ds.attrs.get('wmo_id')
            df['float_wmo_id'] = float_id
            logging.info(f"Found {len(df)} valid data points in the file.")
            return df

    def _generate_summary(self, row: pd.Series) -> str:
        """Generates a human-readable text summary for a single data point."""
        summary_parts = [
            f"Data point from {row.get('time').strftime('%Y-%m-%d')}",
            f"at location ({row.get('latitude'):.2f}, {row.get('longitude'):.2f})."
        ]
        if row.get('float_wmo_id'):
            summary_parts.insert(1, f"float {row.get('float_wmo_id')}")
        if 'PSAL' in row and pd.notna(row['PSAL']):
            summary_parts.append(f"Practical salinity was {row.get('PSAL'):.2f} PSS-78.")
        if 'TEMP' in row and pd.notna(row['TEMP']):
            summary_parts.append(f"Sea temperature was {row.get('TEMP'):.2f} degrees Celsius.")
        return " ".join(summary_parts)

    def process_file(self, file_path: str):
        """Orchestrates the processing of a single NetCDF file using batching."""
        try:
            df = self._extract_data_from_nc(file_path)
            if df.empty:
                return

            batch_size = 2048
            num_batches = (len(df) // batch_size) + 1
            logging.info(f"Processing {len(df)} points in {num_batches} batches...")

            for i in range(0, len(df), batch_size):
                batch_df = df.iloc[i:i + batch_size]
                
                # 1. Prepare data for PostgreSQL
                profiles_to_insert = []
                for _, row in batch_df.iterrows():
                    profiles_to_insert.append({
                        "float_wmo_id": row.get('float_wmo_id'),
                        "timestamp": row.get('time'),
                        "latitude": row.get('latitude'),
                        "longitude": row.get('longitude'),
                        "measurements": row.drop(['time', 'latitude', 'longitude', 'float_wmo_id'], errors='ignore').to_dict()
                    })
                
                # 2. Insert into PostgreSQL and get real IDs
                inserted_ids = db_utils.insert_profiles_batch(self.pg_session, profiles_to_insert)
                # NEW LOGGING: Confirm PostgreSQL insertion
                logging.info(f"  -> Batch {i//batch_size + 1}/{num_batches}: Saved {len(inserted_ids)} records to PostgreSQL.")
                
                if not inserted_ids:
                    logging.warning(f"  - Batch {i//batch_size + 1}/{num_batches} had no new records to insert.")
                    continue

                # 3. Generate Summaries and Embeddings
                summaries = [self._generate_summary(row) for _, row in batch_df.iterrows()]
                embeddings = self.embedding_model.encode(summaries, show_progress_bar=False)
                
                # 4. Add to ChromaDB
                metadatas = [{"postgres_id": pid} for pid in inserted_ids]
                self.chroma_collection.add(
                    ids=[str(pid) for pid in inserted_ids],
                    embeddings=embeddings.tolist(),
                    metadatas=metadatas
                )
                
                # 5. Add to Faiss
                ids_to_add = np.array(inserted_ids, dtype=np.int64)
                self.faiss_index.add_with_ids(embeddings, ids_to_add)
                # NEW LOGGING: Confirm Faiss insertion
                logging.info(f"  -> Batch {i//batch_size + 1}/{num_batches}: Added {len(ids_to_add)} vectors to Faiss.")

            logging.info(f"Successfully processed {len(df)} points from {file_path}.")

        except Exception as e:
            logging.error(f"Failed to process file {file_path}: {e}")
            raise