import streamlit as st
import pandas as pd
from db_manager import InventarioDB
from qrcode import QRCode
import io
import os
import time
from fpdf import FPDF
from datetime import datetime
import cloudinary
import cloudinary.uploader
from streamlit_qrcode_scanner import qrcode_scanner

# --- CONFIGURAZIONE PERCORSI IMMAGINI ---
import os

# --- CONFIGURAZIONE PERCORSI (Dopo aver rinominato i file in assets) ---
ASSETS_DIR = "assets"

def check_img(nome_file):
    path = os.path.join(ASSETS_DIR, nome_file)
    if os.path.exists(path):
        return path
    # Se il file manca, usiamo un placeholder per non far crashare Streamlit
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

# --- ESTETICA PROFESSIONALE (FIX VISIBILITÀ CELLULARE) ---
st.markdown("""
    <style>
    .main { 
        background-color: #f0f2f6; 
    }
    [data-testid="stSidebar"] { 
        background-color: #001f3f; 
    }
    [data-testid="stSidebar"] * { 
        color: white !important; 
        font-size: 1.1rem; 
    }
    h1, h2, h3, p, span, label, .stMarkdown { 
        color: #001f3f !important; 
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
    }
    .stMetric { 
        background-color: #ffffff; 
        padding: 15px; 
        border-radius: 10px; 
        border-left: 5px solid #007bff; 
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1); 
    }
    .stExpander { 
        background-color: white !important; 
        border: 1px solid #007bff; 
        border-radius: 10px; 
    }
    .big-emoji { 
        font-size: 3rem !important; 
        margin-bottom: 0; 
    }
    .data-piccola { 
        font-size: 0.85rem; 
        color: #555 !important; 
        font-style: italic; 
    }
    </style>
    """, unsafe_allow_html=True)

db = InventarioDB()
utenti = ["Victor", "Evelyn", "Daniel", "Carly", "Rebby"]
menu = ["🏠 Home", "🔍 Cerca ed Elimina", "📸 Scanner QR", "➕ Nuova Scatola", "🔄 Alloca/Sposta", "⚙️ Configura Magazzino", "🖨️ Stampa"]
scelta = st.sidebar.selectbox("Menu Principale", menu)

