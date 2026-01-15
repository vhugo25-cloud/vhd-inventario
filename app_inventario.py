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

# --- ESTETICA PROFESSIONALE (FIX DARK MODE & CONTRASTO) ---
# Ho aggiunto il selettore per far sì che il testo cambi colore in base al tema di Streamlit
st.markdown("""
    <style>
    /* Forza visibilità testi in base al tema */
    @media (prefers-color-scheme: dark) {
        h1, h2, h3, p, span, label, .stMarkdown { color: #FFFFFF !important; }
    }
    @media (prefers-color-scheme: light) {
        h1, h2, h3, p, span, label, .stMarkdown { color: #001f3f !important; }
    }

    [data-testid="stSidebar"] { background-color: #001f3f; }
    [data-testid="stSidebar"] * { color: white !important; font-size: 1.1rem; }
    
    .stMetric { 
        background-color: #ffffff; padding: 15px; border-radius: 10px; 
        border-left: 5px solid #007bff; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); 
    }
    /* Colore metriche per non farle sparire */
    [data-testid="stMetricValue"] { color: #007bff !important; }
    
    .stExpander { border: 1px solid #007bff; border-radius: 10px; }
    .data-piccola { font-size: 0.85rem; font-style: italic; }
    </style>
    """, unsafe_allow_html=True)

# Inizializzazione Database
db = db_manager.InventarioDB()
utenti = ["Victor", "Evelyn", "Daniel", "Carly", "Rebby"]

# --- MENU CON VOCE MODIFICA ---
menu = [
    "🏠 Home", 
    "🔍 Cerca ed Elimina", 
    "➕ Nuova Scatola", 
    "📝 Modifica Scatola", # <-- Inserita qui come richiesto
    "📸 Scanner QR", 
    "🔄 Alloca/Sposta", 
    "⚙️ Configura Magazzino", 
    "🖨️ Stampa"
]
scelta = st.sidebar.selectbox("Menu Principale", menu)

# --- FUNZIONE UPLOAD FOTO ---
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
# --- 🏠 HOME (VERSIONE RIPARATA, VELOCE E DARK-READY) ---
if scelta == "🏠 Home":
    st.image(PATH_HOME, width=150)
    st.title("Inventario Casa VHD")
    
    col_testo, col_bottone = st.columns([2, 1])
    with col_bottone:
        if st.button("🔗 Sistema offline?", type="secondary", help="Sveglia il database se le metriche sono a zero"):
            with st.spinner("Sveglia database..."):
                ok, msg = db.sveglia_database()
                if ok:
                    st.toast("Connesso!", icon="✅")
                    st.rerun()

    st.info("Benvenuto nel sistema WMS Cloud. Riepilogo magazzino in tempo reale.")
    
    # Recupero dati (Formato Dizionario per gestire le 66 colonne senza crash)
    inv_data = db.visualizza_inventario()
    pos = db.visualizza_posizioni()
    
    # --- METRICHE ---
    c1, c2, c3, c4 = st.columns(4)
    
    c1.metric("📦 Scatole", len(inv_data))
    
    zone_uniche = len(set([p.get('zona') for p in pos if p.get('zona')])) if pos else 0
    c2.metric("📍 Zone", zone_uniche)
    
    c3.metric("📌 Ubicazioni", len(pos))

    # Calcolo "Da Allocare" sicuro (usando i nomi colonne del tuo SQL)
    count_da_allocare = 0
    if inv_data:
        count_da_allocare = len([
            s for s in inv_data 
            if s.get('ubi') == "NON ALLOCATA" or not s.get('ubi') or str(s.get('ubi')).strip() == ""
        ])
    
    c4.metric("⚠️ Da Allocare", count_da_allocare, delta=count_da_allocare, delta_color="inverse" if count_da_allocare > 0 else "normal")
    
    st.write("---")
    
    if inv_data:
        # Creazione DataFrame automatica: gestisce 33 o 66 colonne senza errori
        df = pd.DataFrame(inv_data)
        
        st.subheader("📊 Ultime 10 Scatole Registrate")
        
        # Mappa nomi colonne per visualizzazione pulita
        mappa_nomi = {
            "nome": "Nome", 
            "zon": "Zona", 
            "ubi": "Ubicazione", 
            "proprietario": "Proprietario", 
            "data_inserimento": "Data"
        }
        
        cols_esistenti = [c for c in mappa_nomi.keys() if c in df.columns]
        mostra_df = df[cols_esistenti].tail(10).rename(columns=mappa_nomi)
        
        # Tabella con inversione ordine (le ultime in alto)
        st.dataframe(mostra_df.iloc[::-1], use_container_width=True, hide_index=True)
        
        # Export Excel professionale
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
        # Mappa occupazione: Ubicazione -> Nome Scatola
        mappa_occupazione = {
            str(s.get('ubi', '')).strip(): s.get('nome') 
            for s in inv_data 
            if s.get('ubi') and str(s.get('ubi')).upper() != "NON ALLOCATA"
        }
        
        cols_per_row = 12
        for i in range(0, len(pos), cols_per_row):
            batch = pos[i:i + cols_per_row]
            cols = st.columns(cols_per_row)
            for j, p in enumerate(batch):
                id_u = str(p.get('id', '')).strip()
                piena = id_u in mappa_occupazione
                
                with cols[j]:
                    # Colore Rosso se piena, Verde se libera
                    color = "#FF4B4B" if piena else "#28A745"
                    icon = "📦" if piena else "✅"
                    
                    # HTML per i quadratini (Testo sempre bianco per contrasto)
                    st.markdown(f'''
                        <div style="background-color:{color}; color:white !important; padding:5px; 
                        border-radius:3px; text-align:center; font-size:8px; line-height:1.2;
                        min-height:35px; border: 1px solid rgba(255,255,255,0.1);" 
                        title="{mappa_occupazione[id_u] if piena else 'Libera'}">
                        <span style="color: white !important;">{icon}</span><br>
                        <span style="color: white !important; font-weight: bold;">{id_u}</span>
                        </div>''', unsafe_allow_html=True)
                    
