import os
from dotenv import load_dotenv

def load_config():
    """
    Loads configuration from the .env file and returns it as a dictionary.
    """
    # Load environment variables from a .env file located in the parent directory
    dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    load_dotenv(dotenv_path)

    config = {
        'DATABASE': {
            'HOST': os.getenv('DB_HOST'),
            'PORT': os.getenv('DB_PORT'),
            'NAME': os.getenv('DB_NAME'),
            'USER': os.getenv('DB_USER'),
            'PASSWORD': os.getenv('DB_PASSWORD')
        },
        'PATHS': {
            'SOURCE_DIR': os.getenv('NETCDF_SOURCE_DIR'),
            'ARCHIVE_DIR': os.getenv('NETCDF_ARCHIVE_DIR'),
            'FAISS_INDEX_PATH': os.getenv('FAISS_INDEX_PATH'),
            'ID_MAPPING_PATH': os.getenv('ID_MAPPING_PATH'),
            # --- THIS IS THE NEW LINE THAT FIXES THE ERROR ---
            'OUTPUT_DIR': os.getenv('OUTPUT_DIR')
        }
    }

    # Basic validation to ensure essential variables are set
    if not all(config['DATABASE'].values()):
        raise ValueError("One or more required database environment variables are not set.")
    if not all(config['PATHS'].values()):
        raise ValueError("One or more required path environment variables are not set.")
        
    return config

if __name__ == '__main__':
    # A simple test to check if the config loads correctly
    try:
        cfg = load_config()
        print("Configuration loaded successfully!")
        import json
        print(json.dumps(cfg, indent=2))
    except (ValueError, FileNotFoundError) as e:
        print(f"Error loading configuration: {e}")