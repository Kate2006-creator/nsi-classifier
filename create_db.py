import psycopg2
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

def create_database():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database='postgres'
        )
        conn.autocommit = True
        cur = conn.cursor()
        
        cur.execute(f"CREATE DATABASE {DB_NAME}")
        print(f"[OK] Database {DB_NAME} created")
        
        cur.close()
        conn.close()
    except psycopg2.errors.DuplicateDatabase:
        print(f"[INFO] Database {DB_NAME} already exists")
    except Exception as e:
        print(f"[ERROR] {e}")

if __name__ == "__main__":
    create_database()