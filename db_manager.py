import pandas as pd
from supabase import create_client, Client
import streamlit as st
import cloudinary
import cloudinary.uploader

# --- CONFIGURAZIONE CLOUDINARY ---
cloudinary.config(
    cloud_name = st.secrets["CLOUDINARY_CLOUD_NAME"],
    api_key = st.secrets["CLOUDINARY_API_KEY"],
    api_secret = st.secrets["CLOUDINARY_API_SECRET"],
    secure = True
)

class InventarioDB:
    def __init__(self):
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
            res = self.supabase.table("inventario").select("*").order("id").execute()
            return res.data
        except:
            return []

    def visualizza_posizioni(self):
        try:
            res = self.supabase.table("posizioni").select("*").order("zona").execute()
            return res.data
        except:
            return []

    def upload_foto(self, file, nome_scatola, posizione):
        try:
            if file is None:
                return None
            folder_path = f"vhd_wms/{nome_scatola}"
            upload_result = cloudinary.uploader.upload(
                file,
                folder=folder_path,
                public_id=f"{nome_scatola}_{posizione}",
                overwrite=True,
                resource_type="image"
            )
            return upload_result.get('secure_url')
        except Exception as e:
            st.error(f"Errore caricamento Cloudinary ({posizione}): {e}")
            return None

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
        except Exception as e:
            st.error(f"Errore inserimento: {e}")
            return False

    def aggiorna_dati_scatola(self, id_scatola, nome, desc, prop, ct, mt, bt, f_main=None, f_cima=None, f_cent=None, f_fond=None):
        try:
            dati = {
                "nome": nome,
                "descrizione": desc,
                "proprietario": prop,
                "cima_testo": ct,
                "centro_testo": mt,
                "fondo_testo": bt
            }
            if f_main: dati["foto_main"] = f_main
            if f_cima: dati["cima_foto"] = f_cima
            if f_cent: dati["centro_foto"] = f_cent
            if f_fond: dati["fondo_foto"] = f_fond
            self.supabase.table("inventario").update(dati).eq("id", id_scatola).execute()
            return True
        except Exception as e:
            st.error(f"Errore aggiornamento: {e}")
            return False

    # --- FUNZIONE AGGIORNATA PER LO SMART SCAN ---
    def aggiorna_posizione_scatola(self, id_scatola, zona, ubi):
        """Aggiorna zona e ubicazione di una scatola nel database"""
        try:
            # Puliamo i testi per evitare errori di spazi bianchi
            nuova_zona = str(zona).strip()
            nuova_ubi = str(ubi).strip()
            
            self.supabase.table("inventario").update({
                "zon": nuova_zona, 
                "ubi": nuova_ubi
            }).eq("id", id_scatola).execute()
            return True
        except Exception as e:
            st.error(f"Errore DB Spostamento: {e}")
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
            self.supabase.table("posizioni").upsert({"id_ubicazione": id_u, "zona": zona}).execute()
            return True
        except:
            return False

    def import_posizioni_da_df(self, df):
        try:
            df.columns = [str(c).lower().strip() for c in df.columns]
            df = df.rename(columns={'id scaffale': 'id_ubicazione', 'id': 'id_ubicazione', 'zona': 'zona'})
            lista_finale = []
            for _, r in df.iterrows():
                lista_finale.append({
                    "id_ubicazione": str(r['id_ubicazione']).strip().upper(),
                    "zona": str(r['zona']).strip()
                })
            self.supabase.table("posizioni").upsert(lista_finale, on_conflict="id_ubicazione").execute()
            return True, len(lista_finale)
        except Exception as e:
            st.error(f"Errore tecnico import: {e}")
            return False, 0

    def reset_totale_inventario(self):
        try:
            self.supabase.table("inventario").delete().neq("id", -1).execute()
            return True
        except:
            return False

    def reset_totale_posizioni(self):
        try:
            self.supabase.table("posizioni").delete().neq("id_ubicazione", "NONE_XYZ").execute()
            return True
        except:
            return False
        