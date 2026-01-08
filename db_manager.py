import pandas as pd
from supabase import create_client, Client # type: ignore
import streamlit as st
from datetime import datetime

class InventarioDB:
    def __init__(self):
        # Caricamento credenziali da secrets.toml
        self.url = st.secrets["SUPABASE_URL"]
        self.key = st.secrets["SUPABASE_KEY"]
        self.supabase: Client = create_client(self.url, self.key)

    def sveglia_database(self):
        """Esegue una query veloce per attivare il database se è in pausa"""
        try:
            # Facciamo una ricerca leggerissima (solo 1 ID) per dare la sveglia
            self.supabase.table('inventario').select("id").limit(1).execute()
            return True, "✅ Database Sveglio e Pronto!"
        except Exception as e:
            return False, f"❌ Errore risveglio: {e}"

    def aggiungi_scatola(self, nome, desc, f_m, ct, cf, mt, mf, bt, bf, zona, ubi, prop):
        d_ora = datetime.now().isoformat()
        data = {
            "nome": nome, "descrizione": desc, "foto_main": f_m,
            "cima_testo": ct, "cima_foto": cf, "centro_testo": mt,
            "centro_foto": mf, "fondo_testo": bt, "fondo_foto": bf,
            "zona": zona, "ubicazione": ubi, "proprietario": prop,
            "data": d_ora
        }
        try:
            self.supabase.table('inventario').insert(data).execute()
            return True
        except Exception as e:
            st.error(f"Errore inserimento: {e}")
            return False

    def visualizza_inventario(self):
        try:
            resp = self.supabase.table('inventario').select("*").order('id', desc=True).execute()
            cols = [
                "id", "nome", "descrizione", "foto_main", "cima_testo", "cima_foto",
                "centro_testo", "centro_foto", "fondo_testo", "fondo_foto", "sinistra_testo",
                "sinistra_foto", "destra_testo", "destra_foto", "zona", "scaffale",
                "ripiano", "ubicazione", "proprietario", "data", "colore_testo",
                "dimensione_carattere", "quantita", "codice_scatola", "categoria",
                "stato", "data_inserimento", "id_ubicazione", "foto_url", "centro_f",
                "cima_f", "fondo_f", "note"
            ]
            return [tuple(r.get(c, None) for c in cols) for r in resp.data]
        except:
            return []

    def cerca_scatola(self, termine):
        """Ricerca ultra-compatibile Nome, Descrizione e Proprietario"""
        try:
            f = f"nome.ilike.%{termine}%,descrizione.ilike.%{termine}%,proprietario.ilike.%{termine}%"
            resp = self.supabase.table('inventario').select("*").filter("or", f"({f})").execute()
            
            cols = [
                "id", "nome", "descrizione", "foto_main", "cima_testo", "cima_foto",
                "centro_testo", "centro_foto", "fondo_testo", "fondo_foto", "sinistra_testo",
                "sinistra_foto", "destra_testo", "destra_foto", "zona", "scaffale",
                "ripiano", "ubicazione", "proprietario", "data", "colore_testo",
                "dimensione_carattere", "quantita", "codice_scatola", "categoria",
                "stato", "data_inserimento", "id_ubicazione", "foto_url", "centro_f",
                "cima_f", "fondo_f", "note"
            ]
            return [tuple(r.get(c, None) for c in cols) for r in resp.data]
        except:
            # Piano B se filter fallisce
            return []

    def elimina_scatola(self, id_s):
        try:
            self.supabase.table('inventario').delete().eq("id", id_s).execute()
            return True
        except:
            return False

    def aggiungi_posizione(self, id_u, zona):
        try:
            self.supabase.table('posizioni').upsert({"id_ubicazione": id_u, "zona": zona}).execute()
        except:
            pass

    def visualizza_posizioni(self):
        try:
            resp = self.supabase.table('posizioni').select("*").order('zona').execute()
            return [(r.get('id_ubicazione'), r.get('zona')) for r in resp.data]
        except:
            return []

    def aggiorna_posizione_scatola(self, id_s, zn, ub):
        try:
            self.supabase.table('inventario').update({"zona": zn, "ubicazione": ub}).eq("id", id_s).execute()
            return True
        except:
            return False

    def elimina_posizione(self, id_u):
        try:
            self.supabase.table('posizioni').delete().eq("id_ubicazione", id_u).execute()
            return True
        except:
            return False