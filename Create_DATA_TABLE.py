import sqlite3


def create_db(table_name):
    try:
        conn = sqlite3.connect('data/listing_data.db')
        c = conn.cursor()
        c.execute(f'''
            CREATE TABLE IF NOT EXISTS {table_name} (
            id INTEGER PRIMARY KEY,
            listing_id TEXT NOT NULL,
            image_url TEXT,
            price TEXT,
            beds TEXT,
            ratings TEXT
        )
    ''')
        conn.commit()
        conn.close()
        print("Successfully Created New Table")
    except Exception as e:
        print("Failed to Create Table")

 # Call this function when initializing your app to ensure the database is ready.
