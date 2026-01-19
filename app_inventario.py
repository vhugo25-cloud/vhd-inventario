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
    return "https://via.placeholder.com/150x150.png?text=VHD+Inventario"

# Percorsi immagini (Assicurati che i file siano .png nella cartella assets)
PATH_HOME     = check_img("home.png")
PATH_NUOVA    = check_img("nuova.png")
PATH_MODIFICA = check_img("modifica.png") # Aggiunto per la nuova sezione
PATH_CERCA    = check_img("cerca.png")
PATH_SPOSTA   = check_img("sposta.png")
PATH_SCANNER  = check_img("scanner.png")
PATH_CONFIG   = check_img("config.png")
PATH_STAMPA   = check_img("stampa.png")
NO_PHOTO      = check_img("no_image.png")

# --- DIZIONARIO LOGHI (Per automazione) ---
LOGHI = {
    "🏠 Home": PATH_HOME,
    "🔍 Cerca ed Elimina": PATH_CERCA,
    "➕ Nuova Scatola": PATH_NUOVA,
    "📝 Modifica Scatola": PATH_MODIFICA,
    "📸 Scanner QR": PATH_SCANNER,
    "🔄 Alloca/Sposta": PATH_SPOSTA,
    "⚙️ Configura Magazzino": PATH_CONFIG,
    "🖨️ Stampa": PATH_STAMPA
}

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

# --- ESTETICA PROFESSIONALE (ALTO CONTRASTO CIANO NEON) ---
st.markdown("""
    <style>
    @media (prefers-color-scheme: dark) {
        .stApp { background-color: #0E1117; }
        h1, h2, h3, p, span, label, .stMarkdown { color: #FFFFFF !important; }
        [data-testid="stMetric"] { 
            background-color: #161B22 !important; 
            border: 1px solid #00FBFF !important;
            box-shadow: 0px 0px 15px rgba(0, 251, 255, 0.1) !important;
        }
        [data-testid="stMetricLabel"] { color: #ADB5BD !important; }
        [data-testid="stMetricValue"] { color: #00FBFF !important; }
    }
    @media (prefers-color-scheme: light) {
        h1, h2, h3, p, span, label, .stMarkdown { color: #001f3f !important; }
        [data-testid="stMetric"] { 
            background-color: #ffffff !important; 
            border-left: 5px solid #007bff !important;
        }
    }
    [data-testid="stSidebar"] { background-color: #001f3f !important; }
    [data-testid="stSidebar"] * { color: white !important; font-size: 1.05rem; }
    .stExpander { border: 1px solid #007bff !important; border-radius: 10px; }
    img { border-radius: 15px; margin-bottom: 15px; border: 1px solid rgba(0,251,255,0.2); }
    div[style*="background-color"] { border: 1px solid rgba(255,255,255,0.1) !important; }
    </style>
    """, unsafe_allow_html=True)

# --- INIZIALIZZAZIONE DATABASE ---
db = db_manager.InventarioDB()
utenti = ["Victor", "Evelyn", "Daniel", "Carly", "Rebby"]

