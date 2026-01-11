import pandas as pd
from supabase import create_client, Client
import streamlit as st

class InventarioDB:
    def __init__(self):
        self.url = st.secrets["SUPABASE_URL"]
        self.key = st.secrets["SUPABASE_KEY"]
        self.supabase: Client = create_client(self.url, self.key)

    def sveglia_database(self):
        try:
            self.supabase.table("inventario").select("*").limit(1).execute()
            return True, "Database Sveglio"
        except Exception as e:
            return False, str(e)

    def visualizza_inventario(self):
        try:
            res = self.supabase.table("inventario").select("*").execute()
            return [list(item.values()) for item in res.data]
        except Exception as e:
            st.error(f"Errore caricamento inventario: {e}")
            return []

    def visualizza_posizioni(self):
        try:
            res = self.supabase.table("posizioni").select("*").execute()
            return [list(item.values()) for item in res.data]
        except Exception as e:
            st.error(f"Errore caricamento posizioni: {e}")
            return []

    def get_scatole(self):
        try:
            res = self.supabase.table("inventario").select("nome").execute()
            return pd.DataFrame(res.data)
        except Exception as e:
            return pd.DataFrame()

    def aggiungi_scatola(self, **kwargs):
        try:
            self.supabase.table("inventario").insert(kwargs).execute()
            return True
        except Exception as e:
            st.error(f"Errore salvataggio nuova scatola: {e}")
            return False

    def aggiungi_posizione(self, id_u, zona):
        """Aggiunge una singola posizione nel magazzino"""
        try:
            self.supabase.table("posizioni").insert({"id": id_u, "zona": zona}).execute()
            return True
        except Exception as e:
            st.error(f"Errore salvataggio posizione: {e}")
            return False

    def import_posizioni_da_df(self, df):
        """Importa posizioni da un file Excel (deve avere colonne 'id' e 'zona')"""
        try:
            records = df.to_dict('records')
            self.supabase.table("posizioni").insert(records).execute()
            return True, len(records)
        except Exception as e:
            st.error(f"Errore importazione: {e}")
            return False, 0

    def aggiorna_foto_scatola(self, nome_scatola, url_foto):
        try:
            self.supabase.table("inventario").update({"f_m": url_foto, "foto_url": url_foto}).eq("nome", nome_scatola).execute()
            return True
        except Exception as e:
            st.error(f"Errore aggiornamento foto: {e}")
            return False

    def aggiorna_posizione_scatola(self, nome_scatola, zona, ubicazione):
        try:
            dati = {"zona": zona, "ubicazione": ubicazione, "ubi": ubicazione, "id_u": ubicazione}
            self.supabase.table("inventario").update(dati).eq("nome", nome_scatola).execute()
            return True
        except Exception as e:
            st.error(f"Errore spostamento: {e}")
            return False

    def cerca_scatola(self, termine):
        try:
            res = self.supabase.table("inventario").select("*").or_(f"nome.ilike.%{termine}%,desc.ilike.%{termine}%").execute()
            return [list(item.values()) for item in res.data]
        except Exception as e:
            st.error(f"Errore ricerca: {e}")
            return []

    def elimina_scatola(self, id_scatola):
        try:
            self.supabase.table("inventario").delete().eq("id", id_scatola).execute()
            return True
        except Exception as e:
            st.error(f"Errore eliminazione: {e}")
            return False