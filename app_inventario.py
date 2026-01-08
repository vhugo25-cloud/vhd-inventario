import streamlit as st
import pandas as pd
import db_manager
from qrcode import QRCode
import io
import os
import time
from fpdf import FPDF
from datetime import datetime
import cloudinary
import cloudinary.uploader
from streamlit_qrcode_scanner import qrcode_scanner

# --- CONFIGURAZIONE PERCORSI ASSETS ---
ASSETS_DIR = "assets"

def check_img(nome_file):
    path = os.path.join(ASSETS_DIR, nome_file)
    if os.path.exists(path):
        return path
    return "https://via.placeholder.com/150x150.png?text=Mancante"

PATH_HOME    = check_img("home.png")
PATH_NUOVA   = check_img("nuova.png")
PATH_SPOSTA  = check_img("sposta.png")
PATH_CERCA   = check_img("cerca.png")
PATH_STAMPA  = check_img("stampa.png")
PATH_SCANNER = check_img("scanner.png")
PATH_CONFIG  = check_img("config.png")
NO_PHOTO     = check_img("no_image.png")

# --- CONFIGURAZIONE CLOUDINARY ---
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

st.set_page_config(page_title="Inventario Casa VHD", layout="wide")

# --- ESTETICA PROFESSIONALE (FIX DARK MODE & VISIBILITÀ) ---
# --- ESTETICA PROFESSIONALE (ADATTIVA PER DARK & LIGHT MODE) ---
st.markdown("""
    <style>
    /* Sfondo Sidebar professionale (rimane scuro con testo bianco) */
    [data-testid="stSidebar"] { background-color: #001f3f; }
    [data-testid="stSidebar"] * { color: white !important; font-size: 1.1rem; }
    
    /* FIX VISIBILITÀ: Non forziamo un colore fisso per i titoli, 
       lasciamo che Streamlit lo gestisca, o usiamo un colore neutro */
    h1, h2, h3 { 
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        /* Rimuoviamo il color: #001f3f !important qui */
    }

    /* Le metriche ora hanno un bordo blu ma uno sfondo che si adatta */
    div[data-testid="stMetric"] {
        background-color: rgba(128, 128, 128, 0.1); 
        padding: 15px; 
        border-radius: 10px; 
        border-left: 5px solid #007bff;
    }
    
    /* Gli Expander (i menu a tendina) ora sono leggibili ovunque */
    .stExpander { 
        border: 1px solid #007bff; 
        border-radius: 10px; 
    }
    
    .data-piccola { font-size: 0.85rem; color: #888; font-style: italic; }
    </style>
    """, unsafe_allow_html=True)

# Inizializzazione Database Cloud (Dalla tua Classe InventarioDB)
db = db_manager.InventarioDB()
utenti = ["Victor", "Evelyn", "Daniel", "Carly", "Rebby"]
menu = ["🏠 Home", "🔍 Cerca ed Elimina", "📸 Scanner QR", "➕ Nuova Scatola", "🔄 Alloca/Sposta", "⚙️ Configura Magazzino", "🖨️ Stampa"]
scelta = st.sidebar.selectbox("Menu Principale", menu)

# Tasto Sveglia per Supabase (Sidebar)


def upload_foto(file, nome, tipo):
    if file:
        try:
            prefisso = (nome[:3].upper()) if len(nome) >= 3 else "BOX"
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nome_unico = f"{prefisso}_{tipo}_{timestamp}"
            ris = cloudinary.uploader.upload(file, folder="VHD_Inventario", public_id=nome_unico)
            return ris['secure_url']
        except:
            return ""
    return ""