# --- GESTIONE MENU UNICO (PULITO) ---
# Usiamo solo questo, così i loghi funzionano sempre
scelta = st.sidebar.selectbox("Inventario Casa Hernandez", list(LOGHI.keys()))
st.image(LOGHI[scelta], width=180) 

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
# --- 🏠 HOME ---
if scelta == "🏠 Home":
    st.title("Inventario Casa Hernandez")
    
    # --- RECUPERO DATI ---
    inv_data = db.visualizza_inventario()
    pos = db.visualizza_posizioni()

    col_testo, col_bottone = st.columns([2, 1])
    with col_bottone:
        if st.button("🔗 Sistema offline?", type="secondary", use_container_width=True):
            with st.spinner("Sveglia database..."):
                ok, msg = db.sveglia_database()
                if ok:
                    st.toast("Connesso!", icon="✅")
                    st.rerun()

    # --- 📖 GLOSSARIO E CONSIGLI (Stile Giallo Oro) ---
    st.markdown("""
        <style>
        .glossario-box {
            background-color: #FFD700; 
            padding: 20px; 
            border-radius: 12px; 
            border-left: 8px solid #FFA500;
            margin-bottom: 25px;
            box-shadow: 2px 2px 10px rgba(0,0,0,0.2);
        }
        .glossario-box h3, .glossario-box p, .glossario-box li {
            color: #1a1a1a !important; /* Testo scuro per massimo contrasto su giallo */
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        .glossario-box b { color: #000 !important; }
        </style>
    """, unsafe_allow_html=True)

    with st.expander("📚 GUIDA RAPIDA E CONSIGLI PER LA FAMIGLIA (Leggi qui!)"):
        st.markdown('<div class="glossario-box">', unsafe_allow_html=True)
        st.markdown("""
        ### 💡 Consigli del Capo Magazziniere
        
        * **🔍 Cerca ed Elimina:** Quando avremo centinaia di scatole, non cercarle a occhio! Usa il filtro **Proprietario** (scrivi Victor, Evelyn, ecc.) per vedere subito solo le tue cose. 
        * **🖨️ Stampa Etichette:** **Consiglio risparmio:** Non stampare una scatola alla volta. Aspetta di averne almeno due e stampale insieme per risparmiare carta e adesivi!
        * **🖼️ Livelli Interni:** Fai sempre le foto di **Cima, Centro e Fondo**. Ti serviranno per sapere cosa c'è sotto senza dover tirare fuori tutto fisicamente.
        * **📍 Allocazione:** Se vedi scatole in "⚠️ Da Allocare", significa che sono "nomadi". Trovagli un posto fisso e registralo subito!
        * **🔄 Regola Hernandez:** Se sposti una scatola fisicamente, il tuo pollice deve spostarla contemporaneamente nell'App. Altrimenti, per il magazzino, è persa!
        """)
        st.markdown('</div>', unsafe_allow_html=True)

    # --- METRICHE E EXPORT ---
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📦 Scatole", len(inv_data))
    
    zone_uniche = len(set([p.get('zona') for p in pos if p.get('zona')])) if pos else 0
    c2.metric("📍 Zone", zone_uniche)
    c3.metric("📌 Ubicazioni", len(pos))

    count_da_allocare = len([s for s in inv_data if not s.get('ubi') or str(s.get('ubi')).strip().upper() in ["", "NON ALLOCATA"]]) if inv_data else 0
    c4.metric("⚠️ Da Allocare", count_da_allocare)
    
    # --- TASTO EXPORT EXCEL ---
    if inv_data:
        import io
        df_exp = pd.DataFrame(inv_data)
        col_utili = ['id', 'nome', 'descrizione', 'proprietario', 'zon', 'ubi', 'cima_testo', 'centro_testo', 'fondo_testo']
        df_exp = df_exp[[c for c in col_utili if c in df_exp.columns]]
        
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df_exp.to_excel(writer, index=False, sheet_name='Inventario')
        
        st.download_button(
            label="📥 Esporta Inventario Completo (Excel)",
            data=buffer,
            file_name="inventario_hernandez.xlsx",
            mime="application/vnd.ms-excel",
            use_container_width=True,
            help="Scarica la lista per lavorare offline o fare un controllo generale"
        )

    st.write("---")
    
    if inv_data:
        df = pd.DataFrame(inv_data)
        st.subheader("📊 Ultime Scatole Registrate")
        mappa_nomi = {"nome": "Nome", "zon": "Zona", "ubi": "Ubicazione", "proprietario": "Proprietario"}
        cols_esistenti = [c for c in mappa_nomi.keys() if c in df.columns]
        st.dataframe(df[cols_esistenti].tail(5).rename(columns=mappa_nomi), use_container_width=True, hide_index=True)
    
    st.write("---")
    
    # --- 🗺️ MAPPA OCCUPAZIONE MAGAZZINO ---
    st.subheader("🗺️ Mappa Occupazione Magazzino")
    if pos:
        mappa_occupazione = {
            str(s.get('ubi', '')).strip().upper(): s.get('nome') 
            for s in inv_data if s.get('ubi') and str(s.get('ubi')).upper() != "NON ALLOCATA"
        }
        
        cols_per_row = 12
        for i in range(0, len(pos), cols_per_row):
            batch = pos[i:i + cols_per_row]
            cols = st.columns(cols_per_row)
            for j, p in enumerate(batch):
                id_u_raw = p.get('id_ubicazione') or p.get('id') or p.get('ID') or p.get('id_u')
                id_u = str(id_u_raw).strip().upper() if id_u_raw else "N/D"
                
                piena = id_u in mappa_occupazione
                nome_contenuto = mappa_occupazione.get(id_u, "Libera")
                
                color = "#FF4B4B" if piena else "#28A745"
                icon = "📦" if piena else "✅"
                
                with cols[j]:
                    st.markdown(f'''
                        <div title="Ubicazione: {id_u}&#10;Contenuto: {nome_contenuto}" 
                             style="background-color:{color}; color:white !important; padding:5px; 
                             border-radius:3px; text-align:center; font-size:8px; line-height:1.2;
                             min-height:45px; border: 1px solid rgba(255,255,255,0.2); cursor:help;">
                        <span style="color: white !important;">{icon}</span><br>
                        <span style="color: white !important; font-weight: bold; font-size: 7px;">{id_u}</span>
                        </div>''', unsafe_allow_html=True)
    else:
        st.warning("⚠️ Nessuna ubicazione trovata. Vai in 'Configura' per creare la mappa.")
        



                    
