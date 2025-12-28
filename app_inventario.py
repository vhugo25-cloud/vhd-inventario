import streamlit as st
import pandas as pd
from db_manager import InventarioDB
from qrcode import QRCode
import io, os
from fpdf import FPDF
import cloudinary
import cloudinary.uploader
from streamlit_qrcode_scanner import qrcode_scanner

# --- CONFIGURAZIONE CLOUDINARY (GITHUB READY) ---
try:
    if "CLOUDINARY_CLOUD_NAME" in st.secrets:
        cloudinary.config(
            cloud_name = st.secrets["CLOUDINARY_CLOUD_NAME"],
            api_key = st.secrets["CLOUDINARY_API_KEY"],
            api_secret = st.secrets["CLOUDINARY_API_SECRET"],
            secure = True
        )
except:
    pass

# --- ESTETICA E COLORI (Regola d'Oro) ---
st.set_page_config(page_title="Inventario Casa VHD", layout="wide")

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
            ris = cloudinary.uploader.upload(file, folder="VHD_Inventario", public_id=f"{nome}_{tipo}")
            return ris['secure_url']
        except: return ""
    return ""

# --- 🏠 HOME PAGE ---
if scelta == "🏠 Home":
    st.markdown("<h1 class='big-emoji'>🏠</h1>", unsafe_allow_html=True)
    st.title("Inventario Casa VHD")
    inv = db.visualizza_inventario()
    pos = db.visualizza_posizioni()
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📦 Scatole", len(inv))
    c2.metric("📍 Zone", len(set([p[1] for p in pos])) if pos else 0)
    c3.metric("📌 Ubicazioni", len(pos))
    c4.metric("⚠️ Da Allocare", len([s for s in inv if s[10] == "DA DEFINIRE"]))
    
    st.write("---")
    if inv:
        df = pd.DataFrame(inv, columns=["ID", "Nome", "Desc", "Foto", "Cima", "FC", "Centro", "FCE", "Fondo", "FF", "Zona", "Ubi", "Prop"])
        st.subheader("📊 Esporta Dati")
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Inventario')
        st.download_button("📥 Scarica Inventario in Excel", output.getvalue(), "Inventario_VHD.xlsx", "application/vnd.ms-excel")
        st.write("### Ultime 5 scatole inserite")
        st.table(df[["Nome", "Zona", "Ubi", "Prop"]].tail(5))

# --- 🔍 CERCA ED ELIMINA ---
elif scelta == "🔍 Cerca ed Elimina":
    st.markdown("<h1 class='big-emoji'>🔍</h1>", unsafe_allow_html=True)
    st.title("Cerca ed Elimina")
    chiave = st.text_input("Cerca per nome, contenuto o zona...")
    ris = db.cerca_scatola(chiave) if chiave else db.visualizza_inventario()
    
    if ris:
        for r in ris:
            with st.expander(f"📦 {r[1]} | {r[10]} - {r[11]} ({r[12]})"):
                c1, c2 = st.columns([1, 2])
                if r[3]: c1.image(r[3], width=250)
                c2.write(f"**Descrizione:** {r[2]}")
                st.write(f"**Cima:** {r[4]} | **Centro:** {r[6]} | **Fondo:** {r[8]}")
                if st.button(f"🗑️ Elimina definitiva {r[1]}", key=f"del_{r[0]}"):
                    db.elimina_scatola(r[0])
                    st.success("Scatola eliminata!")
                    st.rerun()
    else: st.info("Nessuna scatola trovata.")

# --- 📸 SCANNER QR ---
elif scelta == "📸 Scanner QR":
    st.markdown("<h1 class='big-emoji'>📸</h1>", unsafe_allow_html=True)
    st.title("Scanner QR VHD")
    codice = qrcode_scanner(key='vhd_scanner')
    if codice:
        res = db.cerca_scatola(codice)
        if res:
            r = res[0]
            st.success(f"Scatola Trovata: {r[1]}")
            st.write(f"Posizione: {r[10]} - {r[11]}")
            if r[3]: st.image(r[3], width=400)
        else: st.error("Codice non trovato.")

# --- ➕ NUOVA SCATOLA ---
elif scelta == "➕ Nuova Scatola":
    st.markdown("<h1 class='big-emoji'>➕</h1>", unsafe_allow_html=True)
    st.title("Registra Nuova Scatola")
    with st.form("n_s"):
        nome = st.text_input("Nome Scatola"); desc = st.text_input("Descrizione Generale"); prop = st.selectbox("Proprietario", utenti)
        f_m = st.file_uploader("📸 Foto Esterna", type=['jpg','png'])
        st.write("---")
        c1, c2 = st.columns([2,1])
        ct = c1.text_input("Contenuto Cima"); cf = c2.file_uploader("Foto Cima", key="c")
        mt = c1.text_input("Contenuto Centro"); mf = c2.file_uploader("Foto Centro", key="m")
        bt = c1.text_input("Contenuto Fondo"); bf = c2.file_uploader("Foto Fondo", key="b")
        if st.form_submit_button("REGISTRA SCATOLA"):
            if nome:
                with st.spinner("Salvataggio in corso..."):
                    u1 = upload_foto(f_m, nome, "main")
                    u2 = upload_foto(cf, nome, "cima")
                    u3 = upload_foto(mf, nome, "centro")
                    u4 = upload_foto(bf, nome, "fondo")
                    db.aggiungi_scatola(nome, desc, u1, ct, u2, mt, u3, bt, u4, "DA DEFINIRE", "NON ALLOCATA", prop)
                    st.success("✅ Scatola registrata con successo!"); st.balloons()
            else: st.error("Il nome è obbligatorio!")

