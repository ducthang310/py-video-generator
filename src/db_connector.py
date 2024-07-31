import psycopg2
from config import DB_CONFIG


def get_db_connection():
    """Establish and return a connection to the PostgreSQL database."""
    conn = None
    try:
        print(f"Attempting to connect to {DB_CONFIG['host']}...")

        conn = psycopg2.connect(**DB_CONFIG)
        print("Database connection successful")
        return conn
    except psycopg2.OperationalError as e:
        print(f"Failed to connect to the database: {e}")
        raise
    except Exception as e:
        print(f"Unexpected error during database connection: {e}")
        raise
    finally:
        if conn is not None and conn.closed:
            conn.close()


def execute_query(query, params=None):
    """Execute a database query and return the results."""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchall()
    except Exception as e:
        print(f"Error executing query: {e}")
        raise
    finally:
        if conn is not None and not conn.closed:
            conn.close()