# --- 🔍 CERCA ED ELIMINA ---
# --- 🔍 CERCA ED ELIMINA ---
elif scelta == "🔍 Cerca ed Elimina":
    st.title("Ricerca e Gestione")
    
    chiave = st.text_input("🔍 Cosa stai cercando?", placeholder="Viti, Garage, Victor...", help="Scrivi qui per filtrare i risultati")
    
    with st.spinner("Ricerca in corso..."):
        ris = db.cerca_scatola(chiave) if chiave else db.visualizza_inventario()
    
    if ris:
        st.write(f"✅ Trovate {len(ris)} scatole")
        for r in ris:
            id_db = r.get('id')
            nome = r.get('nome', 'Senza Nome')
            desc = r.get('descrizione', '-')
            zona = r.get('zon', 'N/D')
            ubi = r.get('ubi', 'N/D')
            prop = r.get('proprietario', 'N/D')
            data_reg = r.get('data_inserimento', 'Data non disp.')
            
            f_main = r.get('foto_main') if r.get('foto_main') else NO_PHOTO
            f_cima = r.get('cima_foto') if r.get('cima_foto') else NO_PHOTO
            f_cent = r.get('centro_foto') if r.get('centro_foto') else NO_PHOTO
            f_fond = r.get('fondo_foto') if r.get('fondo_foto') else NO_PHOTO

            with st.expander(f"📦 {nome} | 📍 {zona} - {ubi} | 👤 {prop}"):
                st.markdown(f"<p style='color: #ADB5BD; font-size: 0.8rem;'>📅 Registrata il: {data_reg}</p>", unsafe_allow_html=True)
                
                col1, col2 = st.columns([1, 2])
                with col1:
                    st.image(f_main, use_container_width=True, caption="Vista Esterna")
                
                with col2:
                    st.write(f"**📝 Descrizione:** {desc}")
                    st.markdown("---")
                    st.subheader("🔍 Contenuto Interno")
                    
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
                
                st.write("")
                if st.button(f"🗑️ ELIMINA: {nome}", key=f"del_{id_db}", use_container_width=True):
                    if db.elimina_scatola(id_db):
                        st.warning(f"Scatola '{nome}' rimossa.")
                        time.sleep(1)
                        st.rerun()
    else:
        st.info("Nessuna scatola trovata.")

