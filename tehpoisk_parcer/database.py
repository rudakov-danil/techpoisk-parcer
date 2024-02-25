import json
import sqlite3

DATABASE = "test_items.db"


def connect():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def create_tables(table_name):
    db = connect()
    cur = db.cursor()
    cur.execute(
        f"""
CREATE TABLE IF NOT EXISTS {table_name} (
      tag              TEXT     PRIMARY KEY,
      info             TEXT     NOT NULL,
      shops            TEXT     NOT NULL,
      image_urls       TEXT     NOT NULL,
      full_info        text
);  
        """)

    db.commit()
    cur.close()
    db.close()


def clear(table_name):
    db = connect()
    cur = db.cursor()
    cur.execute(f'''
        DROP TABLE IF EXISTS {table_name}
    ''')
    create_tables(table_name)
    db.commit()
    cur.close()
    db.close()

def alter(table_name):
    db = connect()
    cur = db.cursor()
    cur.execute(f'''
            ALTER TABLE {table_name} 
            ADD full_info text;
        ''')
    db.commit()
    cur.close()
    db.close()





if __name__ == '__main__':
    clear('mb')
