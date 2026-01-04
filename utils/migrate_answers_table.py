"""One-off migration script to update answers table schema.

This script migrates the answers table from confidence_score to understanding_score.
Run this once to update existing databases.
"""

import sqlite3
import sys
from pathlib import Path

# Add src to path to import config
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from inkling.config import get_config


def migrate_answers_table(db_path: Path) -> bool:
    """Migrate answers table from confidence_score to understanding_score.
    
    Args:
        db_path: Path to the SQLite database file
        
    Returns:
        True if migration was successful or not needed, False if it failed
    """
    if not db_path.exists():
        print(f"Database file not found: {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if old column exists
        cursor.execute("PRAGMA table_info(answers)")
        columns = [row[1] for row in cursor.fetchall()]
        
        has_confidence_score = 'confidence_score' in columns
        has_understanding_score = 'understanding_score' in columns
        
        if not has_confidence_score and has_understanding_score:
            print("✓ Database already has understanding_score column. No migration needed.")
            return True
        
        if not has_confidence_score:
            print("✓ No confidence_score column found. Database may already be migrated or schema is different.")
            return True
        
        print(f"Found confidence_score column. Starting migration...")
        
        # Create new table with correct schema
        cursor.execute("""
            CREATE TABLE answers_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id INTEGER NOT NULL,
                user_answer TEXT NOT NULL,
                is_correct BOOLEAN NOT NULL,
                understanding_score INTEGER,
                feedback TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (question_id) REFERENCES questions(id)
            )
        """)
        
        # Copy data from old table (excluding confidence_score)
        cursor.execute("""
            INSERT INTO answers_new 
            (id, question_id, user_answer, is_correct, understanding_score, feedback, timestamp)
            SELECT 
                id, 
                question_id, 
                user_answer, 
                is_correct, 
                NULL as understanding_score,
                feedback, 
                timestamp
            FROM answers
        """)
        
        # Get row count for confirmation
        cursor.execute("SELECT COUNT(*) FROM answers_new")
        row_count = cursor.fetchone()[0]
        
        # Drop old table
        cursor.execute("DROP TABLE answers")
        
        # Rename new table
        cursor.execute("ALTER TABLE answers_new RENAME TO answers")
        
        conn.commit()
        print(f"✓ Successfully migrated {row_count} answer records")
        print("✓ Replaced confidence_score column with understanding_score column")
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"✗ Migration failed: {str(e)}")
        return False
    finally:
        conn.close()


def main():
    """Run the migration."""
    config = get_config()
    storage_config = config.get_storage_config()
    db_path = Path(storage_config.get('database_path', 'data/inkling.db'))
    
    print(f"Migrating database: {db_path}")
    print("-" * 50)
    
    success = migrate_answers_table(db_path)
    
    if success:
        print("-" * 50)
        print("Migration completed successfully!")
        sys.exit(0)
    else:
        print("-" * 50)
        print("Migration failed. Please check the error messages above.")
        sys.exit(1)


if __name__ == "__main__":
    main()