# --- ➕ NUOVA SCATOLA ---
# --- ➕ NUOVA SCATOLA ---
elif scelta == "➕ Nuova Scatola":
    st.title("Registrazione Nuova Scatola")
    
    # Rimosso clear_on_submit per evitare che i file spariscano prima dell'upload
    with st.form("form_nuova_scatola"):
        col_n, col_p = st.columns(2)
        nome = col_n.text_input("📦 Nome Scatola (es: BOX-001)")
        prop = col_p.selectbox("👤 Proprietario", utenti)
        desc = st.text_area("📝 Descrizione contenuto")
        
        st.write("---")
        st.subheader("📸 Foto Principale (Esterna)")
        f_main = st.file_uploader("Carica foto esterna", type=['png', 'jpg', 'jpeg'], key="main")
        
        st.write("---")
        st.subheader("Contenuto per Livelli")
        
        # Livello Cima
        c1, c2 = st.columns([2, 1])
        t_cima = c1.text_input("Cosa c'è in cima?", key="t_cima_input")
        f_cima = c2.file_uploader("Foto Cima", type=['png', 'jpg', 'jpeg'], key="f_cima_file")
        
        # Livello Centro
        m1, m2 = st.columns([2, 1])
        t_cent = m1.text_input("Cosa c'è al centro?", key="t_cent_input")
        f_cent = m2.file_uploader("Foto Centro", type=['png', 'jpg', 'jpeg'], key="f_cent_file")
        
        # Livello Fondo
        b1, b2 = st.columns([2, 1])
        t_fond = b1.text_input("Cosa c'è sul fondo?", key="t_fond_input")
        f_fond = b2.file_uploader("Foto Fondo", type=['png', 'jpg', 'jpeg'], key="f_fond_file")
        
        submit = st.form_submit_button("🚀 SALVA SCATOLA NEL CLOUD")
        
        if submit:
            if nome:
                with st.spinner("Caricamento immagini in corso..."):
                    # Esecuzione Upload
                    u_main = upload_foto(f_main, nome, "main")
                    u_cima = upload_foto(f_cima, nome, "cima")
                    u_cent = upload_foto(f_cent, nome, "centro")
                    u_fond = upload_foto(f_fond, nome, "fondo")
                    
                    # Log di controllo (visibile solo se qualcosa fallisce)
                    if not u_cima and f_cima: st.error("Errore upload foto Cima")
                    
                    if db.aggiungi_scatola(
                        nome=nome, desc=desc, f_m=u_main, 
                        ct=t_cima, cf=u_cima, 
                        mt=t_cent, mf=u_cent, 
                        bt=t_fond, bf=u_fond, 
                        prop=prop
                    ):
                        st.balloons()
                        st.success(f"✅ Scatola {nome} registrata con tutte le foto!")
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error("❌ Errore nel salvataggio dei dati nel database.")
            else:
                st.error("⚠️ Il nome della scatola è obbligatorio!")

