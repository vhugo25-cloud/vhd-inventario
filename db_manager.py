import pandas as pd
from supabase import create_client, Client
import streamlit as st

class InventarioDB:
    def __init__(self):
        # Carica le credenziali dai Secrets di Streamlit
        self.url = st.secrets["SUPABASE_URL"]
        self.key = st.secrets["SUPABASE_KEY"]
        self.supabase: Client = create_client(self.url, self.key)

    def sveglia_database(self):
        """Verifica la connessione con Supabase"""
        try:
            self.supabase.table("inventario").select("*").limit(1).execute()
            return True, "Database Sveglio"
        except Exception as e:
            return False, str(e)

    def visualizza_inventario(self):
        """Scarica tutto l'inventario per la Home"""
        try:
            res = self.supabase.table("inventario").select("*").execute()
            return [list(item.values()) for item in res.data]
        except Exception as e:
            st.error(f"Errore caricamento inventario: {e}")
            return []

    def visualizza_posizioni(self):
        """Scarica le ubicazioni per la mappa magazzino"""
        try:
            res = self.supabase.table("posizioni").select("*").execute()
            return [list(item.values()) for item in res.data]
        except Exception as e:
            st.error(f"Errore caricamento posizioni: {e}")
            return []

    def get_scatole(self):
        """Recupera solo i nomi delle scatole per i menu a tendina"""
        try:
            res = self.supabase.table("inventario").select("nome").execute()
            return pd.DataFrame(res.data)
        except Exception as e:
            return pd.DataFrame()

    def aggiungi_scatola(self, **kwargs):
        """Inserisce una nuova scatola (accetta qualsiasi colonna f_m, ubi, prop, ecc.)"""
        try:
            self.supabase.table("inventario").insert(kwargs).execute()
            return True
        except Exception as e:
            st.error(f"Errore salvataggio nuova scatola: {e}")
            return False

    def aggiorna_foto_scatola(self, nome_scatola, url_foto):
        """Aggiorna il link della foto per una scatola esistente (Modifica Foto)"""
        try:
            # Aggiorniamo sia 'f_m' che 'foto_url' per massima compatibilità
            self.supabase.table("inventario").update({"f_m": url_foto, "foto_url": url_foto}).eq("nome", nome_scatola).execute()
            return True
        except Exception as e:
            st.error(f"Errore aggiornamento foto: {e}")
            return False

    def aggiorna_posizione_scatola(self, nome_scatola, zona, ubicazione):
        """Sposta una scatola in una nuova zona e ubicazione"""
        try:
            dati_aggiornati = {
                "zona": zona,
                "ubicazione": ubicazione,
                "ubi": ubicazione,  # Supporto per colonna abbreviata
                "id_u": ubicazione  # Supporto per colonna ID posizione
            }
            self.supabase.table("inventario").update(dati_aggiornati).eq("nome", nome_scatola).execute()
            return True
        except Exception as e:
            st.error(f"Errore durante lo spostamento: {e}")
            return False

    def cerca_scatola(self, termine):
        """Cerca una scatola per nome o descrizione (case-insensitive)"""
        try:
            res = self.supabase.table("inventario").select("*").or_(f"nome.ilike.%{termine}%,desc.ilike.%{termine}%").execute()
            return [list(item.values()) for item in res.data]
        except Exception as e:
            st.error(f"Errore durante la ricerca: {e}")
            return []

    def elimina_scatola(self, id_scatola):
        """Elimina definitivamente una scatola dal database tramite ID"""
        try:
            self.supabase.table("inventario").delete().eq("id", id_scatola).execute()
            return True
        except Exception as e:
            st.error(f"Errore eliminazione: {e}")
            return False

    def get_prossimo_id(self):
        """Calcola l'ID per la prossima scatola"""
        try:
            res = self.supabase.table("inventario").select("id").order("id", desc=True).limit(1).execute()
            if res.data:
                return res.data[0]['id'] + 1
            return 1
        except:
            return 1