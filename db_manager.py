import sqlite3
DB_NAME = 'magazzino_casa.db'
def connetti_db(): return sqlite3.connect(DB_NAME)
def crea_tabelle():
    conn = connetti_db()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS POSIZIONI (ID_POSIZIONE TEXT PRIMARY KEY, DESCRIZIONE TEXT NOT NULL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS SCATOLE (ID_SCATOLA TEXT PRIMARY KEY, CONTENUTO TEXT NOT NULL, POSIZIONE_ATTUALE TEXT, COORDINATE TEXT, PROPRIETARIO TEXT, FOTO_COPERTINA TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS CONTENUTO_DETTAGLIO (ID_DETTAGLIO INTEGER PRIMARY KEY AUTOINCREMENT, ID_SCATOLA TEXT, DESCRIZIONE_OGGETTO TEXT NOT NULL, FOTO_PATH TEXT, STRATO TEXT)''')
    conn.commit(); conn.close()
def esegui_query(query, parametri=()):
    conn = connetti_db(); cursor = conn.cursor(); cursor.execute(query, parametri); r = cursor.fetchall(); conn.commit(); conn.close()
    return r