import streamlit as st
import pandas as pd
from db_manager import InventarioDB
from qrcode import QRCode
import io, os
from fpdf import FPDF
from streamlit_qrcode_scanner import qrcode_scanner

# --- CONFIGURAZIONE ESTETICA ---
st.set_page_config(page_title="Inventario Casa VHD", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    h1, h2, h3 { color: #004280 !important; font-family: 'Segoe UI', sans-serif; }
    [data-testid="stSidebar"] { background-color: #001f3f; color: white; }
    [data-testid="stSidebar"] * { color: white !important; }
    [data-testid="stMetricValue"] { font-size: 45px !important; font-weight: bold; color: #007BFF !important; }
    [data-testid="stMetricLabel"] { font-size: 22px !important; color: #333 !important; font-weight: 600 !important; }
    .stButton>button { background-color: #007BFF; color: white; border-radius: 8px; font-weight: bold; height: 3em; width: 100%; border: none; }
    .stButton>button:hover { background-color: #0056b3; color: white; }
    </style>
    """, unsafe_allow_html=True)

db = InventarioDB()
if not os.path.exists("foto_scatole"): os.makedirs("foto_scatole")

utenti = ["Victor", "Evelyn", "Daniel", "Carly", "Rebby"]
menu = ["🏠 Home", "🔍 Cerca ed Elimina", "📸 Scanner QR", "➕ Nuova Scatola", "🔄 Alloca/Sposta", "⚙️ Configura Magazzino", "🖨️ Stampa"]
scelta = st.sidebar.selectbox("Menu Principale", menu)

def salva_foto(foto, nome_scatola, tipo):
    if foto:
        path = f"foto_scatole/{nome_scatola}_{tipo}.jpg"
        with open(path, "wb") as f: f.write(foto.getbuffer())
        return path
    return ""

# --- LOGICA PAGINE ---

if scelta == "🏠 Home":
    st.title("🏠 Inventario Casa VHD")
    inv = db.visualizza_inventario()
    scaff = db.visualizza_posizioni()
    st.write("---")
    c1, c2, c3 = st.columns(3)
    with c1: st.metric("📦 Scatole Totali", len(inv))
    with c2: st.metric("📍 Postazioni", len(scaff))
    with c3: st.metric("⚠️ Da Allocare", len([s for s in inv if s[10] == "DA DEFINIRE"]))
    st.write("---")
    if inv:
        st.subheader("📋 Ultime Scatole Registrate")
        df = pd.DataFrame([list(s[1:3]) + [s[10], s[11], s[12]] for s in inv[-10:]], 
                          columns=["Nome", "Descrizione", "Zona", "Ubicazione", "Proprietario"])
        st.table(df)

elif scelta == "📸 Scanner QR":
    st.title("📸 Scanner QR Operativo")
    dato = qrcode_scanner(key='scanner_vhd_final')
    if dato:
        st.success(f"Scansione completata: {dato}")
        res = db.cerca_scatola(dato)
        if res:
            for r in res:
                id_db, nome, desc, f_main, z_att, u_att, prop = r[0], r[1], r[2], r[3], r[10], r[11], r[12]
                c_inf, c_fot = st.columns([2, 1])
                with c_inf:
                    st.subheader(f"📦 {nome}")
                    st.write(f"**Contenuto:** {desc}")
                    st.write(f"**👤 Proprietario:** {prop}")
                    st.info(f"📍 Posizione Attuale: {z_att} - {u_att}")
                with c_fot:
                    if f_main: st.image(f_main, use_container_width=True)
                st.divider()
                st.subheader("🔄 Sposta Scatola")
                col_z, col_u = st.columns(2)
                nuova_z = col_z.text_input("Nuova Zona", value=z_att, key=f"sz_{id_db}")
                nuova_u = col_u.text_input("Nuova Ubicazione", value=u_att, key=f"su_{id_db}")
                if st.button("Conferma Spostamento", key=f"sb_{id_db}"):
                    conn = db.connetti_db()
                    conn.execute("UPDATE inventario SET zona = ?, ubicazione = ? WHERE id = ?", (nuova_z, nuova_u, id_db))
                    conn.commit(); conn.close()
                    st.success("Posizione Aggiornata!"); st.rerun()

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
                pm, pc, pmid, pf = salva_foto(f_main, nome, "main"), salva_foto(c_f, nome, "cima"), salva_foto(m_f, nome, "centro"), salva_foto(b_f, nome, "fondo")
                db.aggiungi_scatola(nome, desc, pm, c_t, pc, m_t, pmid, b_t, pf, "DA DEFINIRE", "NON ALLOCATA", prop)
                st.success(f"Scatola {nome} salvata!")

elif scelta == "🔄 Alloca/Sposta":
    st.title("🔄 Posizionamento Manuale")
    for s in db.visualizza_inventario():
        with st.expander(f"📦 {s[1]} | {s[10]} - {s[11]}"):
            c1, c2 = st.columns(2)
            nz = c1.text_input("Cambia Zona", value=s[10], key=f"az_{s[0]}")
            nu = c2.text_input("Cambia Ubicazione", value=s[11], key=f"au_{s[0]}")
            if st.button("Aggiorna Posizione", key=f"ab_{s[0]}"):
                conn = db.connetti_db()
                conn.execute("UPDATE inventario SET zona = ?, ubicazione = ? WHERE id = ?", (nz, nu, s[0]))
                conn.commit(); conn.close(); st.rerun()

elif scelta == "🔍 Cerca ed Elimina":
    st.title("🔍 Ricerca Inventario")
    chiave = st.text_input("Cerca...")
    ris = db.cerca_scatola(chiave) if chiave else db.visualizza_inventario()
    for r in ris:
        with st.expander(f"📦 {r[1]} | Posizione: {r[10]}-{r[11]}"):
            c1, c2 = st.columns([1, 2])
            if r[3]: c1.image(r[3], width=200)
            c2.write(f"**Descrizione:** {r[2]}")
            s1, s2, s3 = st.columns(3)
            if r[5]: s1.image(r[5], caption=f"Cima: {r[4]}")
            if r[7]: s2.image(r[7], caption=f"Centro: {r[6]}")
            if r[9]: s3.image(r[9], caption=f"Fondo: {r[8]}")
            if st.button("🗑️ ELIMINA SCATOLA", key=f"del_{r[0]}"):
                db.elimina_scatola(r[0]); st.rerun()

elif scelta == "⚙️ Configura Magazzino":
    st.title("⚙️ Setup Postazioni")
    with st.form("c_mag"):
        col_s, col_z = st.columns(2)
        scaf = col_s.text_input("Codice Scaffale (es. A1)")
        zona = col_z.text_input("Nome Zona (es. Garage)")
        if st.form_submit_button("Salva Nuova Postazione"):
            if scaf and zona:
                db.aggiungi_posizione(scaf, zona)
                st.success(f"Postazione {scaf} aggiunta!")
                st.rerun()

    st.write("---")
    st.subheader("📍 Elenco Postazioni Registrate")
    
    conn = db.connetti_db()
    df_pos = pd.read_sql_query("SELECT * FROM posizioni", conn)
    conn.close()

    if not df_pos.empty:
        # Pulizia nomi colonne
        df_pos.columns = [c.upper() for c in df_pos.columns]
        
        for index, row in df_pos.iterrows():
            # Logica "Flessibile" per i nomi delle colonne
            c_codice = row.get('ID_POSIZIONE', row.get('CODICE', 'N/A'))
            # Prova a cercare 'NOME_ZONA', se non esiste cerca 'ZONA'
            c_zona = row.get('NOME_ZONA', row.get('ZONA', 'N/A'))
            
            c1, c2, c3 = st.columns([2, 2, 1])
            c1.write(f"**Codice:** {c_codice}")
            c2.write(f"**Zona:** {c_zona}")
            if c3.button("Elimina", key=f"btn_del_{c_codice}_{index}"):
                conn = db.connetti_db()
                # Elimina usando la colonna corretta (ID_POSIZIONE)
                col_id = 'ID_POSIZIONE' if 'ID_POSIZIONE' in df_pos.columns else 'id_posizione'
                conn.execute(f"DELETE FROM posizioni WHERE {col_id} = ?", (c_codice,))
                conn.commit(); conn.close()
                st.success(f"Postazione {c_codice} eliminata!")
                st.rerun()
    else:
        st.info("Nessuna postazione registrata.")

elif scelta == "🖨️ Stampa":
    st.title("🖨️ Centro Stampa")
    t1, t2 = st.tabs(["📦 Scatole", "📍 Scaffali"])
    with t1:
        scatole = db.visualizza_inventario()
        sel_s = [s for s in scatole if st.checkbox(f"Stampa {s[1]}", key=f"ps_{s[0]}")]
        if st.button("Genera PDF Scatole") and sel_s:
            pdf = FPDF()
            for i in range(0, len(sel_s), 2):
                pdf.add_page()
                for idx, s in enumerate(sel_s[i:i+2]):
                    y = 10 if idx == 0 else 150
                    pdf.rect(10, y, 190, 130)
                    pdf.set_font("Arial", 'B', 24); pdf.set_xy(15, y+10); pdf.cell(0,10,f"SCATOLA: {s[1]}")
                    pdf.set_font("Arial", '', 14); pdf.set_xy(15, y+25); pdf.multi_cell(110,8,f"DESC: {s[2]}")
                    qr = QRCode(box_size=6); qr.add_data(s[1]); qr.make(); img = qr.make_image(); p = f"t_s_{idx}.png"; img.save(p)
                    pdf.image(p, x=135, y=y+20, w=55); os.remove(p)
            st.download_button("Scarica PDF Scatole", pdf.output(dest='S').encode('latin-1'), "scatole.pdf")
    with t2:
        pos = db.visualizza_posizioni()
        sel_p = [p for p in pos if st.checkbox(f"Stampa {p[0]}", key=f"pp_{p[0]}")]
        if st.button("Genera PDF Scaffali") and sel_p:
            pdf = FPDF()
            for i in range(0, len(sel_p), 2):
                pdf.add_page()
                for idx, p in enumerate(sel_p[i:i+2]):
                    y = 10 if idx == 0 else 150
                    pdf.rect(10, y, 190, 130)
                    pdf.set_font("Arial", 'B', 40); pdf.set_xy(15, y+40); pdf.cell(0,10,f"POSTO: {p[0]}")
                    pdf.set_font("Arial", '', 20); pdf.set_xy(15, y+60); pdf.cell(0,10,f"ZONA: {p[1]}")
                    qr = QRCode(box_size=8); qr.add_data(p[0]); qr.make(); img = qr.make_image(); path = f"t_p_{idx}.png"; img.save(path)
                    pdf.image(path, x=130, y=y+25, w=60); os.remove(path)
            st.download_button("Scarica PDF Scaffali", pdf.output(dest='S').encode('latin-1'), "scaffali.pdf")