# --- 🔍 CERCA ED ELIMINA ---
# --- 🔍 CERCA ED ELIMINA (VERSIONE RIPARATA E VISIBILE) ---
elif scelta == "🔍 Cerca ed Elimina":
    st.image(PATH_CERCA, width=150)
    st.title("Gestione e Ricerca Database")
    
    # Campo di ricerca
    chiave = st.text_input("🔍 Cosa stai cercando?", placeholder="Viti, Garage, Victor...", help="Scrivi qui per filtrare i risultati")
    
    # Recupero dati dal database
    with st.spinner("Ricerca in corso..."):
        ris = db.cerca_scatola(chiave) if chiave else db.visualizza_inventario()
    
    if ris:
        st.write(f"✅ Trovate {len(ris)} scatole")
        for r in ris:
            # ✅ ESTRAZIONE SICURA: Se la colonna non esiste, mette "N/D" invece di dare errore
            id_db = r.get('id')
            nome = r.get('nome', 'Senza Nome')
            desc = r.get('descrizione', '-')
            zona = r.get('zon', 'N/D')
            ubi = r.get('ubi', 'N/D')
            prop = r.get('proprietario', 'N/D')
            data_reg = r.get('data_inserimento', 'Data non disp.')
            
            # Recupero Foto con fallback (se vuote mette l'immagine di default)
            f_main = r.get('foto_main') if r.get('foto_main') else NO_PHOTO
            f_cima = r.get('cima_foto') if r.get('cima_foto') else NO_PHOTO
            f_cent = r.get('centro_foto') if r.get('centro_foto') else NO_PHOTO
            f_fond = r.get('fondo_foto') if r.get('fondo_foto') else NO_PHOTO

            # --- INTERFACCIA GRAFICA ---
            # Usiamo HTML per assicurarci che il titolo dell'expander sia leggibile
            with st.expander(f"📦 {nome} | 📍 {zona} - {ubi} | 👤 {prop}"):
                st.markdown(f"<p style='color: #A0A0A0; font-size: 0.8rem;'>📅 Registrata il: {data_reg}</p>", unsafe_allow_html=True)
                
                col1, col2 = st.columns([1, 2])
                with col1:
                    # Foto Esterna
                    st.image(f_main, use_container_width=True, caption="Vista Esterna")
                
                with col2:
                    st.write(f"**📝 Descrizione:** {desc}")
                    st.markdown("---")
                    st.subheader("🔍 Contenuto Interno (3 Livelli)")
                    
                    # Griglia per i 3 strati
                    i1, i2, i3 = st.columns(3)
                    with i1:
                        st.image(f_cima, use_container_width=True)
                        st.caption(f"🔼 {r.get('cima_testo', 'Cima')}")
                    with i2:
                        st.image(f_cent, use_container_width=True)
                        st.caption(f"↔️ {r.get('centro_testo', 'Centro')}")
                    with i3:
                        st.image(f_fond, use_container_width=True)
                        st.caption(f"🔽 {r.get('fondo_testo', 'Fondo')}")
                
                st.write("") # Spaziatore
                # Bottone Elimina con chiave univoca
                if st.button(f"🗑️ ELIMINA DEFINITIVAMENTE: {nome}", key=f"del_{id_db}", use_container_width=True):
                    if db.elimina_scatola(id_db):
                        st.warning(f"Scatola '{nome}' rimossa.")
                        time.sleep(1)
                        st.rerun()
    else:
        st.info("Nessuna scatola trovata. Prova a inserire un'altra parola chiave o lascia vuoto per vedere tutto.")