# --- 📝 MODIFICA SCATOLA (NUOVA FUNZIONE) ---
# --- 📝 MODIFICA SCATOLA ---
elif scelta == "📝 Modifica Scatola":
    st.title("Modifica e Aggiornamento Scatola")
    
    inv_data = db.visualizza_inventario()
    
    if inv_data:
        # Selezione scatola per ID e Nome
        nomi_scatole = [f"{s.get('id')} - {s.get('nome')}" for s in inv_data]
        scelta_box = st.selectbox("Scegli la scatola da aggiornare", nomi_scatole)
        
        id_sel = int(scelta_box.split(" - ")[0])
        s = next(item for item in inv_data if item.get('id') == id_sel)
        
        with st.form("form_modifica"):
            st.warning(f"🛠️ Stai modificando la scatola ID: {id_sel}")
            
            col_1, col_2 = st.columns(2)
            nuovo_nome = col_1.text_input("Nuovo Nome", value=s.get('nome'))
            nuovo_prop = col_2.selectbox("Cambia Proprietario", utenti, 
                                          index=utenti.index(s.get('proprietario')) if s.get('proprietario') in utenti else 0)
            
            nuova_desc = st.text_area("Aggiorna Descrizione", value=s.get('descrizione', ''))
            
            st.write("---")
            st.subheader("🖼️ Gestione Immagini (Sostituzione)")
            st.info("💡 Carica un file solo per sostituire la foto attuale. Se lasci vuoto, l'immagine non cambierà.")
            
            # Griglia 2x2 per caricamento foto
            c_f1, c_f2 = st.columns(2)
            f_main_new = c_f1.file_uploader("Sostituisci Foto Esterna", type=['jpg','jpeg','png'], key="mod_main")
            f_cima_new = c_f2.file_uploader("Sostituisci Foto Cima", type=['jpg','jpeg','png'], key="mod_cima")
            
            c_f3, c_f4 = st.columns(2)
            f_cent_new = c_f3.file_uploader("Sostituisci Foto Centro", type=['jpg','jpeg','png'], key="mod_cent")
            f_fond_new = c_f4.file_uploader("Sostituisci Foto Fondo", type=['jpg','jpeg','png'], key="mod_fond")
            
            st.write("---")
            st.subheader("✍️ Testi Livelli Interni")
            t_cima_new = st.text_input("Testo Cima", value=s.get('cima_testo', ''))
            t_cent_new = st.text_input("Testo Centro", value=s.get('centro_testo', ''))
            t_fond_new = st.text_input("Testo Fondo", value=s.get('fondo_testo', ''))

            if st.form_submit_button("✅ SALVA TUTTE LE MODIFICHE"):
                with st.spinner("Aggiornamento immagini su Cloudinary..."):
                    # Caricamento intelligente: nuova foto o mantiene URL esistente
                    url_m = upload_foto(f_main_new, nuovo_nome, "main") if f_main_new else s.get('foto_main')
                    url_ci = upload_foto(f_cima_new, nuovo_nome, "cima") if f_cima_new else s.get('cima_foto')
                    url_ce = upload_foto(f_cent_new, nuovo_nome, "centro") if f_cent_new else s.get('centro_foto')
                    url_fo = upload_foto(f_fond_new, nuovo_nome, "fondo") if f_fond_new else s.get('fondo_foto')
                    
                    # CHIAMATA AL DB: Parametri allineati al nuovo db_manager.py
                    if db.aggiorna_dati_scatola(
                        id_scatola=id_sel, 
                        nome=nuovo_nome, 
                        desc=nuova_desc, 
                        prop=nuovo_prop, 
                        ct=t_cima_new, 
                        mt=t_cent_new, 
                        bt=t_fond_new, 
                        f_main=url_m,
                        f_cima=url_ci,
                        f_cent=url_ce,
                        f_fond=url_fo
                    ):
                        st.success("✨ Modifiche salvate correttamente!")
                        time.sleep(1.5)
                        st.rerun()
                    else:
                        st.error("Errore durante il salvataggio. Controlla il log nel db_manager.")
    else:
        st.info("🔍 Non ci sono scatole registrate da poter modificare.")


# --- 📸 SCANNER QR (Ritorno alla versione VELOCE) ---
elif scelta == "📸 Scanner QR":
    st.title("Scanner Intelligente Hernandez")
    st.info("💡 Inquadra il QR Code per il riconoscimento immediato.")

    # Importiamo il componente che ti piaceva
    from streamlit_qrcode_scanner import qrcode_scanner

    # Usiamo una chiave che cambia ogni volta per "resettare" il componente e non farlo crashare
    import time
    chiave_dinamica = f"scanner_{int(time.time() / 10)}" # Cambia ogni 10 secondi
    
    codice_scansionato = qrcode_scanner(key=chiave_dinamica)

    if codice_scansionato:
        st.success(f"✅ Codice rilevato: {codice_scansionato}")
        inv_data = db.visualizza_inventario()
        
        # Ricerca della scatola
        risultato = [s for s in inv_data if str(s.get('nome', '')).strip().upper() == str(codice_scansionato).strip().upper()]
        
        if risultato:
            r = risultato[0]
            st.markdown("---")
            st.subheader(f"📦 Scatola: {r.get('nome')}")
            
            col_imm, col_info = st.columns([1, 1.5])
            with col_imm:
                # IMPORTANTE: Qui abbiamo tolto border=True che faceva crashare tutto
                st.image(r.get('foto_main') or NO_PHOTO, use_container_width=True)
            
            with col_info:
                st.markdown(f"**📍 Ubicazione:** `{r.get('zon', 'N/D')} - {r.get('ubi', 'N/D')}`")
                st.markdown(f"**👤 Proprietario:** {r.get('proprietario', 'N/D')}")
                st.info(f"**📝 Descrizione:**\n{r.get('descrizione', 'Nessuna descrizione')}")
        else:
            st.error(f"❌ La scatola '{codice_scansionato}' non esiste.")
            
 

