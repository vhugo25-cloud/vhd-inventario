import streamlit as st
import pandas as pd
from db_manager import InventarioDB
from qrcode import QRCode
import io, os
from fpdf import FPDF
from streamlit_qrcode_scanner import qrcode_scanner
import cloudinary
import cloudinary.uploader

# --- CONFIGURAZIONE CLOUDINARY (Usa i Secrets salvati su Streamlit) ---
try:
    cloudinary.config(
        cloud_name = st.secrets["CLOUDINARY_CLOUD_NAME"],
        api_key = st.secrets["CLOUDINARY_API_KEY"],
        api_secret = st.secrets["CLOUDINARY_API_SECRET"],
        secure = True
    )
except Exception as e:
    st.warning("⚠️ Configurazione Cloudinary non ancora attiva nei Secrets.")

# --- CONFIGURAZIONE ESTETICA ---
st.set_page_config(page_title="Inventario Casa VHD", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    h1, h2, h3 { color: #004280 !important; font-family: 'Segoe UI', sans-serif; }
    [data-testid="stSidebar"] { background-color: #001f3f; color: white; }
    [data-testid="stSidebar"] * { color: white !important; }
    .stButton>button { background-color: #007BFF; color: white; border-radius: 8px; font-weight: bold; width: 100%; height: 3em; border: none; }
    .stButton>button:hover { background-color: #0056b3; }
    </style>
    """, unsafe_allow_html=True)

db = InventarioDB()

# Liste personalizzate richieste
utenti = ["Victor", "Evelyn", "Daniel", "Carly", "Rebby"]
menu = ["🏠 Home", "🔍 Cerca ed Elimina", "📸 Scanner QR", "➕ Nuova Scatola", "🔄 Alloca/Sposta", "⚙️ Configura Magazzino", "🖨️ Stampa"]
scelta = st.sidebar.selectbox("Menu Principale", menu)

def salva_foto_cloudinary(foto, nome_scatola, tipo):
    if foto:
        try:
            # Carica la foto su Cloudinary nella cartella VHD_Inventario
            risultato = cloudinary.uploader.upload(
                foto, 
                folder = "VHD_Inventario",
                public_id = f"{nome_scatola}_{tipo}",
                overwrite = True,
                resource_type = "image"
            )
            return risultato['secure_url'] # Restituisce il link internet della foto
        except Exception as e:
            st.error(f"Errore Cloudinary: {e}")
            return ""
    return ""

# --- LOGICA PAGINE ---

if scelta == "🏠 Home":
    st.title("🏠 Inventario Casa VHD")
    inv = db.visualizza_inventario()
    st.write("---")
    c1, c2, c3 = st.columns(3)
    with c1: st.metric("📦 Scatole Totali", len(inv))
    with c2: st.metric("📍 Postazioni", len(db.visualizza_posizioni()))
    with c3: st.metric("⚠️ Da Allocare", len([s for s in inv if s[10] == "DA DEFINIRE"]))
    st.write("---")
    if inv:
        st.subheader("📋 Ultime Scatole Registrate")
        df = pd.DataFrame([list(s[1:3]) + [s[10], s[11], s[12]] for s in inv[-10:]], 
                          columns=["Nome", "Descrizione", "Zona", "Ubicazione", "Proprietario"])
        st.table(df)

elif scelta == "🔍 Cerca ed Elimina":
    st.title("🔍 Ricerca Inventario")
    chiave = st.text_input("Cerca per nome o contenuto...")
    ris = db.cerca_scatola(chiave) if chiave else db.visualizza_inventario()
    for r in ris:
        with st.expander(f"📦 {r[1]} | Posizione: {r[10]}-{r[11]}"):
            c1, c2 = st.columns([1, 2])
            # Se r[3] è un link (Cloudinary) lo mostra, altrimenti mostra avviso
            if r[3]: 
                c1.image(r[3], width=250)
            else:
                c1.info("📸 Nessuna foto")
            
            c2.write(f"**Descrizione:** {r[2]}")
            c2.write(f"**Proprietario:** {r[12]}")
            
            s1, s2, s3 = st.columns(3)
            if r[5]: s1.image(r[5], caption=f"Cima: {r[4]}")
            if r[7]: s2.image(r[7], caption=f"Centro: {r[6]}")
            if r[9]: s3.image(r[9], caption=f"Fondo: {r[8]}")
            
            if st.button("🗑️ ELIMINA SCATOLA", key=f"del_{r[0]}"):
                db.elimina_scatola(r[0]); st.rerun()

elif scelta == "➕ Nuova Scatola":
    st.title("➕ Registra Nuova Scatola")
    with st.form("f_scatola"):
        c_top1, c_top2 = st.columns(2)
        nome = c_top1.text_input("Nome/Codice Scatola")
        prop = c_top2.selectbox("Proprietario", utenti)
        desc = st.text_area("Cosa c'è dentro?")
        f_main = st.file_uploader("Foto Esterna Scatola", type=["jpg","png"])
        
        st.subheader("📦 Dettaglio Strati (Opzionale)")
        c1, c2 = st.columns(2)
        c_t = c1.text_input("Cima"); c_f = c2.file_uploader("Foto Cima", key="fc")
        m_t = c1.text_input("Centro"); m_f = c2.file_uploader("Foto Centro", key="fm")
        b_t = c1.text_input("Fondo"); b_f = c2.file_uploader("Foto Fondo", key="fb")
        
        if st.form_submit_button("REGISTRA SCATOLA"):
            if nome:
                with st.spinner("Salvataggio nel Cloud in corso..."):
                    pm = salva_foto_cloudinary(f_main, nome, "main")
                    pc = salva_foto_cloudinary(c_f, nome, "cima")
                    pmid = salva_foto_cloudinary(m_f, nome, "centro")
                    pf = salva_foto_cloudinary(b_f, nome, "fondo")
                    
                    db.aggiungi_scatola(nome, desc, pm, c_t, pc, m_t, pmid, b_t, pf, "DA DEFINIRE", "NON ALLOCATA", prop)
                    st.success(f"Scatola {nome} salvata correttamente!")
            else:
                st.error("Inserisci almeno il nome della scatola!")

# --- LE ALTRE PAGINE (Scanner, Alloca, Configura, Stampa) ---
# Seguono la stessa logica del database già presente nel tuo db_manager.py
elif scelta == "📸 Scanner QR":
    st.title("📸 Scanner QR Operativo")
    dato = qrcode_scanner(key='scanner_vhd')
    if dato:
        res = db.cerca_scatola(dato)
        if res:
            for r in res:
                st.subheader(f"📦 Scatola: {r[1]}")
                if r[3]: st.image(r[3], width=300)
                st.write(f"**Contenuto:** {r[2]}")
                st.info(f"📍 Posizione: {r[10]} - {r[11]}")

elif scelta == "⚙️ Configura Magazzino":
    st.title("⚙️ Setup Postazioni")
    with st.form("c_mag"):
        col_s, col_z = st.columns(2)
        scaf = col_s.text_input("Codice Scaffale (es. A1)")
        zona = col_z.text_input("Nome Zona (es. Garage)")
        if st.form_submit_button("Salva Postazione"):
            if scaf and zona:
                db.aggiungi_posizione(scaf, zona)
                st.success("Postazione aggiunta!")

elif scelta == "🖨️ Stampa":
    st.title("🖨️ Centro Stampa")
    st.write("Seleziona le scatole per generare i QR Code in PDF.")
    # (Logica stampa PDF come prima)