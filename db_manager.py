import sqlite3
from datetime import datetime
import pandas as pd

class InventarioDB:
    def __init__(self, db_name="vhd_warehouse.db"):
        self.db_name = db_name
        self.crea_tabelle()

    def connetti_db(self):
        return sqlite3.connect(self.db_name)

    def crea_tabelle(self):
        conn = self.connetti_db()
        cursor = conn.cursor()
        # Tabella Inventario: 14 colonne totali (ID + 13 campi dati)
        cursor.execute('''CREATE TABLE IF NOT EXISTS inventario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT, 
            descrizione TEXT, 
            foto_main TEXT,
            cima_testo TEXT, 
            cima_foto TEXT,
            centro_testo TEXT, 
            centro_foto TEXT,
            fondo_testo TEXT, 
            fondo_foto TEXT,
            zona TEXT, 
            ubicazione TEXT, 
            proprietario TEXT, 
            data TEXT
        )''')
        
        # Tabella Posizioni: Struttura del magazzino
        cursor.execute('''CREATE TABLE IF NOT EXISTS posizioni (
            id_ubicazione TEXT PRIMARY KEY,
            zona TEXT
        )''')
        conn.commit()
        conn.close()

    def aggiungi_scatola(self, nome, desc, f_m, ct, cf, mt, mf, bt, bf, zona, ubi, prop):
        conn = self.connetti_db()
        cursor = conn.cursor()
        data_ora = datetime.now().strftime("%d/%m/%Y %H:%M")
        cursor.execute('''INSERT INTO inventario 
            (nome, descrizione, foto_main, cima_testo, cima_foto, 
             centro_testo, centro_foto, fondo_testo, fondo_foto, 
             zona, ubicazione, proprietario, data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (nome, desc, f_m, ct, cf, mt, mf, bt, bf, zona, ubi, prop, data_ora))
        conn.commit()
        conn.close()

    def visualizza_inventario(self):
        conn = self.connetti_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM inventario ORDER BY id DESC")
        rows = cursor.fetchall()
        conn.close()
        return rows

    def cerca_scatola(self, termine):
        conn = self.connetti_db()
        cursor = conn.cursor()
        t = f"%{termine}%"
        cursor.execute('''SELECT * FROM inventario WHERE 
                          nome LIKE ? OR descrizione LIKE ? OR 
                          cima_testo LIKE ? OR centro_testo LIKE ? OR 
                          fondo_testo LIKE ? OR proprietario LIKE ? OR 
                          zona LIKE ?''', (t, t, t, t, t, t, t))
        rows = cursor.fetchall()
        conn.close()
        return rows

    def elimina_scatola(self, id_scatola):
        conn = self.connetti_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM inventario WHERE id = ?", (id_scatola,))
        conn.commit()
        conn.close()

    # --- GESTIONE POSIZIONI (MAGAZZINO) ---
    def aggiungi_posizione(self, id_u, zona):
        conn = self.connetti_db()
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO posizioni (id_ubicazione, zona) VALUES (?, ?)", (id_u, zona))
        conn.commit()
        conn.close()

    def visualizza_posizioni(self):
        conn = self.connetti_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM posizioni ORDER BY zona, id_ubicazione")
        rows = cursor.fetchall()
        conn.close()
        return rows

    def elimina_posizione(self, id_u):
        conn = self.connetti_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM posizioni WHERE id_ubicazione = ?", (id_u,))
        conn.commit()
        conn.close()

    def aggiorna_posizione_scatola(self, id_s, zona, ubi):
        conn = self.connetti_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE inventario SET zona = ?, ubicazione = ? WHERE id = ?", (zona, ubi, id_s))
        conn.commit()
        conn.close()

    def import_posizioni_da_df(self, df):
        """Versione Universale: Legge la prima colonna come ID e la seconda come ZONA"""
        conn = self.connetti_db()
        cursor = conn.cursor()
        
        successi = 0
        try:
            for i, row in df.iterrows():
                # Legge per posizione delle colonne (0 e 1) invece che per nome
                val_id = str(row.iloc[0]).strip()
                val_zona = str(row.iloc[1]).strip()
                
                # Salta le righe di intestazione se presenti
                if val_id.upper() in ["ID", "UBICAZIONE", "SCAFFALE"] or val_zona.upper() == "ZONA":
                    continue

                # Inserisce solo se i dati sono validi
                if val_id and val_id.lower() != 'nan' and val_zona and val_zona.lower() != 'nan':
                    cursor.execute("INSERT OR REPLACE INTO posizioni (id_ubicazione, zona) VALUES (?, ?)", 
                                   (val_id, val_zona))
                    successi += 1
            
            conn.commit()
            conn.close()
            return True, successi
        except Exception as e:
            print(f"Errore Import: {e}")
            conn.close()
            return False, 0
        