# --- 🔄 ALLOCA/SPOSTA ---
# --- 🔄 ALLOCA/SPOSTA ---
elif scelta == "🔄 Alloca/Sposta":
    st.title("Movimentazione e Allocazione")
    
    # Recupero dati
    inv = db.visualizza_inventario()
    pos = db.visualizza_posizioni()
    
    if inv and pos:
        st.info("💡 Seleziona una scatola e la sua nuova destinazione nel magazzino.")
        
        # ✅ Selezione Scatola con ID chiaro
        s_options = {f"{s.get('id')} | {s.get('nome')}": s for s in inv}
        s_sel_key = st.selectbox("📦 Scatola da spostare", options=list(s_options.keys()), 
                                 help="Mostra ID, Nome e posizione attuale")
        
        # ✅ Selezione Posizione
        p_list = []
        for p in pos:
            codice_ubi = p.get('id_ubicazione') or p.get('id') or "N/D"
            nome_zona = p.get('zona', 'N/D')
            p_list.append(f"{nome_zona} | {codice_ubi}")
            
        p_sel = st.selectbox("📍 Nuova Destinazione (Zona | Scaffale)", p_list)
        
        if st.button("🚀 CONFERMA SPOSTAMENTO", use_container_width=True):
            try:
                # Estraiamo l'ID della scatola
                id_scatola = int(s_sel_key.split(" | ")[0])
                
                # Estraiamo Zona e Ubicazione
                nuova_zona, nuova_ubi = p_sel.split(" | ")
                
                with st.spinner("Aggiornamento posizione..."):
                    if db.aggiorna_posizione_scatola(id_scatola, nuova_zona, nuova_ubi):
                        st.success(f"✅ Spostamento completato! Scatola {id_scatola} ora in: {nuova_zona} - {nuova_ubi}")
                        time.sleep(1.5)
                        st.rerun()
                    else:
                        st.error("Errore nel database durante l'aggiornamento.")
            except Exception as e:
                st.error(f"Errore tecnico nella selezione: {e}")
                
        # Anteprima rapida della scatola selezionata
        st.markdown("---")
        s_dati = s_options[s_sel_key]
        st.caption(f"Stato attuale: {s_dati.get('nome')} si trova in {s_dati.get('zon', 'N/D')} - {s_dati.get('ubi', 'N/D')}")

    else:
        if not inv:
            st.warning("⚠️ Non ci sono scatole nell'inventario. Registrane una prima.")
        if not pos:
            st.error("⚠️ Non hai configurato le zone del magazzino. Vai in 'Configura Magazzino'.")