# --- ➕ NUOVA SCATOLA (STRUTTURA ORIGINALE) ---
elif scelta == "➕ Nuova Scatola":
    st.image(PATH_NUOVA, width=150)
    st.title("Registrazione Nuova Scatola")
    
    with st.form("form_nuova_scatola", clear_on_submit=True):
        col_n, col_p = st.columns(2)
        nome = col_n.text_input("📦 Nome Scatola (es: BOX-001)")
        prop = col_p.selectbox("👤 Proprietario", utenti)
        desc = st.text_area("📝 Descrizione contenuto")
        
        st.write("---")
        st.subheader("📸 Foto Principale (Esterna)")
        f_main = st.file_uploader("Carica foto esterna", type=['png', 'jpg', 'jpeg'], key="main")
        
        st.write("---")
        st.subheader("🔼 Livello 1: Cima")
        c1, c2 = st.columns([2, 1])
        t_cima = c1.text_input("Cosa c'è in cima?", key="t_cima")
        f_cima = c2.file_uploader("Foto Cima", type=['png', 'jpg', 'jpeg'], key="f_cima")
        
        st.write("---")
        st.subheader("↔️ Livello 2: Centro")
        m1, m2 = st.columns([2, 1])
        t_cent = m1.text_input("Cosa c'è al centro?", key="t_cent")
        f_cent = m2.file_uploader("Foto Centro", type=['png', 'jpg', 'jpeg'], key="f_cent")
        
        st.write("---")
        st.subheader("🔽 Livello 3: Fondo")
        b1, b2 = st.columns([2, 1])
        t_fond = b1.text_input("Cosa c'è sul fondo?", key="t_fond")
        f_fond = b2.file_uploader("Foto Fondo", type=['png', 'jpg', 'jpeg'], key="f_fond")
        
        if st.form_submit_button("🚀 SALVA SCATOLA NEL CLOUD"):
            if nome:
                with st.spinner("Caricamento immagini e dati..."):
                    # Upload immagini su Cloudinary
                    u_main = upload_foto(f_main, nome, "main")
                    u_cima = upload_foto(f_cima, nome, "cima")
                    u_cent = upload_foto(f_cent, nome, "centro")
                    u_fond = upload_foto(f_fond, nome, "fondo")
                    
                    if db.aggiungi_scatola(
                        nome=nome, desc=desc, f_m=u_main, 
                        ct=t_cima, cf=u_cima, 
                        mt=t_cent, mf=u_cent, 
                        bt=t_fond, bf=u_fond, 
                        prop=prop
                    ):
                        st.balloons()
                        st.success(f"Scatola {nome} registrata correttamente!")
                        time.sleep(2)
                        st.rerun()
            else:
                st.error("Il nome della scatola è obbligatorio!")