# --- 🏠 HOME ---
# --- 🏠 HOME (VERSIONE FINALE PER LA FAMIGLIA) ---
if scelta == "🏠 Home":
    st.image(PATH_HOME, width=150)
    st.title("Inventario Casa VHD")
    
    # Riga discreta per l'assistenza connessione
    col_testo, col_bottone = st.columns([2, 1])
    with col_bottone:
        if st.button("🔗 Sistema offline?", type="secondary", help="Clicca se le metriche sotto segnano zero"):
            with st.spinner("Sveglia database in corso..."):
                ok, msg = db.sveglia_database()
                if ok:
                    st.toast("Magazzino connesso!", icon="✅")
                    st.rerun()
                else:
                    st.error("Errore. Controlla internet.")

    st.info("Benvenuto nel sistema WMS Cloud. Riepilogo magazzino in tempo reale.")
    st.write("---")
    
    # Recupero dati
    inv = db.visualizza_inventario()
    pos = db.visualizza_posizioni()
    
    # --- METRICHE ---
    c1, c2, c3, c4 = st.columns(4)
    
    # 1. Totale Scatole
    c1.metric("📦 Scatole", len(inv))
    
    # 2. Zone Uniche
    zone_uniche = len(set([p[1] for p in pos])) if pos else 0
    c2.metric("📍 Zone", zone_uniche)
    
    # 3. Totale Ubicazioni
    c3.metric("📌 Ubicazioni", len(pos))
    
    # 4. Calcolo "Da Allocare" (Colonna 17: Ubicazione)
    try:
        da_allocare_list = [
            s for s in inv 
            if len(s) > 17 and (str(s[17]).strip().upper() == "NON ALLOCATA" or s[17] is None or str(s[17]).strip() == "")
        ]
        count_da_allocare = len(da_allocare_list)
    except:
        count_da_allocare = 0

    c4.metric("⚠️ Da Allocare", count_da_allocare, delta=count_da_allocare, delta_color="inverse" if count_da_allocare > 0 else "normal")
    
    st.write("---")
    
    if inv:
        # Definizione nomi colonne per il DataFrame
        column_names_all = [
            "ID", "Nome", "Descrizione", "Foto_Main", "Cima_Testo", "Cima_Foto", 
            "Centro_Testo", "Centro_Foto", "Fondo_Testo", "Fondo_Foto", "Sinistra_Testo", 
            "Sinistra_Foto", "Destra_Testo", "Destra_Foto", "Zona", "Scaffale", 
            "Ripiano", "Ubicazione", "Proprietario", "Data", "Colore_Testo", 
            "Dimensione_Carattere", "Quantita", "Codice_Scatola", "Categoria", 
            "Stato", "Data_Inserimento", "Id_Ubicazione", "Foto_Url", "Centro_F", 
            "Cima_F", "Fondo_F", "Note"
        ]
        
        num_cols_received = len(inv[0])
        df = pd.DataFrame(inv, columns=column_names_all[:num_cols_received])
        
        st.subheader("📊 Ultime 10 Scatole Registrate")
        colonne_visibili = [c for c in ["Nome", "Zona", "Ubicazione", "Proprietario", "Data"] if c in df.columns]
        mostra_df = df[colonne_visibili].tail(10).iloc[::-1]
        st.dataframe(mostra_df, use_container_width=True, hide_index=True)
        
        # Export Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Inventario')
        
        st.download_button(
            label="📊 Scarica Report Excel Completo",
            data=output.getvalue(),
            file_name=f"Inventario_VHD_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    
    st.write("---")
    st.subheader("🗺️ Mappa Occupazione Magazzino")
    if pos:
        mappa_occupazione = {str(s[17]).strip(): s[1] for s in inv if len(s) > 17 and str(s[17]).strip().upper() != "NON ALLOCATA"}
        
        cols_per_row = 12
        for i in range(0, len(pos), cols_per_row):
            batch = pos[i:i + cols_per_row]
            cols = st.columns(cols_per_row)
            for j, p in enumerate(batch):
                id_u = str(p[0]).strip()
                with cols[j]:
                    if id_u in mappa_occupazione:
                        st.markdown(f'<div style="background-color:#FF4B4B; color:white; padding:5px; border-radius:3px; text-align:center; font-size:8px; line-height:1;" title="Scatola: {mappa_occupazione[id_u]}">📦<br>{id_u}</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div style="background-color:#28A745; color:white; padding:5px; border-radius:3px; text-align:center; font-size:8px; line-height:1;" title="LIBERA">✅<br>{id_u}</div>', unsafe_allow_html=True)
# --- 🔍 CERCA ED ELIMINA ---
elif scelta == "🔍 Cerca ed Elimina":
    st.image(PATH_CERCA, width=150)
    st.title("Gestione e Ricerca Database")
    chiave = st.text_input("🔍 Cosa stai cercando?", placeholder="Viti, Garage, Victor...")
    ris = db.cerca_scatola(chiave) if chiave else db.visualizza_inventario()
    
    if ris:
        for r in ris:
            with st.expander(f"📦 {r[1]} | 📍 {r[10]} - {r[11]} | 👤 {r[12]}"):
                st.markdown(f"<p class='data-piccola'>📅 Registrata il: {r[13]}</p>", unsafe_allow_html=True)
                col1, col2 = st.columns([1, 2])
                with col1:
                    st.image(r[3] if r[3] else NO_PHOTO, use_container_width=True)
                with col2:
                    st.write(f"**📝 Descrizione:** {r[2]}")
                    st.subheader("📸 Contenuto (Livelli)")
                    i1, i2, i3 = st.columns(3)
                    i1.image(r[5] if r[5] else NO_PHOTO); i1.caption(f"🔼 {r[4]}")
                    i2.image(r[7] if r[7] else NO_PHOTO); i2.caption(f"↔️ {r[6]}")
                    i3.image(r[9] if r[9] else NO_PHOTO); i3.caption(f"🔽 {r[8]}")
                if st.button(f"🗑️ ELIMINA: {r[1]}", key=f"del_{r[0]}", use_container_width=True):
                    db.elimina_scatola(r[0]); st.warning("Eliminata!"); time.sleep(1); st.rerun()
# --- 📸 SCANNER QR ---
elif scelta == "📸 Scanner QR":
    st.image(PATH_SCANNER, width=100)
    st.title("Scanner Rapido VHD")
    st.info("Punta la fotocamera verso il codice QR della scatola.")
    barcode = qrcode_scanner(key='scanner')
    if barcode:
        st.success(f"🔍 Codice rilevato: {barcode}")
        risultato = db.cerca_scatola(barcode)
        if risultato:
            r = risultato[0]
            st.markdown(f"### ✅ Scatola Trovata: {r[1]}")
            with st.expander("Dettagli", expanded=True):
                st.write(f"**📍 Ubicazione:** {r[10]} - {r[11]} | **👤 Proprietario:** {r[12]}")
                c1, c2 = st.columns(2)
                c1.image(r[3] if r[3] else NO_PHOTO, use_container_width=True)
                c2.info(f"🔼 **Cima:** {r[4]}\n\n↔️ **Centro:** {r[6]}\n\n🔽 **Fondo:** {r[8]}")
        else:
            st.error(f"❌ Scatola '{barcode}' non trovata.")

# --- ➕ NUOVA SCATOLA ---
# --- ➕ NUOVA SCATOLA ---
elif scelta == "➕ Nuova Scatola":
    st.image(PATH_NUOVA, width=150)
    st.title("Registra Nuova Scatola")
    with st.form("n_s", clear_on_submit=True):
        col_top1, col_top2 = st.columns([2, 1])
        with col_top1:
            nome = st.text_input("📦 Nome Scatola", placeholder="Esempio: SCATOLA_001")
            desc = st.text_area("📝 Descrizione Generale")
        with col_top2:
            prop = st.selectbox("👤 Proprietario", utenti)
            f_m = st.file_uploader("📸 Foto Esterna", type=['jpg', 'png', 'jpeg'])
        
        st.write("---")
        st.subheader("🔍 Dettaglio Contenuto Interno")
        c1, c2 = st.columns([2, 1])
        ct = c1.text_input("🔼 Livello SUPERIORE (Cima)")
        cf = c2.file_uploader("Foto Cima", key="fcima", type=['jpg', 'png'])
        
        m1, m2 = st.columns([2, 1])
        mt = m1.text_input("↔️ Livello CENTRALE")
        mf = m2.file_uploader("Foto Centro", key="fcentro", type=['jpg', 'png'])
        
        b1, b2 = st.columns([2, 1])
        bt = b1.text_input("🔽 Livello INFERIORE (Fondo)")
        bf = b2.file_uploader("Foto Fondo", key="ffondo", type=['jpg', 'png'])
        
        if st.form_submit_button("🚀 REGISTRA NEL DATABASE", use_container_width=True):
            if nome:
                with st.spinner("☁️ Caricamento foto e salvataggio in corso..."):
                    # 1. Carichiamo le foto su Cloudinary
                    u1 = upload_foto(f_m, nome, "main")
                    u2 = upload_foto(cf, nome, "cima")
                    u3 = upload_foto(mf, nome, "centro")
                    u4 = upload_foto(bf, nome, "fondo")
                    
                    # 2. Salvataggio nel database (Sincronizzato con db_manager)
                    try:
                        successo = db.aggiungi_scatola(
                            nome=nome,
                            desc=desc,
                            f_m=u1,
                            ct=ct,
                            cf=u2,
                            mt=mt,
                            mf=u3,
                            bt=bt,
                            bf=u4,
                            zona="DA DEFINIRE",
                            ubi="NON ALLOCATA",
                            prop=prop
                        )
                        
                        if successo:
                            st.balloons()
                            st.success(f"✅ Scatola '{nome}' salvata correttamente con le foto!")
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error("❌ Il database non ha risposto correttamente.")

                    except Exception as e:
                        st.error(f"❌ Errore durante il salvataggio: {e}")
            else:
                st.error("⚠️ Il nome è obbligatorio!")

# --- 🔄 ALLOCA/SPOSTA ---
elif scelta == "🔄 Alloca/Sposta":
    st.image(PATH_SPOSTA, width=150)
    st.title("Movimentazione e Allocazione")
    inv = db.visualizza_inventario(); pos = db.visualizza_posizioni()
    if pos and inv:
        col_move1, col_move2 = st.columns(2)
        with col_move1:
            s_list = [f"{s[0]} | {s[1]} (Attuale: {s[11]})" for s in inv]
            s_sel = st.selectbox("Scegli la scatola", s_list)
        with col_move2:
            p_list = [f"{p[1]} - {p[0]}" for p in pos]
            p_sel = st.selectbox("Scegli la destinazione", p_list)
        ids = int(s_sel.split(" | ")[0]); zn, un = p_sel.split(" - ")
        if st.button("✅ CONFERMA SPOSTAMENTO", use_container_width=True):
            db.aggiorna_posizione_scatola(ids, zn, un)
            st.success("Spostamento completato!"); time.sleep(1.5); st.rerun()

# --- ⚙️ CONFIGURA ---
elif scelta == "⚙️ Configura Magazzino":
    st.image(PATH_CONFIG, width=100)
    st.title("Impostazioni Motore WMS")
    t1, t2, t3 = st.tabs(["➕ Nuova Ubicazione", "📥 Import Excel", "🗑️ Gestione"])
    with t1:
        with st.form("p", clear_on_submit=True):
            s = st.text_input("🆔 ID Ubicazione"); z = st.text_input("📍 Zona")
            if st.form_submit_button("➕ SALVA POSIZIONE"):
                if s and z:
                    db.aggiungi_posizione(s, z); st.success("Salvata!"); st.rerun()
    with t2:
        file_ex = st.file_uploader("Carica Excel", type=['xlsx'])
        if file_ex:
            df_pos = pd.read_excel(file_ex)
            st.dataframe(df_pos.head(10))
            if st.button("🚀 AVVIA IMPORTAZIONE"):
                ok, count = db.import_posizioni_da_df(df_pos)
                if ok: st.success(f"Caricate {count} posizioni!"); st.rerun()
    with t3:
        # Reset Totale (ZONA PERICOLOSA)
        if st.expander("🚨 RESET TOTALE DATABASE"):
            pwd = st.text_input("Password Amministratore", type="password")
            if st.button("🔥 AZZERA TUTTO"):
                if pwd == "233674":
                    # Nota: la funzione reset va aggiunta nel db_manager se necessario
                    st.warning("Funzione reset attivata."); time.sleep(2); st.rerun()

# --- 🖨️ STAMPA ---
# --- 🖨️ STAMPA (VERSIONE DEFINITIVA E CALIBRATA) ---
elif scelta == "🖨️ Stampa":
    st.image(PATH_STAMPA, width=150)
    st.title("Centro Stampa Etichette Professionale")
    
    # Recupero dati dal DB per il filtro
    inv_totale = db.visualizza_inventario()
    
    if "filtro_stampa" not in st.session_state: 
        st.session_state.filtro_stampa = ""
    
    filtro_veloce = st.text_input("🔍 Cerca per Nome, Proprietario o Contenuto", 
                                  value=st.session_state.filtro_stampa,
                                  placeholder="Es: Victor, Evelyn, Scarpe...")
    st.session_state.filtro_stampa = filtro_veloce
    
    if filtro_veloce:
        tab_s, tab_u = st.tabs(["📦 Etichette Scatole", "📍 Etichette Ubicazioni"])
        
        with tab_s:
            # Filtro intelligente locale (Nome, Proprietario, Descrizione)
            f = filtro_veloce.lower()
            inv_da_mostrare = [
                s for s in inv_totale 
                if f in str(s[1]).lower() or f in str(s[18]).lower() or f in str(s[2]).lower()
            ]
            
            sel_s = []
            if inv_da_mostrare:
                st.write(f"✅ Trovate {len(inv_da_mostrare)} scatole")
                for s in inv_da_mostrare:
                    # s[1]=Nome, s[17]=Ubicazione, s[18]=Proprietario
                    nome_s = s[1]
                    prop_s = s[18] if s[18] else "N/A"
                    ubi_s = s[17] if s[17] else "DA ALLOCARE"
                    
                    if st.checkbox(f"👤 {prop_s.upper()} | 📦 {nome_s} | 📍 {ubi_s}", key=f"st_{s[0]}"):
                        sel_s.append(s)
                
                if sel_s and st.button("📥 GENERA PDF PER SELEZIONATI", use_container_width=True):
                    pdf = FPDF()
                    # Elaboriamo 2 scatole alla volta per pagina
                    for i in range(0, len(sel_s), 2):
                        pdf.add_page()
                        for idx, s in enumerate(sel_s[i:i+2]):
                            # Calcolo coordinata Y di partenza (10 per la prima, 150 per la seconda)
                            y_start = 10 if idx == 0 else 150
                            
                            nome_etichetta = str(s[1])
                            prop_etichetta = str(s[18]).upper()
                            data_raw = str(s[19])
                            
                            # Formattazione Data DD/MM/YYYY
                            try:
                                dp = data_raw[:10].split("-")
                                data_f = f"{dp[2]}/{dp[1]}/{dp[0]}"
                            except:
                                data_f = data_raw

                            # --- DISEGNO GRAFICO ---
                            # Cornice etichetta
                            pdf.rect(10, y_start, 190, 130)
                            
                            # Proprietario (Grande)
                            pdf.set_font("Arial", 'B', 45)
                            pdf.set_xy(15, y_start + 15)
                            pdf.cell(110, 20, prop_etichetta, ln=0)
                            
                            # Nome Scatola (Sotto proprietario)
                            pdf.set_font("Arial", 'B', 25)
                            pdf.set_xy(15, y_start + 45)
                            pdf.multi_cell(110, 12, nome_etichetta)
                            
                            # Data (In basso a sinistra)
                            pdf.set_font("Arial", 'I', 12)
                            pdf.set_xy(15, y_start + 115)
                            pdf.cell(0, 10, f"Registrata il: {data_f}")
                            
                            # --- GENERAZIONE QR CODE ---
                            qr = QRCode(box_size=5)
                            qr.add_data(nome_etichetta)
                            qr.make()
                            img = qr.make_image()
                            temp_img = f"qr_temp_{idx}.png"
                            img.save(temp_img)
                            
                            # Inserimento QR Code con coordinata Y calibrata
                            pdf.image(temp_img, x=125, y=y_start + 30, w=65)

                    st.download_button("💾 Scarica PDF", pdf.output(dest='S').encode('latin-1'), "etichette_vhd.pdf")
            else:
                st.warning("Nessuna scatola trovata.")

        with tab_u:
            pos_complete = db.visualizza_posizioni()
