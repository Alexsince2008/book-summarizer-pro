import sqlite3
import os
import psycopg2
from app import db
from models import Summary

def migrate_to_postgres():
    """Migrate data from SQLite to PostgreSQL database."""
    
    # Path to the SQLite database
    db_path = 'instance/book_summaries.db'
    
    # Check if the SQLite database exists
    if not os.path.exists(db_path):
        print(f"SQLite database file not found at {db_path}")
        return False
    
    # Connect to the SQLite database
    sqlite_conn = sqlite3.connect(db_path)
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cursor = sqlite_conn.cursor()
    
    try:
        # Get all summaries from SQLite
        sqlite_cursor.execute("SELECT * FROM summary")
        rows = sqlite_cursor.fetchall()
        
        print(f"Found {len(rows)} summaries in SQLite database.")
        
        if not rows:
            print("No data to migrate.")
            return True
        
        # Create new records in PostgreSQL
        count = 0
        for row in rows:
            # Convert SQLite row to dict
            row_dict = {key: row[key] for key in row.keys()}
            
            # Check if a summary with the same filename already exists in PostgreSQL
            existing = Summary.query.filter_by(filename=row_dict['filename']).first()
            
            if not existing:
                # Create a new Summary instance
                summary = Summary(
                    filename=row_dict['filename'],
                    title=row_dict['title'] if 'title' in row_dict and row_dict['title'] else os.path.splitext(row_dict['filename'])[0],
                    pdf_text=row_dict.get('pdf_text', ''),
                    short_summary=row_dict.get('short_summary', ''),
                    brief_summary=row_dict.get('brief_summary', ''),
                    detailed_summary=row_dict.get('detailed_summary', ''),
                    page_count=row_dict.get('page_count', 0)
                )
                
                db.session.add(summary)
                count += 1
                
                # Commit every 10 records to avoid large transactions
                if count % 10 == 0:
                    db.session.commit()
                    print(f"Migrated {count} of {len(rows)} summaries...")
        
        # Final commit for any remaining records
        if count % 10 != 0:
            db.session.commit()
            
        print(f"Successfully migrated {count} summaries to PostgreSQL.")
        return True
        
    except Exception as e:
        print(f"Error during migration: {e}")
        db.session.rollback()
        return False
        
    finally:
        sqlite_conn.close()

if __name__ == "__main__":
    # This will run within the Flask app context
    from app import app
    with app.app_context():
        migrate_to_postgres()