# --- 📝 MODIFICA SCATOLA (NUOVA FUNZIONE) ---
elif scelta == "📝 Modifica Scatola":
    st.title("Modifica e Aggiornamento Scatola")
    inv_data = db.visualizza_inventario()
    
    if inv_data:
        nomi_scatole = [s.get('nome') for s in inv_data]
        box_da_modificare = st.selectbox("Scegli la scatola da aggiornare", nomi_scatole)
        
        # Recupero dati attuali della scatola scelta
        s = next(item for item in inv_data if item.get('nome') == box_da_modificare)
        
        with st.form("form_modifica"):
            st.warning(f"Stai modificando: {box_da_modificare}")
            
            nuovo_nome = st.text_input("Nuovo Nome", value=s.get('nome'))
            nuovo_prop = st.selectbox("Cambia Proprietario", utenti, index=utenti.index(s.get('proprietario')) if s.get('proprietario') in utenti else 0)
            nuova_desc = st.text_area("Aggiorna Descrizione", value=s.get('descrizione', ''))
            
            st.write("---")
            st.subheader("🖼️ Gestione Immagini")
            st.info("Carica una foto solo se vuoi sostituire quella attuale.")
            
            c_f1, c_f2 = st.columns(2)
            f_main_new = c_f1.file_uploader("Sostituisci Foto Esterna", type=['jpg','jpeg','png'])
            f_cima_new = c_f2.file_uploader("Sostituisci Foto Cima", type=['jpg','jpeg','png'])
            
            st.write("---")
            st.subheader("✍️ Testi Livelli")
            t_cima_new = st.text_input("Testo Cima", value=s.get('cima_testo', ''))
            t_cent_new = st.text_input("Testo Centro", value=s.get('centro_testo', ''))
            t_fond_new = st.text_input("Testo Fondo", value=s.get('fondo_testo', ''))

            if st.form_submit_button("✅ SALVA TUTTE LE MODIFICHE"):
                with st.spinner("Aggiornamento in corso..."):
                    # Se l'utente carica una nuova foto, la carichiamo, altrimenti teniamo la vecchia URL
                    url_main = upload_foto(f_main_new, nuovo_nome, "main") if f_main_new else s.get('foto_main')
                    url_cima = upload_foto(f_cima_new, nuovo_nome, "cima") if f_cima_new else s.get('cima_foto')
                    
                    # Chiamata al db_manager per aggiornare
                    if db.aggiorna_dati_scatola(
                        s.get('id'), nuovo_nome, nuova_desc, nuovo_prop, 
                        t_cima_new, t_cent_new, t_fond_new, url_main
                    ):
                        st.success("Modifiche salvate con successo!")
                        time.sleep(1)
                        st.rerun()
    else:
        st.info("Non ci sono scatole da modificare.")


# --- ➕ NUOVA SCATOLA ---
# --- ➕ NUOVA SCATOLA (Tua versione originale sincronizzata) ---
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
                    u1 = upload_foto(f_m, nome, "main")
                    u2 = upload_foto(cf, nome, "cima")
                    u3 = upload_foto(mf, nome, "centro")
                    u4 = upload_foto(bf, nome, "fondo")
                    
                    try:
                        successo = db.aggiungi_scatola(
                            nome=nome, desc=desc, f_m=u1,
                            ct=ct, cf=u2, mt=mt, mf=u3, bt=bt, bf=u4,
                            zona="DA DEFINIRE", ubi="NON ALLOCATA", prop=prop
                        )
                        if successo:
                            st.balloons()
                            st.success(f"✅ Scatola '{nome}' salvata correttamente!")
                            time.sleep(2)
                            st.rerun()
                    except Exception as e:
                        st.error(f"❌ Errore: {e}")
            else:
                st.error("⚠️ Il nome è obbligatorio!")

