import sqlite3
import os

def migrate_database():
    # Path to the SQLite database
    db_path = 'instance/book_summaries.db'
    
    # Check if the database exists
    if not os.path.exists(db_path):
        print(f"Database file not found at {db_path}")
        return False
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if pdf_text column exists
        cursor.execute("PRAGMA table_info(summary)")
        columns = cursor.fetchall()
        column_names = [column[1] for column in columns]
        
        if 'pdf_text' not in column_names:
            print("Adding pdf_text column to summary table...")
            cursor.execute("ALTER TABLE summary ADD COLUMN pdf_text TEXT")
            conn.commit()
            print("Migration successful!")
        else:
            print("pdf_text column already exists.")
        
        return True
    except Exception as e:
        print(f"Error during migration: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()