# --- ⚙️ CONFIGURA MAGAZZINO ---
# --- ⚙️ CONFIGURA MAGAZZINO ---
elif scelta == "⚙️ Configura Magazzino":
    st.title("Impostazioni Struttura Magazzino")
    
    # CSS specifico per rendere i Tab più visibili e i Form eleganti
    st.markdown("""<style>
        div.stForm { 
            background-color: rgba(0, 251, 255, 0.03); 
            border: 1px solid rgba(0, 251, 255, 0.2); 
            border-radius: 10px; 
            padding: 20px; 
        }
        .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
            font-size: 1.1rem;
            font-weight: bold;
        }
    </style>""", unsafe_allow_html=True)

    t1, t2, t3 = st.tabs(["➕ Nuova Ubicazione", "📥 Import Excel", "🗑️ Gestione & Reset"])
    
    with t1:
        st.subheader("Registra un nuovo spazio")
        with st.form("p_new", clear_on_submit=True):
            col_id, col_zon = st.columns(2)
            s_id = col_id.text_input("🆔 ID Ubicazione", placeholder="es: A1-01")
            z_id = col_zon.text_input("📍 Nome Zona", placeholder="es: Garage")
            
            if st.form_submit_button("➕ SALVA POSIZIONE", use_container_width=True):
                if s_id and z_id:
                    id_pulito = str(s_id).strip().upper()
                    zona_pulita = str(z_id).strip()
                    
                    if db.aggiungi_posizione(id_pulito, zona_pulita):
                        st.success(f"✅ Ubicazione {id_pulito} creata con successo!")
                        time.sleep(1)
                        st.rerun()
                else:
                    st.error("⚠️ Inserisci sia l'ID che la Zona.")
    
    with t2:
        st.subheader("Caricamento da file Excel")
        st.markdown("""
        💡 **Istruzioni:** Il file deve avere le colonne denominate esattamente **id** e **zona**.
        """)
        file_ex = st.file_uploader("Trascina qui il file .xlsx", type=['xlsx'])
        
        if file_ex:
            try:
                df_pos = pd.read_excel(file_ex)
                df_pos.columns = [c.lower().strip() for c in df_pos.columns]
                
                st.write("🔍 Anteprima dati:")
                st.dataframe(df_pos.head(10), use_container_width=True)
                
                if st.button("🚀 AVVIA IMPORTAZIONE", use_container_width=True):
                    with st.spinner("Sincronizzazione database..."):
                        ok, count = db.import_posizioni_da_df(df_pos)
                        if ok:
                            st.balloons()
                            st.success(f"📥 Ottimo! Caricate {count} nuove posizioni.")
                            time.sleep(2)
                            st.rerun()
            except Exception as e:
                st.error(f"Errore tecnico: {e}")

    with t3:
        st.subheader("🛡️ Sicurezza e Manutenzione")
        pos_attuali = db.visualizza_posizioni()
        st.info(f"Il magazzino Hernandez ha attualmente **{len(pos_attuali)}** ubicazioni attive.")
        
        st.write("---")
        # Inserimento password per sbloccare i tasti di reset
        pwd = st.text_input("🔑 Inserisci Password Master per le azioni pericolose", type="password")
        
        if pwd == "233674":
            st.warning("⚠️ **MODALITÀ ADMIN ATTIVA**: I tasti sottostanti cancellano i dati in modo definitivo.")
            
            col_r1, col_r2 = st.columns(2)
            
            with col_r1:
                if st.button("🔥 RESET TOTALE INVENTARIO", use_container_width=True):
                    with st.spinner("Cancellazione scatole..."):
                        if db.reset_totale_inventario():
                            st.success("Inventario completamente svuotato.")
                            time.sleep(1.5)
                            st.rerun()
            
            with col_r2:
                if st.button("🗑️ RESET TOTALE POSIZIONI", use_container_width=True):
                    with st.spinner("Cancellazione mappa..."):
                        if db.reset_totale_posizioni():
                            st.success("Mappa delle posizioni azzerata.")
                            time.sleep(1.5)
                            st.rerun()
        elif pwd:
            st.error("❌ Password Errata")


