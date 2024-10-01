import sqlite3
import json


def get_db_connection():
    conn = sqlite3.connect('sequence_reconstruction.db')
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    c = conn.cursor()

    # Create documents table
    c.execute('''CREATE TABLE IF NOT EXISTS documents
                 (id INTEGER PRIMARY KEY, content TEXT)''')

    # Create pubmed_results table
    c.execute('''CREATE TABLE IF NOT EXISTS pubmed_results
                 (id INTEGER PRIMARY KEY, query TEXT UNIQUE, results TEXT)''')

    # Create arxiv_results table
    c.execute('''CREATE TABLE IF NOT EXISTS arxiv_results
                 (id INTEGER PRIMARY KEY, query TEXT UNIQUE, results TEXT)''')

    conn.commit()
    conn.close()


def store_document(chunks):
    conn = get_db_connection()
    c = conn.cursor()
    for chunk in chunks:
        c.execute("INSERT INTO documents (content) VALUES (?)", (json.dumps(chunk),))
    conn.commit()
    conn.close()
    return len(chunks)


def get_relevant_documents(query):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM documents WHERE content LIKE ?", (f"%{query}%",))
    results = [json.loads(row['content']) for row in c.fetchall()]
    conn.close()
    return results


def store_pubmed_results(query, results):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO pubmed_results (query, results) VALUES (?, ?)",
              (query, json.dumps(results)))
    conn.commit()
    conn.close()


def get_pubmed_results(query):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT results FROM pubmed_results WHERE query = ?", (query,))
    row = c.fetchone()
    conn.close()
    return json.loads(row['results']) if row else []


def store_arxiv_results(query, results):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO arxiv_results (query, results) VALUES (?, ?)",
              (query, json.dumps(results)))
    conn.commit()
    conn.close()


def get_arxiv_results(query):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT results FROM arxiv_results WHERE query = ?", (query,))
    row = c.fetchone()
    conn.close()
    return json.loads(row['results']) if row else []


def clear_all_data():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("DELETE FROM documents")
    c.execute("DELETE FROM pubmed_results")
    c.execute("DELETE FROM arxiv_results")
    conn.commit()
    conn.close()


def get_all_documents():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM documents")
    results = [{'id': row['id'], 'content': json.loads(row['content'])} for row in c.fetchall()]
    conn.close()
    return results


def get_all_pubmed_queries():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT DISTINCT query FROM pubmed_results")
    results = [row['query'] for row in c.fetchall()]
    conn.close()
    return results


def get_all_arxiv_queries():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT DISTINCT query FROM arxiv_results")
    results = [row['query'] for row in c.fetchall()]
    conn.close()
    return results


# Call this function when your application starts
init_db()