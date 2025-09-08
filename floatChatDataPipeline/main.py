import logging
from src.run_pipeline import main as run_pipeline_main

# Configure a basic logger for the main entry point
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

if __name__ == "__main__":
    """
    This is the main entry point for the entire application.
    It calls the pipeline's main function and includes a top-level
    exception handler to catch any critical failures.
    """
    try:
        logging.info("--- Executing FloatChat Data Pipeline via main.py ---")
        run_pipeline_main()
        logging.info("--- Pipeline execution complete. ---")
    except Exception as e:
        # This is a final safety net to catch any uncaught errors from the pipeline.
        logging.critical(f"The pipeline failed with a critical error: {e}", exc_info=True)
        # In a production system, you could add alerting (e.g., send an email) here.