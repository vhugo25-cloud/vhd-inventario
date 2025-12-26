import streamlit as st
import pandas as pd
from db_manager import InventarioDB
import io, os
import cloudinary
import cloudinary.uploader
from streamlit_qrcode_scanner import qrcode_scanner

# --- CONFIGURAZIONE CLOUDINARY ---
try:
    # Online userà i Secrets di Streamlit Cloud
    cloudinary.config(
        cloud_name = st.secrets["CLOUDINARY_CLOUD_NAME"],
        api_key = st.secrets["CLOUDINARY_API_KEY"],
        api_secret = st.secrets["CLOUDINARY_API_SECRET"],
        secure = True
    )
except Exception as e:
    st.warning("⚠️ Configurazione Cloudinary non rilevata (normale se sei su PC senza file secrets.toml)")

# --- ESTETICA ---
st.set_page_config(page_title="Inventario Casa VHD", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    h1, h2, h3 { color: #004280 !important; font-family: 'Segoe UI', sans-serif; }
    [data-testid="stSidebar"] { background-color: #001f3f; color: white; }
    [data-testid="stSidebar"] * { color: white !important; }
    .stButton>button { background-color: #007BFF; color: white; border-radius: 8px; font-weight: bold; width: 100%; height: 3em; border: none; }
    </style>
    """, unsafe_allow_html=True)

db = InventarioDB()

# Liste personalizzate
utenti = ["Victor", "Evelyn", "Daniel", "Carly", "Rebby"]
menu = ["🏠 Home", "🔍 Cerca ed Elimina", "📸 Scanner QR", "➕ Nuova Scatola", "🔄 Alloca/Sposta", "⚙️ Configura Magazzino", "🖨️ Stampa"]
scelta = st.sidebar.selectbox("Menu Principale", menu)

# --- AREA AMMINISTRATORE (PASSWORD: 233674) ---
st.sidebar.write("---")
st.sidebar.subheader("🛠️ Area Riservata")
pwd_input = st.sidebar.text_input("Inserisci Password Admin", type="password")

if st.sidebar.button("⚠️ RESET TOTALE DATABASE"):
    if pwd_input == "233674":
        try:
            conn = db.connetti_db()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM inventario")
            cursor.execute("DELETE FROM posizioni")
            conn.commit()
            st.sidebar.success("✅ Database svuotato correttamente!")
            st.rerun()
        except Exception as e:
            st.sidebar.error(f"Errore: {e}")
    else:
        st.sidebar.error("❌ Password errata!")

# --- FUNZIONE FOTO ---
def salva_foto_cloudinary(foto, nome_scatola, tipo):
    if foto:
        try:
            risultato = cloudinary.uploader.upload(
                foto, 
                folder = "VHD_Inventario",
                public_id = f"{nome_scatola}_{tipo}",
                overwrite = True
            )
            return risultato['secure_url']
        except:
            return ""
    return ""

# --- LOGICA PAGINE ---

if scelta == "🏠 Home":
    st.title("🏠 Inventario Casa VHD")
    inv = db.visualizza_inventario()
    pos_list = db.visualizza_posizioni()
    
    c1, c2, c3 = st.columns(3)
    with c1: st.metric("📦 Scatole Totali", len(inv))
    with c2: st.metric("📍 Postazioni", len(pos_list))
    with c3: st.metric("⚠️ Da Allocare", len([s for s in inv if s[10] == "DA DEFINIRE"]))
    
    st.write("---")
    
    if inv:
        st.subheader("📥 Esporta Dati")
        df = pd.DataFrame(inv, columns=["ID", "Nome", "Descrizione", "URL Foto", "Cima", "F_Cima", "Centro", "F_Centro", "Fondo", "F_Fondo", "Zona", "Ubicazione", "Proprietario"])
        
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Inventario')
        
        st.download_button(
            label="📊 Scarica Inventario in Excel",
            data=buffer.getvalue(),
            file_name="Inventario_VHD.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        st.write("### Ultime scatole inserite:")
        st.table(df[["Nome", "Zona", "Proprietario"]].tail(5))

elif scelta == "🔍 Cerca ed Elimina":
    st.title("🔍 Ricerca ed Elimina")
    chiave = st.text_input("Cerca per nome o contenuto...")
    ris = db.cerca_scatola(chiave) if chiave else db.visualizza_inventario()
    
    for r in ris:
        with st.expander(f"📦 {r[1]} | {r[10]}"):
            c1, c2 = st.columns([1, 2])
            if r[3] and r[3].startswith("http"):
                c1.image(r[3], width=250)
            c2.write(f"**Proprietario:** {r[12]}")
            c2.write(f"**Descrizione:** {r[2]}")
            if st.button("🗑️ Elimina Scatola", key=f"del_{r[0]}"):
                db.elimina_scatola(r[0])
                st.rerun()

elif scelta == "➕ Nuova Scatola":
    st.title("➕ Aggiungi Scatola")
    with st.form("nuova_scatola"):
        nome = st.text_input("Nome Scatola")
        prop = st.selectbox("Proprietario", utenti)
        desc = st.text_area("Cosa contiene?")
        foto = st.file_uploader("Scatta o seleziona foto", type=["jpg", "png"])
        
        if st.form_submit_button("REGISTRA"):
            if nome:
                with st.spinner("Caricamento immagine..."):
                    url = salva_foto_cloudinary(foto, nome, "main")
                    db.aggiungi_scatola(nome, desc, url, "", "", "", "", "", "", "DA DEFINIRE", "NON ALLOCATA", prop)
                    st.success(f"Scatola {nome} registrata!")
            else:
                st.error("Il nome è obbligatorio!")

elif scelta == "⚙️ Configura Magazzino":
    st.title("⚙️ Configura Magazzino")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📍 Aggiungi Nuova Zona")
        nuova_zona = st.text_input("Zona (es. Garage, Cantina)")
        nuova_ubi = st.text_input("Dettaglio (es. Scaffale A, Mobile 1)")
        if st.button("REGISTRA POSIZIONE"):
            if nuova_zona and nuova_ubi:
                db.aggiungi_posizione(nuova_zona, nuova_ubi)
                st.success("Posizione registrata!")
                st.rerun()
    with col2:
        st.subheader("📋 Posizioni Attuali")
        posizioni = db.visualizza_posizioni()
        if posizioni:
            for p in posizioni:
                st.write(f"• **{p[1]}**: {p[2]}")
        else:
            st.info("Nessuna posizione configurata.")

elif scelta == "🔄 Alloca/Sposta":
    st.title("🔄 Alloca o Sposta Scatole")
    inv = db.visualizza_inventario()
    pos = db.visualizza_posizioni()
    if inv and pos:
        scatola_sel = st.selectbox("Seleziona Scatola", [f"{s[0]} - {s[1]}" for s in inv])
        dest_sel = st.selectbox("Destinazione", [f"{p[1]} | {p[2]}" for p in pos])
        if st.button("CONFERMA SPOSTAMENTO"):
            id_s = int(scatola_sel.split(" - ")[0])
            z, u = dest_sel.split(" | ")
            db.aggiorna_posizione_scatola(id_s, z, u)
            st.success("Spostato!")
            st.rerun()
    else:
        st.warning("Assicurati di avere sia scatole che posizioni create!")