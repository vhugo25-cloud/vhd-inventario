import pandas as pd
from supabase import create_client, Client
import streamlit as st

class InventarioDB:
    def __init__(self):
        # Carica le credenziali dai secrets di Streamlit
        self.url = st.secrets["SUPABASE_URL"]
        self.key = st.secrets["SUPABASE_KEY"]
        self.supabase: Client = create_client(self.url, self.key)

    def sveglia_database(self):
        try:
            self.supabase.table("inventario").select("id").limit(1).execute()
            return True, "Online"
        except:
            return False, "Offline"

    def visualizza_inventario(self):
        try:
            res = self.supabase.table("inventario").select("*").execute()
            return res.data
        except:
            return []

    def visualizza_posizioni(self):
        try:
            res = self.supabase.table("posizioni").select("*").execute()
            return res.data
        except:
            return []

    def aggiungi_scatola(self, **kwargs):
        try:
            dati = {
                "nome": kwargs.get("nome"),
                "descrizione": kwargs.get("desc"),
                "foto_main": kwargs.get("f_m"),
                "cima_testo": kwargs.get("ct"),
                "cima_foto": kwargs.get("cf"),
                "centro_testo": kwargs.get("mt"),
                "centro_foto": kwargs.get("mf"),
                "fondo_testo": kwargs.get("bt"),
                "fondo_foto": kwargs.get("bf"),
                "proprietario": kwargs.get("prop"),
                "ubi": kwargs.get("ubi", "NON ALLOCATA"),
                "zon": kwargs.get("zona", "DA DEFINIRE")
            }
            self.supabase.table("inventario").insert(dati).execute()
            return True
        except:
            return False

    def aggiorna_dati_scatola(self, id_scatola, nome, desc, prop, ct, mt, bt, url_foto=None):
        try:
            dati = {
                "nome": nome,
                "descrizione": desc,
                "proprietario": prop,
                "cima_testo": ct,
                "centro_testo": mt,
                "fondo_testo": bt
            }
            if url_foto:
                dati["foto_main"] = url_foto
            self.supabase.table("inventario").update(dati).eq("id", id_scatola).execute()
            return True
        except:
            return False

    def aggiorna_posizione_scatola(self, id_scatola, zona, ubi):
        try:
            self.supabase.table("inventario").update({"zon": zona, "ubi": ubi}).eq("id", id_scatola).execute()
            return True
        except:
            return False

    def cerca_scatola(self, termine):
        try:
            filtro = f"nome.ilike.%{termine}%,descrizione.ilike.%{termine}%,proprietario.ilike.%{termine}%"
            res = self.supabase.table("inventario").select("*").or_(filtro).execute()
            return res.data
        except:
            return []

    def elimina_scatola(self, id_scatola):
        try:
            self.supabase.table("inventario").delete().eq("id", id_scatola).execute()
            return True
        except:
            return False

    def aggiungi_posizione(self, id_u, zona):
        try:
            # Upsert anche per l'aggiunta singola (evita errori se esiste già)
            self.supabase.table("posizioni").upsert({"id_ubicazione": id_u, "zona": zona}).execute()
            return True
        except:
            return False

    def import_posizioni_da_df(self, df):
        """
        Importa ubicazioni usando UPSERT: 
        se l'ID esiste già, lo aggiorna invece di bloccarsi.
        """
        try:
            # 1. Pulizia nomi colonne
            df.columns = [str(c).lower().strip() for c in df.columns]
            
            # 2. Rinominazione per id_ubicazione (il tuo campo SQL)
            df = df.rename(columns={'id scaffale': 'id_ubicazione', 'id': 'id_ubicazione', 'zona': 'zona'})
            
            # 3. Preparazione lista pulita
            lista_finale = []
            for _, r in df.iterrows():
                lista_finale.append({
                    "id_ubicazione": str(r['id_ubicazione']).strip().upper(),
                    "zona": str(r['zona']).strip()
                })
            
            # 4. UPSERT Massivo (Ignora o aggiorna duplicati)
            self.supabase.table("posizioni").upsert(lista_finale, on_conflict="id_ubicazione").execute()
            return True, len(lista_finale)
        except Exception as e:
            st.error(f"Errore tecnico import: {e}")
            return False, 0