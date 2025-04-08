import sqlite3
import os
from datetime import datetime

def get_recent_summaries():
    # Path to the SQLite database
    db_path = 'instance/book_summaries.db'
    
    # Check if the database exists
    if not os.path.exists(db_path):
        print(f"Database file not found at {db_path}")
        return []
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # This enables column access by name
    cursor = conn.cursor()
    
    try:
        # Get the most recent summaries
        cursor.execute("""
            SELECT id, filename, title, page_count, created_at 
            FROM summary 
            ORDER BY id DESC 
            LIMIT 5
        """)
        
        summaries = []
        for row in cursor.fetchall():
            summary = dict(row)
            # Format created_at if it exists
            if summary.get('created_at'):
                try:
                    created_at = datetime.fromisoformat(summary['created_at'].replace('Z', '+00:00'))
                    summary['created_at'] = created_at.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    pass
            summaries.append(summary)
        
        return summaries
    except Exception as e:
        print(f"Error getting summaries: {e}")
        return []
    finally:
        conn.close()

if __name__ == "__main__":
    summaries = get_recent_summaries()
    if summaries:
        print("Recent summaries:")
        for summary in summaries:
            print(f"ID: {summary['id']}, Title: {summary['title']}, Pages: {summary['page_count']}, Created: {summary.get('created_at', 'N/A')}")
    else:
        print("No summaries found or error occurred.")