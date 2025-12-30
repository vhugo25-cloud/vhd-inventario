import streamlit as st
import pandas as pd
from db_manager import InventarioDB
from qrcode import QRCode
import io, os
from fpdf import FPDF
from datetime import datetime
import cloudinary
import cloudinary.uploader
from streamlit_qrcode_scanner import qrcode_scanner

# --- CONFIGURAZIONE CLOUDINARY ---
try:
    if "CLOUDINARY_CLOUD_NAME" in st.secrets:
        cloudinary.config(
            cloud_name = st.secrets["CLOUDINARY_CLOUD_NAME"],
            api_key = st.secrets["CLOUDINARY_API_KEY"],
            api_secret = st.secrets["CLOUDINARY_API_SECRET"],
            secure = True
        )
except: pass

st.set_page_config(page_title="Inventario Casa VHD", layout="wide")

# --- ESTETICA BLU NOTTE ---
st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    [data-testid="stSidebar"] { background-color: #001f3f; }
    [data-testid="stSidebar"] * { color: white !important; font-size: 1.1rem; }
    h1, h2 { color: #004280; font-family: 'Segoe UI'; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border-left: 5px solid #007bff; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); }
    .big-emoji { font-size: 3rem !important; margin-bottom: 0; }
    </style>
    """, unsafe_allow_html=True)

db = InventarioDB()
utenti = ["Victor", "Evelyn", "Daniel", "Carly", "Rebby"]
menu = ["🏠 Home", "🔍 Cerca ed Elimina", "📸 Scanner QR", "➕ Nuova Scatola", "🔄 Alloca/Sposta", "⚙️ Configura Magazzino", "🖨️ Stampa"]
scelta = st.sidebar.selectbox("Menu Principale", menu)

def upload_foto(file, nome, tipo):
    if file:
        try:
            prefisso = (nome[:3].upper()) if len(nome) >= 3 else "BOX"
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nome_unico = f"{prefisso}_{tipo}_{timestamp}"
            ris = cloudinary.uploader.upload(file, folder="VHD_Inventario", public_id=nome_unico)
            return ris['secure_url']
        except: return ""
    return ""

# --- 🏠 HOME ---
if scelta == "🏠 Home":
    st.markdown("<h1 class='big-emoji'>🏠</h1>", unsafe_allow_html=True)
    st.title("Inventario Casa VHD")
    inv = db.visualizza_inventario()
    pos = db.visualizza_posizioni()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📦 Scatole", len(inv))
    c2.metric("📍 Zone", len(set([p[1] for p in pos])) if pos else 0)
    c3.metric("📌 Ubicazioni", len(pos))
    c4.metric("⚠️ Da Allocare", len([s for s in inv if s[11] == "NON ALLOCATA"]))
    
    st.write("---")
    if inv:
        df = pd.DataFrame(inv, columns=["ID", "Nome", "Desc", "Foto", "Cima", "FC", "Centro", "FCE", "Fondo", "FF", "Zona", "Ubicazione", "Proprietario"])
        st.subheader("📊 Riepilogo Ultime Scatole")
        st.table(df[["Nome", "Zona", "Ubicazione", "Proprietario"]].tail(10))
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False)
        st.download_button("📥 Scarica Excel Completo", output.getvalue(), "Inventario_VHD.xlsx")

# --- 🔍 CERCA ED ELIMINA ---
elif scelta == "🔍 Cerca ed Elimina":
    st.title("Cerca ed Elimina")
    chiave = st.text_input("Cerca per nome o contenuto...")
    ris = db.cerca_scatola(chiave) if chiave else db.visualizza_inventario()
    if ris:
        for r in ris:
            with st.expander(f"📦 {r[1]} | Posizione: {r[10]} - {r[11]} | Prop: {r[12]}"):
                c1, c2 = st.columns([1, 2])
                if r[3]: 
                    try:
                        c1.image(r[3], width=300)
                    except:
                        c1.info("📸 Anteprima non disponibile")
                
                c2.write(f"**Descrizione:** {r[2]}")
                c2.write(f"**Contenuto:** Cima: {r[4]} | Centro: {r[6]} | Fondo: {r[8]}")
                if st.button(f"🗑️ Elimina {r[1]}", key=f"del_{r[0]}"):
                    db.elimina_scatola(r[0])
                    st.success(f"✅ Scatola '{r[1]}' eliminata con successo!")
                    st.rerun()
# --- 📸 SCANNER QR ---
elif scelta == "📸 Scanner QR":
    st.markdown("<h1 class='big-emoji'>📸</h1>", unsafe_allow_html=True)
    st.title("Scanner QR VHD")
    codice = qrcode_scanner(key='vhd_scanner')
    if codice:
        res = db.cerca_scatola(codice)
        if res:
            r = res[0]
            st.success(f"✅ Trovata: {r[1]}")
            st.write(f"Posizione attuale: **{r[10]} - {r[11]}**")
            if r[3]: st.image(r[3], width=400)
            st.write("---")
            st.subheader("🔄 Azione Rapida: Sposta")
            pos_list = db.visualizza_posizioni()
            if pos_list:
                dest = [f"{p[1]} - {p[0]}" for p in pos_list]
                nuova = st.selectbox("Nuova Destinazione", dest, key="q_m")
                if st.button("CONFERMA SPOSTAMENTO"):
                    zn, un = nuova.split(" - ")
                    db.aggiorna_posizione_scatola(r[0], zn, un)
                    st.success(f"✅ Spostamento di '{r[1]}' completato!")
                    st.balloons()
        else:
            st.warning(f"⚠️ Nessuna scatola trovata con codice: {codice}")
 
# --- ➕ NUOVA SCATOLA ---
elif scelta == "➕ Nuova Scatola":
    st.title("Registra Nuova Scatola")
    with st.form("n_s"):
        nome = st.text_input("Nome Scatola")
        desc = st.text_area("Descrizione Generale")
        prop = st.selectbox("Proprietario", utenti)
        f_m = st.file_uploader("📸 Foto Esterna Principale", type=['jpg','png'])
        
        st.write("---")
        st.subheader("📦 Dettaglio Strati Interni")
        c1, c2 = st.columns([2,1])
        ct = c1.text_input("Contenuto Cima (Sopra)")
        cf = c2.file_uploader("Foto Cima", key="f_cima", type=['jpg','png'])
        mt = c1.text_input("Contenuto Centro (Mezzo)")
        mf = c2.file_uploader("Foto Centro", key="f_centro", type=['jpg','png'])
        bt = c1.text_input("Contenuto Fondo (Sotto)")
        bf = c2.file_uploader("Foto Fondo", key="f_fondo", type=['jpg','png'])
        
        if st.form_submit_button("REGISTRA SCATOLA COMPLETA"):
            if nome:
                with st.spinner("📦 Salvataggio e caricamento foto su Cloudinary..."):
                    u1 = upload_foto(f_m, nome, "main")
                    u2 = upload_foto(cf, nome, "cima")
                    u3 = upload_foto(mf, nome, "centro")
                    u4 = upload_foto(bf, nome, "fondo")
                    db.aggiungi_scatola(nome, desc, u1, ct, u2, mt, u3, bt, u4, "DA DEFINIRE", "NON ALLOCATA", prop)
                    st.success(f"✅ Ottimo! La scatola '{nome}' è stata salvata correttamente.")
                    st.balloons()
            else:
                st.error("⚠️ Inserisci almeno il Nome della scatola!")

# --- 🔄 ALLOCA/SPOSTA ---
elif scelta == "🔄 Alloca/Sposta":
    st.title("Alloca o Sposta")
    inv = db.visualizza_inventario()
    pos = db.visualizza_posizioni()
    if inv and pos:
        s_sel = st.selectbox("Seleziona Scatola", [f"{s[0]} | {s[1]}" for s in inv])
        p_sel = st.selectbox("Destinazione", [f"{p[1]} - {p[0]}" for p in pos])
        if st.button("CONFERMA SPOSTAMENTO"):
            ids = int(s_sel.split(" | ")[0])
            nome_s = s_sel.split(" | ")[1]
            zn, un = p_sel.split(" - ")
            db.aggiorna_posizione_scatola(ids, zn, un)
            st.success(f"✅ Fatto! '{nome_s}' spostata in {zn} ({un}).")
            st.balloons()

# --- ⚙️ CONFIGURA ---
elif scelta == "⚙️ Configura Magazzino":
    st.title("Configura Magazzino")
    t1, t2 = st.tabs(["➕ Singola", "📥 Importazione Massiva"])
    
    with t1:
        with st.form("p"):
            s = st.text_input("ID Scaffale / Ubicazione (es: GAR.1.1)")
            z = st.text_input("Zona (es: Garage)")
            if st.form_submit_button("SALVA UBICAZIONE"):
                if s and z:
                    esistenti = [p[0] for p in db.visualizza_posizioni()]
                    if s in esistenti:
                        st.error(f"❌ Errore: L'ubicazione {s} esiste già!")
                    else:
                        db.aggiungi_posizione(s, z)
                        st.success(f"✅ Ubicazione {s} salvata correttamente!")
                        st.rerun()
                else:
                    st.warning("⚠️ Compila entrambi i campi.")

    with t2:
        st.subheader("Importazione Massiva")
        file_ex = st.file_uploader("Seleziona file Excel", type=['xlsx'])
        if file_ex:
            df_im = pd.read_excel(file_ex)
            if st.button("IMPORTA TUTTO DA EXCEL"):
                with st.spinner("📥 Caricamento in corso..."):
                    db.import_posizioni_da_df(df_im)
                    st.success(f"✅ Successo! Caricate {len(df_im)} nuove ubicazioni.")
                    st.rerun()

    st.markdown("---")
    st.subheader("💾 Backup Sicurezza")
    try:
        with open("magazzino_casa.db", "rb") as f:
            st.download_button("📥 Scarica Database Backup (.db)", f, "magazzino_casa.db")
    except: st.warning("⚠️ Database non trovato.")           
    
    st.write("---")
    st.subheader("🗑️ Elimina Singola Ubicazione")
    with st.form("elimina_ubi"):
        ubi_da_del = st.text_input("ID da eliminare")
        if st.form_submit_button("ELIMINA ORA"):
            if ubi_da_del:
                db.elimina_posizione(ubi_da_del)
                st.success(f"✅ Ubicazione {ubi_da_del} rimossa.")
                st.rerun()

    st.write("---")
    with st.expander("🚨 RESET TOTALE"):
        pwd = st.text_input("Password", type="password")
        if st.button("AZZERA TUTTO"):
            if pwd == "233674":
                conn = db.connetti_db()
                conn.execute("DELETE FROM inventario"); conn.execute("DELETE FROM POSIZIONI")
                conn.commit()
                st.error("💥 Database azzerato!")
                st.rerun()

# --- 🖨️ STAMPA ---
elif scelta == "🖨️ Stampa":
    st.title("Stampa Etichette")
    # ... (Il codice di stampa rimane identico al tuo originale) ...                    