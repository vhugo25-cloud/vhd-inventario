import sqlite3

class InventarioDB:
    def __init__(self, db_name="magazzino_casa.db"):
        self.db_name = db_name
        self.crea_tabelle()

    def connetti_db(self):
        return sqlite3.connect(self.db_name, check_same_thread=False)

    def crea_tabelle(self):
        conn = self.connetti_db()
        cursor = conn.cursor()
        # Tabella Posizioni
        cursor.execute('''CREATE TABLE IF NOT EXISTS POSIZIONI 
                          (ID_POSIZIONE TEXT PRIMARY KEY, ZONA TEXT)''')
        # Tabella Inventario
        cursor.execute('''CREATE TABLE IF NOT EXISTS inventario 
                          (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                           nome_scatola TEXT NOT NULL, 
                           desc_generale TEXT,
                           foto_principale TEXT,
                           strato_cima TEXT, foto_cima TEXT,
                           strato_centro TEXT, foto_centro TEXT,
                           strato_fondo TEXT, foto_fondo TEXT,
                           zona TEXT, 
                           ubicazione TEXT,
                           proprietario TEXT)''')
        conn.commit()
        conn.close()

    def aggiungi_scatola(self, nome, desc, f_main, cima, f_cima, centro, f_centro, fondo, f_fondo, zona, ubicazione, proprietario):
        conn = self.connetti_db()
        query = """INSERT INTO inventario 
                   (nome_scatola, desc_generale, foto_principale, strato_cima, foto_cima, strato_centro, foto_centro, strato_fondo, foto_fondo, zona, ubicazione, proprietario) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
        conn.execute(query, (nome, desc, f_main, cima, f_cima, centro, f_centro, fondo, f_fondo, zona, ubicazione, proprietario))
        conn.commit()
        conn.close()

    def elimina_scatola(self, id_scatola):
        conn = self.connetti_db()
        conn.execute("DELETE FROM inventario WHERE id = ?", (id_scatola,))
        conn.commit()
        conn.close()

    def visualizza_inventario(self):
        conn = self.connetti_db()
        res = conn.execute("SELECT * FROM inventario").fetchall()
        conn.close()
        return res

    def cerca_scatola(self, termine):
        conn = self.connetti_db()
        c = f"%{termine}%"
        res = conn.execute("""SELECT * FROM inventario WHERE 
                              nome_scatola LIKE ? OR desc_generale LIKE ? OR 
                              zona LIKE ? OR ubicazione LIKE ? OR 
                              strato_cima LIKE ? OR strato_centro LIKE ? OR strato_fondo LIKE ?""", 
                           (c, c, c, c, c, c, c)).fetchall()
        conn.close()
        return res
    
    def visualizza_posizioni(self):
        conn = self.connetti_db()
        res = conn.execute("SELECT ID_POSIZIONE, ZONA FROM POSIZIONI").fetchall()
        conn.close()
        return res

    def aggiungi_posizione(self, id_posizione, zona):
        conn = self.connetti_db()
        conn.execute("INSERT OR IGNORE INTO POSIZIONI (ID_POSIZIONE, ZONA) VALUES (?, ?)", (id_posizione, zona))
        conn.commit()
        conn.close()

    def aggiorna_posizione_scatola(self, id_scatola, zona, ubicazione):
        conn = self.connetti_db()
        conn.execute("UPDATE inventario SET zona = ?, ubicazione = ? WHERE id = ?", (zona, ubicazione, id_scatola))
        conn.commit()
        conn.close()

    def import_posizioni_da_df(self, df):
        conn = self.connetti_db()
        cursor = conn.cursor()
        for _, row in df.iterrows():
            id_p = str(row.get('ID Scaffale', row.get('Ubicazione', row.get('ID_POSIZIONE', ''))))
            zona = str(row.get('Zona', row.get('ZONA', '')))
            if id_p and zona:
                cursor.execute("INSERT OR IGNORE INTO POSIZIONI (ID_POSIZIONE, ZONA) VALUES (?, ?)", (id_p, zona))
        conn.commit()
        conn.close()

    def elimina_posizione(self, id_posizione):
        conn = self.connetti_db()
        conn.execute("DELETE FROM POSIZIONI WHERE ID_POSIZIONE = ?", (id_posizione,))
        conn.commit()
        conn.close()
            