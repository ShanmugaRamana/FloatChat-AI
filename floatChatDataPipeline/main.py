import os
import sys
import logging
from src import config, database, etl, vector_store

def setup_logging():
    """
    Configures a root logger to write to files and the console.
    This is a more robust setup.
    """
    os.makedirs('logs', exist_ok=True)
    
    # Get the root logger
    log = logging.getLogger()
    log.setLevel(logging.INFO)
    
    # Clear existing handlers to prevent duplicate logs
    if log.handlers:
        log.handlers.clear()

    # Create a shared formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    log.addHandler(console_handler)

    # Create app.log file handler
    app_file_handler = logging.FileHandler('logs/app.log', mode='a')
    app_file_handler.setFormatter(formatter)
    log.addHandler(app_file_handler)
    
    # Create pipeline.log file handler
    pipeline_file_handler = logging.FileHandler('logs/pipeline.log', mode='a')
    # Make pipeline log simpler
    pipeline_file_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
    log.addHandler(pipeline_file_handler)

def main():
    """Main function to orchestrate the ETL and indexing pipeline."""
    setup_logging()
    app_logger = logging.getLogger('app_main') # Get a logger for this module
    
    app_logger.info("--- Starting FloatChat Data Pipeline Run ---")
    
    conn = None
    try:
        cfg = config.load_config()
        app_logger.info("Configuration loaded.")
        
        conn = database.get_connection(cfg)
        app_logger.info("Database connection successful.")

        database.setup_database(conn)
        app_logger.info("Database schema setup complete.")

        source_dir = cfg['PATHS']['SOURCE_DIR']
        files_to_process = etl.find_new_files(source_dir)
        
        if not files_to_process:
            app_logger.info("No new files found to process.")
            return

        app_logger.info(f"Found {len(files_to_process)} new file(s) to process.")
        successful_files_count = 0

        for nc_file in files_to_process:
            file_name = os.path.basename(nc_file)
            logging.info(f"Processing: {file_name}") # Use root logger for pipeline steps
            
            success = etl.process_file(conn, nc_file, cfg)
            
            if success:
                successful_files_count += 1
                logging.info(f"SUCCESS: {file_name} processed and archived.")
            else:
                logging.error(f"FAILED: {file_name}. Check logs for details.")
        
        app_logger.info(f"File processing complete. {successful_files_count}/{len(files_to_process)} successful.")

        if successful_files_count > 0:
            app_logger.info("New data added, rebuilding FAISS index...")
            vector_store.rebuild_index(conn, cfg)
            app_logger.info("FAISS index rebuilt successfully.")
        else:
            app_logger.info("No data was successfully processed, skipping index rebuild.")

    except Exception as e:
        app_logger.error(f"A critical error occurred: {e}", exc_info=True)
    finally:
        if conn:
            conn.close()
            app_logger.info("Database connection closed.")
        app_logger.info("--- FloatChat Data Pipeline Run Finished ---\n")

if __name__ == "__main__":
    main()