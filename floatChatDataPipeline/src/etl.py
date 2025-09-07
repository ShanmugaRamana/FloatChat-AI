import os
import shutil
import logging
import xarray as xr
import pandas as pd
import numpy as np
import json
from psycopg2.extras import execute_values

etl_logger = logging.getLogger('etl')
VIRTUAL_FLOAT_ID = 9999999

# Define the variables that are coordinates/dimensions, not measurements.
# We'll treat everything else as a measurement.
COORDINATE_VARS = {'time', 'latitude', 'longitude', 'depth'}

def find_new_files(source_dir):
    if not os.path.isdir(source_dir):
        etl_logger.warning(f"Source directory not found: {source_dir}. No files to process.")
        return []
    return [os.path.join(source_dir, f) for f in os.listdir(source_dir) if f.endswith('.nc')]

def process_file(conn, nc_file_path, config):
    ds = None
    try:
        etl_logger.info(f"Opening {os.path.basename(nc_file_path)} with flexible JSONB logic.")
        with xr.open_dataset(nc_file_path) as ds:
            df = ds.to_dataframe().reset_index()

            if not all(coord in df.columns for coord in COORDINATE_VARS):
                etl_logger.error(f"File {os.path.basename(nc_file_path)} is missing a core coordinate. Skipping.")
                return False

            # Dynamically discover the measurement variables
            data_vars = [col for col in df.columns if col not in COORDINATE_VARS]
            if not data_vars:
                etl_logger.warning(f"No data variables found in {os.path.basename(nc_file_path)}. Skipping.")
                return False

            df.dropna(subset=list(COORDINATE_VARS), inplace=True)
            if df.empty:
                etl_logger.warning(f"No valid coordinate data in {os.path.basename(nc_file_path)}. Archiving.")
                archive_dir = config['PATHS']['ARCHIVE_DIR']
                os.makedirs(archive_dir, exist_ok=True)
                shutil.move(nc_file_path, os.path.join(archive_dir, os.path.basename(nc_file_path)))
                return True

            profile_groups = df.groupby(['time', 'latitude', 'longitude'])

            with conn.cursor() as cur:
                for (profile_time, lat, lon), group in profile_groups:
                    profile_sql = """
                        INSERT INTO profiles (float_id, profile_time, latitude, longitude)
                        VALUES (%s, %s, %s, %s) ON CONFLICT (float_id, profile_time, latitude, longitude) DO NOTHING RETURNING profile_id;
                    """
                    cur.execute(profile_sql, (VIRTUAL_FLOAT_ID, profile_time, float(lat), float(lon)))
                    result = cur.fetchone()
                    if result is None: continue
                    profile_id = result[0]

                    measurements_data = []
                    for _, row in group.iterrows():
                        # Create a dictionary payload of all available data variables
                        data_payload = {}
                        for var in data_vars:
                            value = row.get(var)
                            if pd.notna(value):
                                # Convert numpy types to standard Python types for JSON
                                if isinstance(value, (np.floating, np.integer)):
                                    data_payload[var] = value.item()
                                else:
                                    data_payload[var] = value
                        
                        # Only insert a row if we have at least one piece of data
                        if data_payload:
                            measurements_data.append((profile_id, float(row['depth']), json.dumps(data_payload)))
                    
                    if measurements_data:
                        measurements_sql = "INSERT INTO measurements (profile_id, depth, data) VALUES %s;"
                        execute_values(cur, measurements_sql, measurements_data)
            conn.commit()

        archive_dir = config['PATHS']['ARCHIVE_DIR']
        os.makedirs(archive_dir, exist_ok=True)
        shutil.move(nc_file_path, os.path.join(archive_dir, os.path.basename(nc_file_path)))
        return True

    except Exception as e:
        etl_logger.error(f"Critical error processing {os.path.basename(nc_file_path)}: {e}", exc_info=True)
        if conn: conn.rollback()
        return False