# --- 🖨️ STAMPA ---
# --- 🖨️ STAMPA ---
elif scelta == "🖨️ Stampa":
    st.title("Centro Stampa Etichette Hernandez")
    
    inv_totale = db.visualizza_inventario()
    pos_totale = db.visualizza_posizioni()
    
    st.info("💡 Cerca le scatole o le zone, selezionale con la spunta e genera il PDF pronto per la stampa.")
    filtro_st = st.text_input("🔍 Cerca per Nome, Proprietario o Zona", placeholder="Es: Victor, Garage...")
    
    if filtro_st:
        tab_s, tab_u = st.tabs(["📦 Etichette Scatole (A4 x2)", "📍 Etichette Ubicazioni (A4 x16)"])
        
        # --- TAB SCATOLE (2 PER FOGLIO A4) ---
        with tab_s:
            f = filtro_st.lower()
            inv_da_mostrare = [s for s in inv_totale if f in str(s.get('nome','')).lower() or f in str(s.get('proprietario','')).lower()]
            
            sel_s = []
            if inv_da_mostrare:
                for s in inv_da_mostrare:
                    id_s = s.get('id')
                    if st.checkbox(f"📦 {s.get('nome')} | {s.get('proprietario')}", key=f"st_sel_{id_s}"):
                        sel_s.append(s)
                
                if sel_s and st.button("📥 GENERA PDF SCATOLE", use_container_width=True):
                    pdf = FPDF()
                    # Elaborazione a coppie di 2 per pagina
                    for i in range(0, len(sel_s), 2):
                        pdf.add_page()
                        batch_s = sel_s[i:i+2]
                        for idx, s in enumerate(batch_s):
                            # Coordinate ricalibrate: idx 0 (sopra), idx 1 (sotto)
                            y_start = 10 if idx == 0 else 145
                            nome_e = str(s.get('nome', 'N/A'))
                            prop_e = str(s.get('proprietario', 'N/A')).upper()
                            data_e = str(s.get('data_inserimento') or datetime.now().strftime("%d/%m/%Y"))
                            
                            # Disegno Etichetta
                            pdf.rect(10, y_start, 190, 125)
                            pdf.set_font("Arial", 'B', 40); pdf.set_xy(15, y_start + 15); pdf.cell(110, 20, prop_e)
                            pdf.set_font("Arial", 'B', 25); pdf.set_xy(15, y_start + 45); pdf.multi_cell(110, 12, nome_e)
                            pdf.set_font("Arial", '', 10); pdf.set_xy(15, y_start + 115); pdf.cell(100, 10, f"Data: {data_e}")
                            
                            # Generazione QR Code temporaneo
                            qr = QRCode(box_size=5); qr.add_data(nome_e); qr.make()
                            img = qr.make_image(); t_img = f"qr_s_{i}_{idx}.png"; img.save(t_img)
                            pdf.image(t_img, x=125, y=y_start + 25, w=60)
                            
                            # Pulizia file temporaneo
                            if os.path.exists(t_img): os.remove(t_img)
                    
                    pdf_output = pdf.output(dest='S').encode('latin-1')
                    st.download_button("💾 Scarica PDF Scatole", pdf_output, "etichette_scatole.pdf")

        # --- TAB UBICAZIONI (16 PER FOGLIO A4 - 4x4) ---
        with tab_u:
            f_u = filtro_st.lower()
            pos_da_mostrare = [p for p in pos_totale if f_u in str(p.get('id_ubicazione') or p.get('id','')).lower() or f_u in str(p.get('zona','')).lower()]
            
            if pos_da_mostrare:
                sel_p = []
                for i, p in enumerate(pos_da_mostrare):
                    id_disp = p.get('id_ubicazione') or p.get('id')
                    if st.checkbox(f"📍 {id_disp} ({p.get('zona')})", key=f"stp_print_{id_disp}_{i}"):
                        sel_p.append(p)
                
                if sel_p and st.button("📥 GENERA PDF UBICAZIONI", use_container_width=True):
                    pdf_u = FPDF()
                    cols, rows = 4, 4
                    w_area, h_area = 48, 68 # Spazio per cella
                    
                    for i in range(0, len(sel_p), 16):
                        pdf_u.add_page()
                        batch_p = sel_p[i:i+16]
                        for idx, p in enumerate(batch_p):
                            c = idx % cols
                            r = (idx // cols) % rows
                            x_off = 10 + (c * w_area)
                            y_off = 10 + (r * h_area)
                            
                            codice_u = str(p.get('id_ubicazione') or p.get('id'))
                            pdf_u.rect(x_off, y_off, 42, 60) 
                            
                            qr_u = QRCode(box_size=2); qr_u.add_data(codice_u); qr_u.make()
                            img_u = qr_u.make_image(); t_u = f"qr_u_{i}_{idx}.png"; img_u.save(t_u)
                            pdf_u.image(t_u, x_off + 6, y_off + 5, w=30)
                            
                            pdf_u.set_font("Arial", 'B', 12); pdf_u.set_xy(x_off, y_off + 38); pdf_u.cell(42, 10, codice_u, align='C')
                            pdf_u.set_font("Arial", '', 7); pdf_u.set_xy(x_off, y_off + 48); pdf_u.cell(42, 5, str(p.get('zona')).upper(), align='C')
                            
                            if os.path.exists(t_u): os.remove(t_u)
                            
                    pdf_u_out = pdf_u.output(dest='S').encode('latin-1')
                    st.download_button("💾 Scarica PDF Ubicazioni", pdf_u_out, "etichette_ubicazioni.pdf")