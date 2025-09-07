import psycopg2
import logging
import os

# Get the logger that was configured in main.py
app_logger = logging.getLogger('app')

def get_connection(config):
    """
    Establishes a connection to the PostgreSQL database using configuration.

    Args:
        config (dict): The configuration dictionary loaded from config.py.

    Returns:
        psycopg2.connection: A connection object, or None if connection fails.
    """
    try:
        conn = psycopg2.connect(
            host=config['DATABASE']['HOST'],
            port=config['DATABASE']['PORT'],
            dbname=config['DATABASE']['NAME'],
            user=config['DATABASE']['USER'],
            password=config['DATABASE']['PASSWORD']
        )
        return conn
    except psycopg2.OperationalError as e:
        app_logger.error(f"Database connection failed: {e}")
        # This is a critical error, so we might want to raise it to stop the pipeline
        raise
    except Exception as e:
        app_logger.error(f"An unexpected error occurred during database connection: {e}")
        raise

def setup_database(conn):
    """
    Sets up the database schema by executing the create_tables.sql script.
    This function is idempotent; it won't fail if the tables already exist.

    Args:
        conn (psycopg2.connection): An active database connection object.
    """
    app_logger.info("Setting up database tables if they don't exist...")
    
    # Construct the path to the SQL file relative to this script's location
    # This script is in src/, the sql folder is a sibling of src/
    sql_file_path = os.path.join(os.path.dirname(__file__), '..', 'sql', 'create_tables.sql')

    try:
        with open(sql_file_path, 'r') as f:
            sql_commands = f.read()

        with conn.cursor() as cur:
            cur.execute(sql_commands)
        
        conn.commit()
        app_logger.info("Database setup successful. Tables are ready.")

    except FileNotFoundError:
        app_logger.error(f"SQL setup file not found at: {sql_file_path}")
        raise
    except Exception as e:
        app_logger.error(f"Failed to execute database setup script: {e}")
        conn.rollback() # Rollback any partial changes
        raise

if __name__ == '__main__':
    # This block allows for direct testing of the database connection and setup
    # Note: You need a .env file and config.py for this to run
    from config import load_config

    # A simple logger for direct testing when this script is run alone
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    connection = None
    try:
        cfg = load_config()
        print("Attempting to connect to the database...")
        connection = get_connection(cfg)
        print("Connection successful!")
        
        setup_database(connection)
        
    except Exception as e:
        print(f"An error occurred during testing: {e}")
    finally:
        if connection:
            connection.close()
            print("Connection closed.")