# --- CONFIGURAZIONE IMMAGINI ---
# Sostituiamo il link esterno con il tuo file locale
NO_PHOTO = "assets/no_image.png"

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
# --- 🏠 HOME ---
if scelta == "🏠 Home":
    # Immagine di testata
    st.image(PATH_HOME, width=150)
    st.title("Inventario Casa VHD")
    st.info("Benvenuto nel sistema di gestione WMS. Qui trovi il riepilogo del tuo magazzino.")
    st.write("---")
    
    inv = db.visualizza_inventario()
    pos = db.visualizza_posizioni()
    
    # --- SEZIONE METRICHE ---
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📦 Scatole", len(inv))
    
    zone_uniche = len(set([p[1] for p in pos])) if pos else 0
    c2.metric("📍 Zone", zone_uniche)
    
    c3.metric("📌 Ubicazioni", len(pos))
    
    da_allocare = len([s for s in inv if s[11] == "NON ALLOCATA"])
    c4.metric("⚠️ Da Allocare", da_allocare, delta=da_allocare, delta_color="inverse" if da_allocare > 0 else "normal")
    
    st.write("---")

    # --- 📊 1. TABELLA ULTIME 10 SCATOLE ---
    if inv:
        df = pd.DataFrame(inv, columns=[
            "ID", "Nome", "Desc", "Foto", "Cima", "FC", 
            "Centro", "FCE", "Fondo", "FF", "Zona", 
            "Ubicazione", "Proprietario", "Data"
        ])
        
        st.subheader("📊 Ultime 10 Scatole Registrate")
        mostra_df = df[["Nome", "Zona", "Ubicazione", "Proprietario", "Data"]].tail(10).iloc[::-1]
        
        st.dataframe(
            mostra_df, 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "Data": st.column_config.TextColumn("📅 Data"),
                "Nome": st.column_config.TextColumn("📦 Nome Scatola"),
                "Ubicazione": st.column_config.TextColumn("📌 Posizione")
            }
        )
        
        # Esportazione rapida Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Inventario')
        
        st.download_button(
            label="📊 Scarica Report Excel",
            data=output.getvalue(),
            file_name=f"Inventario_VHD_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.warning("Il database è vuoto. Inizia registrando una nuova scatola!")

    st.write("---")

    # --- 🗺️ 2. MAPPA GRAFICA DEL MAGAZZINO ---
    st.subheader("🗺️ Mappa Occupazione Magazzino")
    st.caption("🟢 Libera | 🔴 Occupata | Passa il mouse per il nome della scatola")
    
    if not pos:
        st.warning("Nessuna ubicazione configurata.")
    else:
        mappa_occupazione = {s[11]: s[1] for s in inv if s[11] != "NON ALLOCATA"}
        
        cols_per_row = 12
        for i in range(0, len(pos), cols_per_row):
            batch = pos[i:i + cols_per_row]
            cols = st.columns(cols_per_row)
            for j, p in enumerate(batch):
                id_u = p[0]
                with cols[j]:
                    if id_u in mappa_occupazione:
                        st.markdown(
                            f"""<div style="background-color:#FF4B4B; color:white; padding:5px; 
                            border-radius:3px; text-align:center; font-size:8px; border:1px solid #ddd; line-height:1;" 
                            title="Scatola: {mappa_occupazione[id_u]}">
                            📦<br>{id_u}</div>""", 
                            unsafe_allow_html=True
                        )
                    else:
                        st.markdown(
                            f"""<div style="background-color:#28A745; color:white; padding:5px; 
                            border-radius:3px; text-align:center; font-size:8px; border:1px solid #ddd; line-height:1;" 
                            title="LIBERA">
                            ✅<br>{id_u}</div>""", 
                            unsafe_allow_html=True
                        )

    # --- 💾 3. SEZIONE BACKUP DATABASE (.db) ---
    st.write("---")
    st.subheader("⚙️ Amministrazione")
    try:
        with open("vhd_warehouse.db", "rb") as f:
            db_byte = f.read()
        
        st.download_button(
            label="💾 Scarica File Database (.db)",
            data=db_byte,
            file_name=f"vhd_warehouse_base.db",
            mime="application/octet-stream",
            help="Scarica questo file per caricarlo come base su GitHub"
        )
    except Exception as e:
        st.error(f"Impossibile leggere il file database: {e}")
        


# --- 🔍 CERCA ED ELIMINA ---
elif scelta == "🔍 Cerca ed Elimina":
    # Immagine di sezione centrata (dalla cartella assets)
    st.image(PATH_CERCA, width=150)
    st.title("Gestione e Ricerca Database")
    st.info("Cerca una scatola per nome, contenuto o proprietario per visualizzarne i dettagli o eliminarla.")
    st.write("---")

    # Stile CSS per la data piccola e le etichette
    st.markdown("""
        <style>
        .data-piccola { font-size: 14px; color: #666; font-style: italic; margin-bottom: 10px; }
        .label-interna { font-weight: bold; color: #1f77b4; }
        </style>
    """, unsafe_allow_html=True)

    # Campo di ricerca dinamico
    chiave = st.text_input("🔍 Cosa stai cercando?", placeholder="Esempio: Viti, Garage, Victor...")
    
    # Esegue la ricerca o mostra tutto l'inventario
    ris = db.cerca_scatola(chiave) if chiave else db.visualizza_inventario()
    
    if ris:
        st.write(f"Trovate {len(ris)} scatole.")
        for r in ris:
            # r[13] è la colonna DATA nel tuo database
            data_label = r[13] if len(r) > 13 and r[13] else "Data N.D."
            
            # Intestazione Expander: Nome | Zona - Ubicazione | Proprietario
            with st.expander(f"📦 {r[1]} | 📍 {r[10]} - {r[11]} | 👤 {r[12]}"):
                st.markdown(f"<p class='data-piccola'>📅 Registrata il: {data_label}</p>", unsafe_allow_html=True)
                
                col_info1, col_info2 = st.columns([1, 2])
                
                with col_info1:
                    # Foto principale esterna (Usa NO_PHOTO locale se manca l'URL Cloudinary)
                    st.image(r[3] if r[3] else NO_PHOTO, use_container_width=True, caption="Vista Esterna")
                
                with col_info2:
                    st.write(f"**📝 Descrizione:**")
                    st.write(r[2] if r[2] else "Nessuna descrizione inserita.")
                    st.write("---")
                    st.subheader("📸 Contenuto Interno (Livelli)")
                    
                    # Griglia per le 3 foto dei livelli (Cima, Centro, Fondo)
                    i1, i2, i3 = st.columns(3)
                    
                    with i1:
                        st.image(r[5] if r[5] else NO_PHOTO, use_container_width=True)
                        st.caption(f"🔼 TOP: {r[4]}")
                    
                    with i2:
                        st.image(r[7] if r[7] else NO_PHOTO, use_container_width=True)
                        st.caption(f"↔️ MID: {r[6]}")
                        
                    with i3:
                        st.image(r[9] if r[9] else NO_PHOTO, use_container_width=True)
                        st.caption(f"🔽 BOT: {r[8]}")
                
                st.write("---")
                # Tasto per eliminazione sicura
                if st.button(f"🗑️ ELIMINA DEFINITIVAMENTE: {r[1]}", key=f"del_{r[0]}", use_container_width=True):
                    db.elimina_scatola(r[0])
                    st.warning(f"La scatola '{r[1]}' è stata rimossa correttamente.")
                    time.sleep(1)
                    st.rerun()
    else:
        st.warning("Nessun risultato trovato. Prova con una parola chiave diversa.")        

# --- 📸 SCANNER QR ---
elif scelta == "📸 Scanner QR":
    st.image(PATH_SCANNER, width=100)
    st.title("Scanner Rapido VHD")
    st.info("Punta la fotocamera del tuo telefono o del PC verso il codice QR della scatola.")
    st.write("---")

    # Avvio dello scanner
    # Nota: Questo componente richiede i permessi della fotocamera nel browser
    barcode = qrcode_scanner(key='scanner')

    if barcode:
        st.beep() # Un piccolo suono di conferma (se supportato dal browser)
        st.success(f"🔍 Codice rilevato: {barcode}")
        
        # Cerchiamo la scatola nel database usando il codice letto
        risultato = db.cerca_scatola(barcode)
        
        if risultato:
            # Mostriamo solo la prima scatola trovata (quella corrispondente al QR)
            r = risultato[0]
            st.markdown(f"### ✅ Scatola Trovata: {r[1]}")
            
            with st.expander("Visualizza Dettagli Completi", expanded=True):
                st.write(f"**📍 Ubicazione:** {r[10]} - {r[11]}")
                st.write(f"**👤 Proprietario:** {r[12]}")
                st.write(f"**📝 Descrizione:** {r[2]}")
                
                c1, c2 = st.columns(2)
                # Foto Esterna
                c1.image(r[3] if r[3] else NO_PHOTO, use_container_width=True, caption="Foto Esterna")
                
                # Info Contenuto Rapido
                c2.info(f"🔼 **Cima:** {r[4]}\n\n↔️ **Centro:** {r[6]}\n\n🔽 **Fondo:** {r[8]}")
                
                # Tasto per andare alla gestione della scatola
                if st.button(f"🔄 Vai a Sposta/Alloca {r[1]}"):
                    # Qui potremmo aggiungere una logica per saltare alla sezione sposta
                    st.info("Funzione in fase di sviluppo: usa il menu a sinistra per spostarla.")
        else:
            st.error(f"❌ Nessuna scatola trovata con il nome '{barcode}' nel database.")
            if st.button("➕ Registrala come nuova"):
                st.info("Vai alla sezione 'Nuova Scatola' dal menu laterale.")

    st.write("---")
    with st.expander("💡 Istruzioni Scanner"):
        st.write("""
        1. Assicurati di aver dato i permessi per la fotocamera.
        2. Mantieni il codice QR al centro dell'inquadratura.
        3. Se il QR non viene letto, prova ad aumentare la luminosità o la distanza.
        """)

# --- ➕ NUOVA SCATOLA ---
elif scelta == "➕ Nuova Scatola":
    st.image(PATH_NUOVA, width=150)
    st.title("Registra Nuova Scatola")
    st.info("Compila i campi sottostanti. Le foto verranno caricate automaticamente su Cloudinary.")
    st.write("---")

    with st.form("n_s", clear_on_submit=True):
        # Informazioni Generali
        col_top1, col_top2 = st.columns([2, 1])
        with col_top1:
            nome = st.text_input("📦 Nome Scatola", placeholder="Esempio: SCATOLA_001")
            desc = st.text_area("📝 Descrizione Generale", placeholder="Cosa contiene in generale?")
        with col_top2:
            prop = st.selectbox("👤 Proprietario", utenti)
            f_m = st.file_uploader("📸 Foto Esterna", type=['jpg', 'png', 'jpeg'])

        st.write("---")
        st.subheader("🔍 Dettaglio Contenuto Interno")
        
        # Griglia per i 3 livelli
        # Livello Cima
        c1, c2 = st.columns([2, 1])
        ct = c1.text_input("🔼 Livello SUPERIORE (Cima)", placeholder="Contenuto in alto...")
        cf = c2.file_uploader("Foto Cima", key="fcima", type=['jpg', 'png'])
        
        # Livello Centro
        m1, m2 = st.columns([2, 1])
        mt = m1.text_input("↔️ Livello CENTRALE", placeholder="Contenuto al centro...")
        mf = m2.file_uploader("Foto Centro", key="fcentro", type=['jpg', 'png'])
        
        # Livello Fondo
        b1, b2 = st.columns([2, 1])
        bt = b1.text_input("🔽 Livello INFERIORE (Fondo)", placeholder="Contenuto sul fondo...")
        bf = b2.file_uploader("Foto Fondo", key="ffondo", type=['jpg', 'png'])
        
        st.write("---")
        
        # Pulsante di invio con stile
        submit = st.form_submit_button("🚀 REGISTRA NEL DATABASE", use_container_width=True)
        
        if submit:
            if nome:
                with st.spinner("☁️ Caricamento foto e salvataggio in corso..."):
                    # Caricamento immagini su Cloudinary
                    u1 = upload_foto(f_m, nome, "main")
                    u2 = upload_foto(cf, nome, "cima")
                    u3 = upload_foto(mf, nome, "centro")
                    u4 = upload_foto(bf, nome, "fondo")
                    
                    # Salvataggio nel DB (Data viene gestita dal DB o passata come stringa se necessario)
                    db.aggiungi_scatola(
                        nome, desc, u1, 
                        ct, u2, 
                        mt, u3, 
                        bt, u4, 
                        "DA DEFINIRE", "NON ALLOCATA", prop
                    )
                    
                    st.balloons() # Effetto festa per successo!
                    st.success(f"✅ Scatola '{nome}' registrata con successo!")
                    time.sleep(2)
                    st.rerun()
            else:
                st.error("⚠️ Il nome della scatola è obbligatorio!")


# --- 🔄 ALLOCA/SPOSTA ---
# --- 🔄 ALLOCA/SPOSTA ---
elif scelta == "🔄 Alloca/Sposta":
    st.image(PATH_SPOSTA, width=150)
    st.title("Movimentazione e Allocazione")
    st.write("---")

    inv = db.visualizza_inventario()
    pos = db.visualizza_posizioni()

    # Controllo 1: Esistono le posizioni?
    if not pos:
        st.error("❌ Il magazzino è vuoto. Carica le ubicazioni in 'Configura Magazzino' prima di continuare.")
    
    # Controllo 2: Esistono le scatole?
    elif not inv:
        st.warning("📦 Non ci sono scatole registrate. Vai in 'Nuova Scatola' per crearne una.")
    
    # Se entrambi esistono, mostriamo il modulo
    else:
        col_move1, col_move2 = st.columns(2)
        
        with col_move1:
            st.subheader("📦 Selezione Scatola")
            scatole_list = [f"{s[0]} | {s[1]} (Attuale: {s[11]})" for s in inv]
            s_sel = st.selectbox("Scegli la scatola da muovere", scatole_list)
        
        with col_move2:
            st.subheader("📍 Destinazione")
            # Qui vediamo se le 8 posizioni appaiono
            pos_list = [f"{p[1]} - {p[0]}" for p in pos]
            p_sel = st.selectbox("Scegli la nuova ubicazione", pos_list)

        st.write("---")
        
        ids = int(s_sel.split(" | ")[0])
        nome_scatola = s_sel.split(" | ")[1].split(" (")[0]
        zn, un = p_sel.split(" - ")

        st.warning(f"Stai per spostare **{nome_scatola}** in **{zn}** presso l'ubicazione **{un}**.")

        if st.button("✅ CONFERMA SPOSTAMENTO", use_container_width=True):
            with st.spinner("Aggiornamento registro in corso..."):
                db.aggiorna_posizione_scatola(ids, zn, un)
                st.success(f"Movimentazione completata!")
                time.sleep(1.5)
                st.rerun()

# --- ⚙️ CONFIGURA ---
# --- ⚙️ CONFIGURA ---
elif scelta == "⚙️ Configura Magazzino":
    st.image(PATH_CONFIG, width=100)
    st.title("Impostazioni Motore WMS")
    st.warning("🚨 **Area Amministrativa**: Qui gestisci le ubicazioni e la struttura del database.")
    st.write("---")

    t1, t2, t3 = st.tabs(["➕ Nuova Ubicazione", "📥 Import Excel", "🗑️ Gestione/Elimina"])
    
    with t1:
        st.subheader("Aggiungi Singola Posizione")
        with st.form("p", clear_on_submit=True):
            col_p1, col_p2 = st.columns(2)
            s = col_p1.text_input("🆔 ID Scaffale/Ubicazione", placeholder="es: A-01-01")
            z = col_p2.text_input("📍 Zona", placeholder="es: ZONA_A")
            
            if st.form_submit_button("➕ SALVA POSIZIONE"):
                if s and z:
                    db.aggiungi_posizione(s, z)
                    st.success(f"Ubicazione {s} creata in {z}")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Entrambi i campi sono obbligatori!")
    
    with t2:
        st.subheader("Caricamento Massivo")
        st.info("Carica un file Excel con le colonne 'ID' e 'Zona'. Il sistema riconoscerà automaticamente anche nomi simili.")
        
        file_ex = st.file_uploader("Seleziona file .xlsx", type=['xlsx'], key="bulk_upload_key")
        
        if file_ex:
            # Anteprima per controllo utente
            df_pos = pd.read_excel(file_ex)
            st.write("👀 Anteprima dei dati trovati nel file:")
            st.dataframe(df_pos.head(10), use_container_width=True)
            
            if st.button("🚀 AVVIA IMPORTAZIONE", use_container_width=True):
                with st.spinner("Importazione e sincronizzazione in corso..."):
                    # Usiamo la nuova funzione con il valore di ritorno (successo, conteggio)
                    successo, conteggio = db.import_posizioni_da_df(df_pos)
                    
                    if successo:
                        st.success(f"✅ Configurazione completata! Caricate {conteggio} ubicazioni correttamente.")
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error("❌ Errore: Non ho trovato colonne valide come 'ID' e 'Zona' nel file.")
            
    with t3:
        st.subheader("Manutenzione Ubicazioni")
        p_list = db.visualizza_posizioni()
        if p_list:
            p_del = st.selectbox("Scegli l'ubicazione da rimuovere:", [f"{p[0]} ({p[1]})" for p in p_list])
            if st.button("🗑️ ELIMINA DEFINITIVAMENTE"):
                id_da_eliminare = p_del.split(" (")[0]
                db.elimina_posizione(id_da_eliminare)
                st.warning(f"Ubicazione {id_da_eliminare} rimossa.")
                time.sleep(1)
                st.rerun()
        else:
            st.write("Nessuna ubicazione presente.")

    st.markdown("<br><br>", unsafe_allow_html=True)
    st.write("---")
    
    # Sezione Pericolosa - Reset Totale
    with st.expander("🚨 ZONA PERICOLOSA: RESET TOTALE DATABASE"):
        st.error("Questa azione cancellerà TUTTE le scatole e TUTTE le ubicazioni. Non si può tornare indietro.")
        pwd = st.text_input("Inserisci la Password di Amministratore", type="password")
        if st.button("🔥 AZZERA TUTTO IL SISTEMA"):
            if pwd == "233674":
                with st.spinner("Cancellazione in corso..."):
                    conn = db.connetti_db()
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM inventario")
                    cursor.execute("DELETE FROM posizioni")
                    conn.commit()
                    conn.close()
                    st.success("Database azzerato correttamente.")
                    time.sleep(2)
                    st.rerun()
            else:
                st.error("Password errata!")
# --- 🖨️ STAMPA ---
# --- 🖨️ STAMPA ---
elif scelta == "🖨️ Stampa":
    st.image(PATH_STAMPA, width=150)
    st.title("Centro Stampa Etichette Professionale")
    st.info("Cerca le scatole o le ubicazioni per generare i file PDF pronti per la stampa.")
    st.write("---")
    
    # Inizializziamo il testo del filtro e il contatore reset nella memoria se non esistono
    if "filtro_stampa" not in st.session_state:
        st.session_state.filtro_stampa = ""
    if "reset_ctr" not in st.session_state:
        st.session_state.reset_ctr = 0

    # --- BARRA DEGLI STRUMENTI ---
    col_t1, col_t2 = st.columns([2, 1])
    
    with col_t2:
        if st.button("🗑️ RESET TOTALE PAGINA", use_container_width=True, help="Pulisce filtri e selezioni"):
            for k in list(st.session_state.keys()):
                if k.startswith("st_") or k.startswith("up_"):
                    del st.session_state[k]
            st.session_state.filtro_stampa = ""
            st.session_state.reset_ctr += 1
            st.rerun()

    with col_t1:
        filtro_veloce = st.text_input("🔍 Filtro rapido (Zona, Nome o Contenuto)", 
                                     value=st.session_state.filtro_stampa, 
                                     placeholder="Scrivi qui per filtrare...",
                                     key="campo_ricerca")
        st.session_state.filtro_stampa = filtro_veloce

    st.write("---")

    # SE IL FILTRO È VUOTO, NON MOSTRIAMO NULLA
    if not filtro_veloce:
        st.info("💡 Digita qualcosa nella barra di ricerca sopra per visualizzare le etichette disponibili.")
    else:
        tab_s, tab_u = st.tabs(["📦 Etichette Scatole", "📍 Etichette Ubicazioni"])
        
        # --- TAB SCATOLE ---
        with tab_s:
            inv_da_mostrare = db.cerca_scatola(filtro_veloce)
            if inv_da_mostrare:
                col_btn1, col_btn2 = st.columns(2)
                if col_btn1.button("✅ Seleziona tutte le scatole", key="sel_all_s"):
                    for s in inv_da_mostrare:
                        st.session_state[f"st_{s[0]}_{st.session_state.reset_ctr}"] = True
                    st.rerun()

                sel_s = []
                # Visualizzazione lista con checkbox
                for s in inv_da_mostrare:
                    key = f"st_{s[0]}_{st.session_state.reset_ctr}"
                    if st.checkbox(f"📦 {s[1]} | 👤 {s[12]} | 📍 {s[10]}", key=key, value=st.session_state.get(key, False)):
                        sel_s.append(s)
                
                if sel_s:
                    st.write(f"✅ {len(sel_s)} scatole selezionate")
                    if st.button("📥 GENERA PDF SCATOLE", use_container_width=True):
                        pdf = FPDF()
                        for i in range(0, len(sel_s), 2):
                            pdf.add_page()
                            for idx, s in enumerate(sel_s[i:i+2]):
                                y = 10 if idx == 0 else 150
                                pdf.rect(10, y, 190, 130)
                                # Intestazione Proprietario (Grande)
                                pdf.set_font("Arial", 'B', 40); pdf.set_xy(15, y+15)
                                pdf.cell(0, 20, f"{s[12]}".upper(), ln=True)
                                # Nome Scatola
                                pdf.set_font("Arial", 'B', 25); pdf.set_xy(15, y+40)
                                pdf.cell(0, 15, f"{s[1]}", ln=True)
                                # Data in basso
                                pdf.set_font("Arial", 'I', 10); pdf.set_xy(15, y+120)
                                pdf.cell(0, 10, f"Registrata il: {s[13]}", ln=False)
                                # QR Code
                                qr = QRCode(box_size=5); qr.add_data(s[1]); qr.make()
                                img = qr.make_image(); img.save("t.png")
                                pdf.image("t.png", x=125, y=y+35, w=65)
                        
                        st.download_button("💾 Scarica Etichette PDF", pdf.output(dest='S').encode('latin-1'), "etichette_vhd.pdf")
            else:
                st.warning("Nessuna scatola corrisponde al filtro.")

        # --- TAB UBICAZIONI ---
        with tab_u:
            pos_complete = db.visualizza_posizioni()
            pos_da_mostrare = [p for p in pos_complete if filtro_veloce.lower() in str(p).lower()]
            
            if pos_da_mostrare:
                if st.button("✅ Seleziona tutte le ubicazioni", key="sel_all_u"):
                    for p in pos_da_mostrare:
                        st.session_state[f"up_{p[0]}_{st.session_state.reset_ctr}"] = True
                    st.rerun()

                sel_p = []
                for p in pos_da_mostrare:
                    key_pos = f"up_{p[0]}_{st.session_state.reset_ctr}"
                    if st.checkbox(f"📍 {p[1]} - {p[0]}", key=key_pos, value=st.session_state.get(key_pos, False)):
                        sel_p.append(p)
                
                if sel_p:
                    st.write(f"✅ {len(sel_p)} ubicazioni selezionate")
                    if st.button("📥 GENERA PDF UBICAZIONI", use_container_width=True):
                        pdf = FPDF()
                        for i in range(0, len(sel_p), 16):
                            pdf.add_page()
                            for idx, p in enumerate(sel_p[i:i+16]):
                                col, row = idx % 4, idx // 4
                                x, y = 10+(col*48), 10+(row*70)
                                pdf.rect(x, y, 45, 65)
                                pdf.set_font("Arial", 'B', 8); pdf.text(x+2, y+8, f"{p[1]}")
                                pdf.set_font("Arial", 'B', 12); pdf.text(x+2, y+18, f"ID: {p[0]}")
                                qr = QRCode(box_size=3); qr.add_data(p[0]); qr.make()
                                img = qr.make_image(); img.save("t_u.png")
                                pdf.image("t_u.png", x=x+5, y=y+22, w=35)
                        
                        st.download_button("💾 Scarica PDF Ubicazioni", pdf.output(dest='S').encode('latin-1'), "ubicazioni_vhd.pdf")
