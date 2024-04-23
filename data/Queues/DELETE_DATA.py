import sqlite3

def delete_all_data(db_file):
    # Connect to the SQLite database
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    try:
        # Fetch all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        # Delete all data from each table
        for table_name in tables:
            print(f"Deleting all data from table {table_name[0]}")
            cursor.execute(f"DELETE FROM {table_name[0]}")

        # Commit the changes
        conn.commit()
        print("All data deleted successfully.")

    except sqlite3.Error as error:
        print(f"Failed to delete all data: {error}")

    finally:
        # Close the cursor and connection
        cursor.close()
        conn.close()

# Usage
db_path = '../listing_data.db'
delete_all_data(db_path)
