import streamlit as st
import pandas as pd
from db_manager import InventarioDB
from qrcode import QRCode
import io, os, time
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

# --- REGOLA D'ORO: FIX COLORI E STILE (PER CELLULARE) ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    [data-testid="stSidebar"] { background-color: #001f3f; }
    [data-testid="stSidebar"] * { color: white !important; }
    
    /* Testo leggibile ovunque */
    h1, h2, h3, p, span, label { color: #002d57 !important; font-family: 'Segoe UI', sans-serif; }
    .stExpander { border: 1px solid #004280; border-radius: 8px; background-color: white !important; }
    
    /* Card Home */
    .stMetric { background-color: white; padding: 15px; border-radius: 10px; border-left: 5px solid #007bff; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); }
    
    /* Testo Piccolo per Data */
    .data-label { font-size: 0.8rem; color: #6c757d !important; font-style: italic; }
    
    .big-emoji { font-size: 3rem !important; margin-bottom: 0; }
    </style>
    """, unsafe_allow_html=True)

db = InventarioDB()
utenti = ["Victor", "Evelyn", "Daniel", "Carly", "Rebby"]
menu = ["🏠 Home", "🔍 Cerca ed Elimina", "📸 Scanner QR", "➕ Nuova Scatola", "🔄 Alloca/Sposta", "⚙️ Configura Magazzino", "🖨️ Stampa"]
scelta = st.sidebar.selectbox("Menu Principale", menu)

# URL Immagine Segnaposto (Placeholder)
NO_PHOTO = "https://res.cloudinary.com/demo/image/upload/v1312461204/sample.jpg" # Puoi sostituire con la tua immagine caricata su Cloudinary

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
        # Nota: abbiamo aggiunto data_creazione alla fine (colonna 13)
        df = pd.DataFrame(inv, columns=["ID", "Nome", "Desc", "Foto", "Cima", "FC", "Centro", "FCE", "Fondo", "FF", "Zona", "Ubicazione", "Proprietario", "Data"])
        st.subheader("📊 Riepilogo Ultime Scatole")
        st.table(df[["Nome", "Zona", "Ubicazione", "Proprietario", "Data"]].tail(10))
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False)
        st.download_button("📥 Scarica Excel Completo", output.getvalue(), "Inventario_VHD.xlsx")
# --- 🔍 CERCA ED ELIMINA (CON TUTTE LE FOTO) ---
elif scelta == "🔍 Cerca ed Elimina":
    st.title("Cerca ed Elimina")
    chiave = st.text_input("Cerca per nome o contenuto...")
    ris = db.cerca_scatola(chiave) if chiave else db.visualizza_inventario()
    if ris:
        for r in ris:
            # Rispettiamo il database aggiornato: r[13] è la data
            data_crea = r[13] if len(r) > 13 else "N.D."
            with st.expander(f"📦 {r[1]} | {r[10]} - {r[11]} | {r[12]}"):
                st.markdown(f"<p class='data-label'>Registrata il: {data_crea}</p>", unsafe_allow_html=True)
                
                # Layout Foto Principale
                c1, c2 = st.columns([1, 2])
                img_main = r[3] if r[3] else NO_PHOTO
                c1.image(img_main, use_container_width=True, caption="Foto Principale")
                
                c2.write(f"**Descrizione:** {r[2]}")
                
                # Visualizzazione dei 3 strati interni
                st.write("---")
                st.subheader("📸 Dettaglio Interno")
                i1, i2, i3 = st.columns(3)
                
                # Strato Cima
                i1.write(f"🔝 **Cima:** {r[4]}")
                i1.image(r[5] if r[5] else NO_PHOTO, use_container_width=True)
                
                # Strato Centro
                i2.write(f"↔️ **Centro:** {r[6]}")
                i2.image(r[7] if r[7] else NO_PHOTO, use_container_width=True)
                
                # Strato Fondo
                i3.write(f"⬇️ **Fondo:** {r[8]}")
                i3.image(r[9] if r[9] else NO_PHOTO, use_container_width=True)
                
                if st.button(f"🗑️ Elimina Scatola", key=f"del_{r[0]}"):
                    db.elimina_scatola(r[0])
                    st.toast(f"Rimossa: {r[1]}", icon="🗑️")
                    time.sleep(1)
                    st.rerun()

# --- 📸 SCANNER QR ---
elif scelta == "📸 Scanner QR":
    st.title("Scanner QR VHD")
    codice = qrcode_scanner(key='vhd_scanner')
    if codice:
        res = db.cerca_scatola(codice)
        if res:
            r = res[0]
            st.success(f"✅ Trovata: {r[1]}")
            st.image(r[3] if r[3] else NO_PHOTO, width=300)
            # Logica Sposta Rapido (mantenuta come nel vecchio codice)
            pos_list = db.visualizza_posizioni()
            dest = [f"{p[1]} - {p[0]}" for p in pos_list]
            nuova = st.selectbox("Nuova Destinazione", dest, key="q_m")
            if st.button("CONFERMA SPOSTAMENTO"):
                zn, un = nuova.split(" - ")
                db.aggiorna_posizione_scatola(r[0], zn, un)
                st.toast("Spostamento completato!", icon="🚚")
                st.balloons()
                time.sleep(1)
                st.rerun()

# --- ➕ NUOVA SCATOLA ---
elif scelta == "➕ Nuova Scatola":
    st.title("Registra Nuova Scatola")
    with st.form("n_s", clear_on_submit=True):
        nome = st.text_input("Nome Scatola (es. Attrezzi Garage)")
        desc = st.text_area("Cosa c'è dentro in generale?")
        prop = st.selectbox("Chi è il proprietario?", utenti)
        f_m = st.file_uploader("📸 Foto Esterna (Principale)", type=['jpg','png'])
        
        st.write("---")
        st.subheader("🔍 Dettaglio per strati (opzionale)")
        c1, c2 = st.columns([2,1])
        ct = c1.text_input("Contenuto Cima")
        cf = c2.file_uploader("Foto Cima", key="f_cima", type=['jpg','png'])
        mt = c1.text_input("Contenuto Centro")
        mf = c2.file_uploader("Foto Centro", key="f_centro", type=['jpg','png'])
        bt = c1.text_input("Contenuto Fondo")
        bf = c2.file_uploader("Foto Fondo", key="f_fondo", type=['jpg','png'])
        
        if st.form_submit_button("REGISTRA SCATOLA"):
            if nome:
                with st.spinner("📦 Caricamento in corso..."):
                    u1 = upload_foto(f_m, nome, "main")
                    u2 = upload_foto(cf, nome, "cima")
                    u3 = upload_foto(mf, nome, "centro")
                    u4 = upload_foto(bf, nome, "fondo")
                    db.aggiungi_scatola(nome, desc, u1, ct, u2, mt, u3, bt, u4, "DA DEFINIRE", "NON ALLOCATA", prop)
                    st.balloons()
                    st.success(f"✅ '{nome}' salvata con successo!")
            else: st.error("⚠️ Il nome è obbligatorio!")

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
            zn, un = p_sel.split(" - ")
            db.aggiorna_posizione_scatola(ids, zn, un)
            st.toast("Spostata!", icon="📍")
            time.sleep(1)
            st.rerun()

# --- ⚙️ CONFIGURA ---
elif scelta == "⚙️ Configura Magazzino":
    st.title("Configura Magazzino")
    t1, t2 = st.tabs(["➕ Singola", "📥 Importazione Massiva"])
    with t1:
        with st.form("p"):
            s = st.text_input("ID Scaffale (es: GAR.1.1)")
            z = st.text_input("Zona (es: Garage)")
            if st.form_submit_button("SALVA"):
                if s and z:
                    db.aggiungi_posizione(s, z)
                    st.toast("Ubicazione aggiunta!")
                    time.sleep(1)
                    st.rerun()
    with t2:
        file_ex = st.file_uploader("Excel Ubicazioni", type=['xlsx'])
        if file_ex and st.button("IMPORTA TUTTO"):
            db.import_posizioni_da_df(pd.read_excel(file_ex))
            st.balloons()
            st.rerun()

# --- 🖨️ STAMPA (CON TASTO RESET) ---
elif scelta == "🖨️ Stampa":
    st.title("Area Stampa Etichette")
    if st.button("🔄 RESET SELEZIONE (Pulisci tutto)"):
        st.rerun()
        
    t1, t2 = st.tabs(["📦 Etichette Scatole", "📍 Etichette Ubicazioni"])
    with t1:
        inv = db.visualizza_inventario()
        sel_s = [s for s in inv if st.checkbox(f"Stampa: {s[1]}", key=f"st_{s[0]}")]
        if st.button("Genera PDF Scatole") and sel_s:
            pdf = FPDF()
            for i in range(0, len(sel_s), 2):
                pdf.add_page()
                for idx, s in enumerate(sel_s[i:i+2]):
                    y = 10 if idx == 0 else 150
                    pdf.rect(10, y, 190, 130)
                    pdf.set_font("Arial", 'B', 45); pdf.set_xy(15, y+15); pdf.cell(0, 20, f"{s[12]}".upper(), ln=True)
                    pdf.set_font("Arial", 'B', 28); pdf.set_xy(15, y+40); pdf.cell(0, 15, f"{s[1]}", ln=True)
                    qr = QRCode(box_size=5); qr.add_data(s[1]); qr.make()
                    img = qr.make_image(); img.save("t.png"); pdf.image("t.png", x=125, y=y+35, w=65)
            st.download_button("📥 Scarica PDF", pdf.output(dest='S').encode('latin-1'), "etichette_vhd.pdf")

    with t2:
        pos_st = db.visualizza_posizioni()
        sel_p = [p for p in pos_st if st.checkbox(f"Ubi {p[1]} - {p[0]}", key=f"up_{p[0]}")]
        if st.button("Genera PDF Ubicazioni") and sel_p:
            pdf = FPDF()
            for i in range(0, len(sel_p), 16):
                pdf.add_page()
                for idx, p in enumerate(sel_p[i:i+16]):
                    col, row = idx % 4, idx // 4
                    x, y = 10 + (col*48), 10 + (row*70)
                    pdf.rect(x, y, 45, 65)
                    pdf.set_font("Arial", 'B', 8); pdf.text(x+2, y+8, f"{p[1]}")
                    pdf.set_font("Arial", 'B', 12); pdf.text(x+2, y+18, f"ID: {p[0]}")
                    qr = QRCode(box_size=3); qr.add_data(p[0]); qr.make()
                    img = qr.make_image(); img.save("t_u.png"); pdf.image("t_u.png", x=x+5, y=y+22, w=35)
            st.download_button("📥 Scarica PDF", pdf.output(dest='S').encode('latin-1'), "ubicazioni_vhd.pdf")
                    