# --- 📝 MODIFICA SCATOLA (VOCE RICHIESTA) ---
elif scelta == "📝 Modifica Scatola":
    st.image(PATH_NUOVA, width=100) # Usiamo l'icona della scatola
    st.title("Modifica e Aggiornamento Scatola")
    
    inv_data = db.visualizza_inventario()
    if inv_data:
        # Creiamo una lista per la ricerca della scatola
        nomi_box = [s.get('nome') for s in inv_data]
        box_sel = st.selectbox("Seleziona la scatola da modificare", nomi_box)
        
        # Recupero dati attuali
        s = next(item for item in inv_data if item.get('nome') == box_sel)
        
        with st.form("edit_form"):
            st.info(f"Stai modificando i dati di: **{box_sel}**")
            
            c1, c2 = st.columns(2)
            nuovo_nome = c1.text_input("Aggiorna Nome", value=s.get('nome'))
            nuovo_prop = c2.selectbox("Cambia Proprietario", utenti, 
                                      index=utenti.index(s.get('proprietario')) if s.get('proprietario') in utenti else 0)
            
            nuova_desc = st.text_area("Modifica Descrizione", value=s.get('descrizione', ''))
            
            st.write("---")
            st.subheader("📸 Aggiornamento Immagini")
            st.warning("⚠️ Carica una foto solo se vuoi sostituire quella attuale, altrimenti lascia vuoto.")
            
            col_f1, col_f2 = st.columns(2)
            f_m_new = col_f1.file_uploader("Sostituisci Foto Esterna", type=['jpg','png','jpeg'])
            f_c_new = col_f2.file_uploader("Sostituisci Foto Cima", type=['jpg','png','jpeg'])
            
            st.write("---")
            st.subheader("✍️ Modifica Testi Strati")
            ct_new = st.text_input("Testo Cima", value=s.get('cima_testo', ''))
            mt_new = st.text_input("Testo Centro", value=s.get('centro_testo', ''))
            bt_new = st.text_input("Testo Fondo", value=s.get('fondo_testo', ''))

            if st.form_submit_button("✅ APPLICA TUTTE LE MODIFICHE"):
                with st.spinner("Aggiornamento in corso..."):
                    # Se l'utente non carica una nuova foto, manteniamo la vecchia URL recuperata dal DB
                    url_m = upload_foto(f_m_new, nuovo_nome, "main") if f_m_new else s.get('foto_main')
                    url_c = upload_foto(f_c_new, nuovo_nome, "cima") if f_c_new else s.get('cima_foto')
                    
                    # Chiamata al db_manager (Assicurati che db_manager abbia questa funzione)
                    successo = db.aggiorna_dati_scatola(
                        s.get('id'), nuovo_nome, nuova_desc, nuovo_prop, 
                        ct_new, mt_new, bt_new, url_m
                    )
                    
                    if successo:
                        st.success(f"Scatola '{nuovo_nome}' aggiornata con successo!")
                        time.sleep(1)
                        st.rerun()
    else:
        st.warning("Nessuna scatola presente nel database per la modifica.")

 # --- 📸 SCANNER QR (VERSIONE PER SURFACE) ---
elif scelta == "📸 Scanner QR":
    st.image(PATH_SCANNER, width=150)
    st.title("Scanner Intelligente VHD")
    st.info("Inquadra il codice QR sulla scatola per vedere il contenuto in tempo reale.")
    
    # Avvia lo scanner (usa la libreria streamlit_qrcode_scanner)
    codice_scansionato = qrcode_scanner(key='scanner_vhd')
    
    if codice_scansionato:
        st.success(f"✅ Codice rilevato: {codice_scansionato}")
        inv_data = db.visualizza_inventario()
        
        # Cerchiamo la scatola che ha quel nome o quel codice
        risultato = [s for s in inv_data if str(s.get('nome')).lower() == codice_scansionato.lower()]
        
        if risultato:
            r = risultato[0]
            with st.container():
                st.markdown(f"### 📦 Risultato: {r.get('nome')}")
                c1, c2 = st.columns([1, 2])
                c1.image(r.get('foto_main') or NO_PHOTO, use_container_width=True)
                with c2:
                    st.write(f"**📍 Posizione:** {r.get('zon')} - {r.get('ubi')}")
                    st.write(f"**👤 Proprietario:** {r.get('proprietario')}")
                    st.write(f"**📝 Descrizione:** {r.get('descrizione')}")
                    
                    st.subheader("🔍 Contenuto Livelli")
                    l1, l2, l3 = st.columns(3)
                    l1.image(r.get('cima_foto') or NO_PHOTO, caption=f"🔼 {r.get('cima_testo')}")
                    l2.image(r.get('centro_foto') or NO_PHOTO, caption=f"↔️ {r.get('centro_testo')}")
                    l3.image(r.get('fondo_foto') or NO_PHOTO, caption=f"🔽 {r.get('fondo_testo')}")
        else:
            st.warning("Scatola non trovata nel database. Verifica il codice QR.")       


