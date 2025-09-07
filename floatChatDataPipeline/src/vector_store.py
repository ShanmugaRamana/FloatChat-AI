import os
import json
import logging
import faiss
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer

app_logger = logging.getLogger('app_vector_store')
MODEL_NAME = 'all-MiniLM-L6-v2'

def rebuild_index(conn, config):
    app_logger.info("Starting FAISS index rebuild process...")
    try:
        # Step 1: Query for the high-level float metadata (same as before)
        profile_meta_query = """
            SELECT
                float_id,
                COUNT(profile_id) as num_profiles,
                MIN(profile_time) as min_date,
                MAX(profile_time) as max_date,
                MIN(latitude) as min_lat,
                MAX(latitude) as max_lat,
                MIN(longitude) as min_lon,
                MAX(longitude) as max_lon
            FROM profiles
            GROUP BY float_id
            ORDER BY float_id;
        """
        df_meta = pd.read_sql_query(profile_meta_query, conn)

        if df_meta.empty:
            app_logger.warning("No data found in 'profiles' table. Skipping index creation.")
            return

        app_logger.info(f"Found metadata for {len(df_meta)} unique floats.")

        # --- NEW LOGIC: GET THE UNIQUE DATA VARIABLES FOR EACH FLOAT ---
        app_logger.info("Discovering measured variables for each float...")
        all_float_variables = {}
        with conn.cursor() as cur:
            for float_id in df_meta['float_id']:
                # This query gets all unique keys from the JSONB column for a specific float
                data_keys_query = """
                    SELECT DISTINCT jsonb_object_keys(m.data)
                    FROM measurements m
                    JOIN profiles p ON m.profile_id = p.profile_id
                    WHERE p.float_id = %s;
                """
                cur.execute(data_keys_query, (int(float_id),))
                # Store the keys as a sorted list for consistency
                all_float_variables[float_id] = sorted([row[0] for row in cur.fetchall()])
        
        # Step 2: Generate the new, "smarter" text summaries
        def create_smart_summary(row):
            float_id = row['float_id']
            # Get the variable list we just queried
            variables = all_float_variables.get(float_id, [])
            variables_text = f"This dataset contains measurements for: {', '.join(variables)}." if variables else ""
            
            return (f"ARGO float WMO ID {float_id} has {row['num_profiles']} profiles. "
                    f"It operated from {row['min_date']:%Y-%m-%d} to {row['max_date']:%Y-%m-%d}. "
                    f"Its location ranges from latitude {row['min_lat']:.2f} to {row['max_lat']:.2f} "
                    f"and longitude {row['min_lon']:.2f} to {row['max_lon']:.2f}. "
                    f"{variables_text}")

        df_meta['summary'] = df_meta.apply(create_smart_summary, axis=1)
        summaries = df_meta['summary'].tolist()

        # Step 3: Create vector embeddings (same as before)
        app_logger.info(f"Loading sentence transformer model: '{MODEL_NAME}'")
        model = SentenceTransformer(MODEL_NAME)
        app_logger.info(f"Generating embeddings for {len(summaries)} summaries...")
        embeddings = model.encode(summaries, show_progress_bar=True)
        embeddings = np.array(embeddings).astype('float32')

        # Step 4: Build and save the FAISS index (same as before)
        dimension = embeddings.shape[1]
        index = faiss.IndexFlatL2(dimension)
        index.add(embeddings)
        output_dir = config['PATHS']['OUTPUT_DIR']
        faiss_index_path = config['PATHS']['FAISS_INDEX_PATH']
        os.makedirs(output_dir, exist_ok=True)
        faiss.write_index(index, faiss_index_path)
        app_logger.info(f"FAISS index saved to: {faiss_index_path}")

        # Step 5: Create and save the ID mapping (same as before)
        float_ids = df_meta['float_id'].tolist()
        id_mapping = {i: int(fid) for i, fid in enumerate(float_ids)}
        id_mapping_path = config['PATHS']['ID_MAPPING_PATH']
        with open(id_mapping_path, 'w') as f:
            json.dump(id_mapping, f)
        app_logger.info(f"ID mapping saved to: {id_mapping_path}")

    except Exception as e:
        app_logger.error(f"Failed to rebuild FAISS index: {e}", exc_info=True)
        raise