# --- 🔄 ALLOCA/SPOSTA ---
elif scelta == "🔄 Alloca/Sposta":
    st.markdown("<h1 class='big-emoji'>🔄</h1>", unsafe_allow_html=True)
    st.title("Alloca o Sposta")
    inv = db.visualizza_inventario(); pos = db.visualizza_posizioni()
    if inv and pos:
        s_sel = st.selectbox("Seleziona Scatola", [f"{s[0]} | {s[1]}" for s in inv])
        p_sel = st.selectbox("Seleziona Destinazione", [f"{p[1]} - {p[0]}" for p in pos])
        if st.button("CONFERMA SPOSTAMENTO"):
            ids = int(s_sel.split(" | ")[0])
            zn, un = p_sel.split(" - ")
            db.aggiorna_posizione_scatola(ids, zn, un)
            st.success(f"✅ Scatola spostata in {zn}!"); st.balloons()
    else: st.warning("Crea prima le scatole e le ubicazioni.")

# --- ⚙️ CONFIGURA MAGAZZINO ---
elif scelta == "⚙️ Configura Magazzino":
    st.markdown("<h1 class='big-emoji'>⚙️</h1>", unsafe_allow_html=True)
    st.title("Configura Magazzino")
    with st.form("p"):
        c1, c2 = st.columns(2)
        s = c1.text_input("Codice Scaffale (ID)"); z = c2.text_input("Zona (Nome)")
        if st.form_submit_button("SALVA POSIZIONE"):
            if s and z:
                db.aggiungi_posizione(s, z); st.rerun()
    
    st.write("---")
    st.subheader("📍 Gestione Ubicazioni")
    cerca_u = st.text_input("Filtra ubicazioni...")
    for p in db.visualizza_posizioni():
        if cerca_u.lower() in p[0].lower() or cerca_u.lower() in p[1].lower():
            col1, col2 = st.columns([4, 1])
            col1.write(f"📍 **{p[1]}** > Scaffale: **{p[0]}**")
            if col2.button("🗑️", key=f"dp_{p[0]}"):
                conn = db.connetti_db(); conn.execute("DELETE FROM POSIZIONI WHERE ID_POSIZIONE=?", (p[0],))
                conn.commit(); conn.close(); st.rerun()

    with st.expander("🛠️ Area Riservata (Reset Totale)"):
        pwd = st.text_input("Password Amministratore", type="password")
        if st.button("⚠️ CANCELLA TUTTO IL DATABASE"):
            if pwd == "233674":
                conn = db.connetti_db(); conn.execute("DELETE FROM inventario"); conn.execute("DELETE FROM POSIZIONI")
                conn.commit(); conn.close(); st.success("RESET COMPLETATO!"); st.balloons()

# --- 🖨️ STAMPA ---
elif scelta == "🖨️ Stampa":
    st.markdown("<h1 class='big-emoji'>🖨️</h1>", unsafe_allow_html=True)
    st.title("Centro Stampa")
    t1, t2 = st.tabs(["📦 Scatole (2xA4)", "📍 Ubicazioni (16xA4)"])
    
    with t1:
        inv = db.visualizza_inventario()
        sel_s = [s for s in inv if st.checkbox(f"Scatola {s[1]}", key=f"st_{s[0]}")]
        if st.button("Scarica PDF Scatole") and sel_s:
            pdf = FPDF()
            for i in range(0, len(sel_s), 2):
                pdf.add_page()
                for idx, s in enumerate(sel_s[i:i+2]):
                    y = 10 if idx == 0 else 150
                    pdf.rect(10, y, 190, 130)
                    pdf.set_font("Arial", 'B', 24); pdf.text(20, y+20, f"SCATOLA: {s[1]}")
                    qr = QRCode(box_size=6); qr.add_data(s[1]); qr.make()
                    img = qr.make_image(); img.save("t.png"); pdf.image("t.png", x=130, y=y+20, w=60)
            st.download_button("Download PDF", pdf.output(dest='S').encode('latin-1'), "scatole_vhd.pdf")
            
    with t2:
        pos = db.visualizza_posizioni()
        sel_p = [p for p in pos if st.checkbox(f"Ubicazione {p[1]}-{p[0]}", key=f"up_{p[0]}")]
        if st.button("Genera PDF Ubicazioni (16 per foglio)") and sel_p:
            pdf = FPDF()
            for i in range(0, len(sel_p), 16):
                pdf.add_page()
                for idx, p in enumerate(sel_p[i:i+16]):
                    col, row = idx % 4, idx // 4
                    x, y = 10 + (col*48), 10 + (row*70)
                    pdf.rect(x, y, 45, 65)
                    pdf.set_font("Arial", 'B', 8); pdf.text(x+2, y+8, f"{p[1][:20]}")
                    pdf.set_font("Arial", 'B', 12); pdf.text(x+2, y+18, f"ID: {p[0]}")
                    qr = QRCode(box_size=3); qr.add_data(p[0]); qr.make()
                    img = qr.make_image(); img.save(f"t_{idx}.png")
                    pdf.image(f"t_{idx}.png", x=x+5, y=y+22, w=35)
                    os.remove(f"t_{idx}.png")
            st.download_button("Scarica PDF Ubicazioni", pdf.output(dest='S').encode('latin-1'), "ubicazioni_vhd.pdf")