# --- 🔄 ALLOCA/SPOSTA ---
# --- 🔄 ALLOCA/SPOSTA ---
elif scelta == "🔄 Alloca/Sposta":
    st.image(PATH_SPOSTA, width=150)
    st.title("Movimentazione e Allocazione")
    
    inv = db.visualizza_inventario()
    pos = db.visualizza_posizioni()
    
    if inv and pos:
        # ✅ Lista scatole sicura per 66 colonne
        s_list = [
            f"{s.get('id')} | {s.get('nome')} (Attuale: {s.get('ubi', 'NON ALLOCATA')})" 
            for s in inv
        ]
        s_sel = st.selectbox("📦 Seleziona la Scatola da spostare", s_list)
        
        # ✅ Lista posizioni sicura
        p_list = [f"{p.get('zona', 'N/D')} - {p.get('id', 'N/D')}" for p in pos]
        p_sel = st.selectbox("📍 Seleziona la nuova Destinazione", p_list)
        
        if st.button("🚀 CONFERMA SPOSTAMENTO", use_container_width=True):
            try:
                id_scatola = int(s_sel.split(" | ")[0])
                nuova_zona, nuova_ubi = p_sel.split(" - ")
                
                if db.aggiorna_posizione_scatola(id_scatola, nuova_zona, nuova_ubi):
                    st.success(f"Movimentazione riuscita! La scatola è ora in {nuova_ubi}")
                    time.sleep(1)
                    st.rerun()
            except Exception as e:
                st.error(f"Errore tecnico: {e}")

# --- ⚙️ CONFIGURA MAGAZZINO ---
# --- ⚙️ CONFIGURA MAGAZZINO (REVISIONE PROFESSIONALE) ---
elif scelta == "⚙️ Configura Magazzino":
    st.image(PATH_CONFIG, width=100)
    st.title("Impostazioni Motore WMS")
    
    # CSS per contrasto Dark Mode specifico per i form
    st.markdown("""<style>
        div.stForm { background-color: rgba(255, 255, 255, 0.05); border-radius: 10px; padding: 20px; }
        .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    </style>""", unsafe_allow_html=True)

    t1, t2, t3 = st.tabs(["➕ Nuova Ubicazione", "📥 Import Excel", "🗑️ Gestione"])
    
    with t1:
        st.subheader("Registra un nuovo spazio nel magazzino")
        with st.form("p_new", clear_on_submit=True):
            # Usiamo nomi chiari: s_id diventerà 'id', z_id diventerà 'zona'
            s_id = st.text_input("🆔 ID Ubicazione (es: A1-01, SCAFFALE-A)")
            z_id = st.text_input("📍 Nome Zona (es: Garage, Mansarda, Cantina)")
            
            if st.form_submit_button("➕ SALVA POSIZIONE"):
                if s_id and z_id:
                    # Pulizia dati: tutto in maiuscolo per l'ID per coerenza
                    id_pulito = str(s_id).strip().upper()
                    zona_pulita = str(z_id).strip()
                    
                    if db.aggiungi_posizione(id_pulito, zona_pulita):
                        st.success(f"✅ Ubicazione {id_pulito} salvata in {zona_pulita}!")
                        time.sleep(1)
                        st.rerun()
                else:
                    st.error("⚠️ Compila entrambi i campi prima di salvare.")
    
    with t2:
        st.subheader("Caricamento Massivo da Excel")
        st.info("Il file Excel deve avere due colonne: 'id' e 'zona'.")
        file_ex = st.file_uploader("Seleziona file .xlsx", type=['xlsx'])
        
        if file_ex:
            try:
                df_pos = pd.read_excel(file_ex)
                # Forza i nomi delle colonne in minuscolo per il database
                df_pos.columns = [c.lower() for c in df_pos.columns]
                
                st.write("👀 Anteprima dei primi 5 righi:")
                st.dataframe(df_pos.head(5), use_container_width=True)
                
                if st.button("🚀 AVVIA IMPORTAZIONE NEL DATABASE"):
                    with st.spinner("Sincronizzazione in corso..."):
                        ok, count = db.import_posizioni_da_df(df_pos)
                        if ok:
                            st.balloons()
                            st.success(f"📥 Importazione completata! Caricate {count} posizioni.")
                            time.sleep(2)
                            st.rerun()
            except Exception as e:
                st.error(f"Errore nella lettura del file: {e}")

    with t3:
        st.subheader("Pulizia e Reset")
        # Estrazione rapida per vedere cosa c'è dentro
        pos_attuali = db.visualizza_posizioni()
        st.write(f"Attualmente ci sono **{len(pos_attuali)}** ubicazioni registrate.")
        
        if st.expander("🚨 RESET TOTALE DATABASE (ZONA PERICOLOSA)"):
            st.warning("Questa azione è irreversibile. Cancellerà tutte le posizioni.")
            pwd = st.text_input("Inserisci Password Master", type="password")
            if st.button("🔥 AZZERA TUTTO"):
                if pwd == "233674":
                    # db.reset_posizioni() # Da attivare se necessario nel db_manager
                    st.error("Comando di cancellazione inviato.")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Password errata.")

