import streamlit as st
import pandas as pd
from db_manager import InventarioDB
from qrcode import QRCode
import io, os
from fpdf import FPDF
from streamlit_qrcode_scanner import qrcode_scanner

st.set_page_config(page_title="VHD WMS Pro Max", layout="wide")
db = InventarioDB()
if not os.path.exists("foto_scatole"): os.makedirs("foto_scatole")

utenti = ["Victor", "Evelyn", "Daniel", "Carly", "Rebby"]
menu = ["🏠 Home", "🔍 Cerca ed Elimina", "📸 Scanner", "➕ Nuova Scatola", "🔄 Alloca/Sposta", "⚙️ Configura Magazzino", "🖨️ Stampa"]
scelta = st.sidebar.selectbox("Menu", menu)

def salva_foto(foto, nome_scatola, tipo):
    if foto:
        path = f"foto_scatole/{nome_scatola}_{tipo}.jpg"
        with open(path, "wb") as f: f.write(foto.getbuffer())
        return path
    return ""

if scelta == "🏠 Home":
    st.title("VHD Magazzino Smart")
    st.write("Sistema pronto per la gestione multi-zona.")

elif scelta == "➕ Nuova Scatola":
    st.title("➕ Registra Scatola")
    with st.form("form_scatola"):
        nome = st.text_input("Nome/Codice Scatola")
        desc_gen = st.text_area("Descrizione generale")
        prop = st.selectbox("Proprietario", utenti)
        st.subheader("🖼️ Foto Principale (Esterna)")
        foto_main = st.file_uploader("Carica foto scatola", type=["jpg","png"], key="fmain")
        with st.expander("➕ Dettaglio Strati (Opzionale)"):
            c1, c2 = st.columns(2)
            cima_t = c1.text_input("Cima"); cima_f = c2.file_uploader("Foto Cima", type=["jpg","png"], key="f1")
            cent_t = c1.text_input("Centro"); cent_f = c2.file_uploader("Foto Centro", type=["jpg","png"], key="f2")
            fond_t = c1.text_input("Fondo"); fond_f = c2.file_uploader("Foto Fondo", type=["jpg","png"], key="f3")
        if st.form_submit_button("Salva Scatola"):
            if nome:
                pm = salva_foto(foto_main, nome, "principale")
                pc = salva_foto(cima_f, nome, "cima")
                pcn = salva_foto(cent_f, nome, "centro")
                pf = salva_foto(fond_f, nome, "fondo")
                db.aggiungi_scatola(nome, desc_gen, pm, cima_t, pc, cent_t, pcn, fond_t, pf, "DA ALLOCARE", prop)
                st.success(f"Scatola {nome} salvata!")
            else: st.error("Inserisci il nome!")

elif scelta == "🔍 Cerca ed Elimina":
    st.title("🔍 Ricerca Inventario")
    chiave = st.text_input("Cerca oggetto o contenuto...")
    ris = db.cerca_scatola(chiave) if chiave else db.visualizza_inventario()
    for r in ris:
        with st.expander(f"📦 {r[1]} | 📍 {r[10].upper()} | 👤 {r[11]}"):
            c_foto, c_info = st.columns([1, 2])
            with c_foto:
                if r[3] and os.path.exists(r[3]): st.image(r[3], use_container_width=True)
            with c_info:
                st.write(f"**Descrizione:** {r[2]}")
                if any([r[4], r[5], r[6], r[7], r[8], r[9]]):
                    s1, s2, s3 = st.columns(3)
                    if r[5]: s1.image(r[5], caption=f"Cima: {r[4]}")
                    if r[7]: s2.image(r[7], caption=f"Centro: {r[6]}")
                    if r[9]: s3.image(r[9], caption=f"Fondo: {r[8]}")
            if st.button(f"🗑️ Elimina", key=f"del_{r[0]}"):
                db.elimina_scatola(r[0]); st.rerun()

elif scelta == "🔄 Alloca/Sposta":
    st.title("🔄 Posizionamento Scatole")
    scatole = db.visualizza_inventario()
    pos_db = db.visualizza_posizioni()
    
    zone_esistenti = sorted(list(set([p[1] for p in pos_db])))
    opzioni_zona = ["--- Seleziona Zona ---", "In Casa", "Ripostiglio", "Garage", "Cantina"] + zone_esistenti
    
    for s in scatole:
        with st.expander(f"📦 {s[1]} - Attualmente in: {s[10]}"):
            c1, c2 = st.columns(2)
            z_scelta = c1.selectbox("1. Zona", opzioni_zona, key=f"z_{s[0]}")
            scaffali_in_z = [p[0] for p in pos_db if p[1] == z_scelta]
            
            if scaffali_in_z:
                ub = c2.selectbox("2. Scaffale", ["Nessuno"] + scaffali_in_z, key=f"ub_{s[0]}")
            else:
                ub = c2.text_input("2. Punto specifico (opzionale)", key=f"txt_ub_{s[0]}")

            if st.button("Salva Posizione", key=f"btn_{s[0]}"):
                if z_scelta != "--- Seleziona Zona ---":
                    pos_fin = z_scelta + (f" - {ub}" if ub and ub != "Nessuno" else "")
                    conn = db.connetti_db()
                    conn.execute("UPDATE inventario SET posizione = ? WHERE id = ?", (pos_fin, s[0]))
                    conn.commit(); conn.close(); st.success(f"Spostata!"); st.rerun()

elif scelta == "⚙️ Configura Magazzino":
    st.title("⚙️ Setup Scaffali")
    with st.form("conf"):
        id_p = st.text_input("Codice Scaffale (es. A1)")
        zona = st.text_input("Dove si trova? (es. Garage)")
        if st.form_submit_button("Aggiungi"):
            if id_p and zona: db.aggiungi_posizione(id_p, zona); st.rerun()
    for p in db.visualizza_posizioni():
        st.write(f"📍 Scaffale **{p[0]}** in **{p[1]}**")
        if st.button("Elimina", key=f"rm_{p[0]}"): db.elimina_posizione(p[0]); st.rerun()

elif scelta == "🖨️ Stampa":
    st.title("🖨️ Stampa QR")
    scatole = db.visualizza_inventario()
    sel_s = [s[1] for s in scatole if st.checkbox(f"Stampa {s[1]}", key=f"ps_{s[0]}")]
    if st.button("Genera PDF") and sel_s:
        pdf = FPDF()
        for i in range(0, len(sel_s), 2):
            pdf.add_page()
            for j, n in enumerate(sel_s[i:i+2]):
                y = 10 if j == 0 else 150
                qr = QRCode(box_size=10); qr.add_data(n); img = qr.make_image()
                p = f"temp_{j}.png"; img.save(p)
                pdf.rect(10, y, 190, 135)
                pdf.set_font("Arial", 'B', 16); pdf.set_xy(15, y+10); pdf.cell(0, 10, f"SCATOLA: {n}")
                pdf.image(p, x=60, y=y+30, w=80); os.remove(p)
        st.download_button("Scarica PDF", pdf.output(dest='S').encode('latin-1'), "etichette.pdf")