# --- 🖨️ STAMPA ---
elif scelta == "🖨️ Stampa":
    st.image(PATH_STAMPA, width=150)
    st.title("Centro Stampa Etichette Professionale")
    
    inv_totale = db.visualizza_inventario()
    pos_totale = db.visualizza_posizioni()
    
    filtro_st = st.text_input("🔍 Cerca per Nome, Proprietario o Zona", placeholder="Es: Victor, Garage, Scarpe...")
    
    if filtro_st:
        tab_s, tab_u = st.tabs(["📦 Etichette Scatole", "📍 Etichette Ubicazioni"])
        
        with tab_s:
            f = filtro_st.lower()
            # ✅ Filtro Scatole
            inv_da_mostrare = [
                s for s in inv_totale 
                if f in str(s.get('nome','')).lower() or 
                   f in str(s.get('proprietario','')).lower() or 
                   f in str(s.get('descrizione','')).lower()
            ]
            
            sel_s = []
            if inv_da_mostrare:
                for s in inv_da_mostrare:
                    nome_s = s.get('nome', 'N/A')
                    prop_s = s.get('proprietario', 'N/A')
                    id_db = s.get('id')
                    if st.checkbox(f"📦 {nome_s} | 👤 {prop_s}", key=f"st_{id_db}"):
                        sel_s.append(s)
                
                if sel_s and st.button("📥 GENERA PDF SCATOLE", use_container_width=True):
                    pdf = FPDF()
                    for i in range(0, len(sel_s), 2):
                        pdf.add_page()
                        for idx, s in enumerate(sel_s[i:i+2]):
                            y_start = 10 if idx == 0 else 150
                            nome_e = str(s.get('nome', 'N/A'))
                            prop_e = str(s.get('proprietario', 'N/A')).upper()
                            pdf.rect(10, y_start, 190, 130)
                            pdf.set_font("Arial", 'B', 40); pdf.set_xy(15, y_start + 15); pdf.cell(110, 20, prop_e)
                            pdf.set_font("Arial", 'B', 25); pdf.set_xy(15, y_start + 45); pdf.multi_cell(110, 12, nome_e)
                            
                            qr = QRCode(box_size=5); qr.add_data(nome_e); qr.make()
                            img = qr.make_image(); t_img = f"qr_s_{idx}.png"; img.save(t_img)
                            pdf.image(t_img, x=125, y=y_start + 30, w=65)
                    st.download_button("💾 Scarica PDF Scatole", pdf.output(dest='S').encode('latin-1'), "etichette_vhd.pdf")

        with tab_u:
            # ✅ FIX: Ricerca Ubicazioni (Cerca per ID o per Zona)
            f_u = filtro_st.lower()
            pos_da_mostrare = [
                p for p in pos_totale 
                if f_u in str(p.get('id','')).lower() or f_u in str(p.get('zona','')).lower()
            ]
            
            if pos_da_mostrare:
                st.write(f"📍 Trovate {len(pos_da_mostrare)} ubicazioni")
                sel_p = []
                for p in pos_da_mostrare:
                    id_p = p.get('id')
                    zona_p = p.get('zona')
                    if st.checkbox(f"📍 {id_p} (Zona: {zona_p})", key=f"stp_{id_p}"):
                        sel_p.append(p)
                
                if sel_p and st.button("📥 GENERA PDF UBICAZIONI", use_container_width=True):
                    pdf_u = FPDF()
                    for p in sel_p:
                        pdf_u.add_page()
                        pdf_u.rect(10, 10, 190, 130)
                        pdf_u.set_font("Arial", 'B', 50); pdf_u.set_xy(15, 30); pdf_u.cell(180, 40, p.get('id'), align='C')
                        pdf_u.set_font("Arial", 'B', 20); pdf_u.set_xy(15, 80); pdf_u.cell(180, 20, p.get('zona').upper(), align='C')
                    st.download_button("💾 Scarica PDF Ubicazioni", pdf_u.output(dest='S').encode('latin-1'), "ubicazioni_vhd.pdf")
            else:
                st.warning("Nessuna ubicazione trovata.")
