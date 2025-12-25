import streamlit as st
import db_manager, inventario, os, pandas as pd
import io

st.set_page_config(page_title="Magazzino Casa PRO", layout="wide")
db_manager.crea_tabelle(); inventario.inizializza_cartelle()

lista_nomi = ["Victor", "Evelyn", "Daniel", "Carly", "Rebby"]
if 'pagina' not in st.session_state: st.session_state.pagina = "🏠 Home"
if 'focus' not in st.session_state: st.session_state.focus = None

menu = ["🏠 Home", "🔍 Cerca Oggetto", "➕ Crea Nuova Scatola", "📦 Dettaglio Contenuto", "🔄 Sposta Scatola", "⚙️ Configura Magazzino", "🖨️ Stampa Etichette"]
st.sidebar.title("Menù")
st.session_state.pagina = st.sidebar.radio("Navigazione:", menu, index=menu.index(st.session_state.pagina))

# --- 1. HOME ---
if st.session_state.pagina == "🏠 Home":
    st.title("📊 Dashboard")
    scat_tot = db_manager.esegui_query("SELECT ID_SCATOLA FROM SCATOLE")
    post_tot = db_manager.esegui_query("SELECT ID_POSIZIONE, DESCRIZIONE FROM POSIZIONI")
    c1, c2, c3 = st.columns(3)
    c1.metric("Scatole", len(scat_tot)); c2.metric("Scaffali", len(post_tot)); c3.metric("Utenti", len(lista_nomi))
    st.divider(); st.subheader("📍 Mappa Scaffali")
    if post_tot:
        cols = st.columns(5)
        for index, p in enumerate(post_tot):
            n = db_manager.esegui_query("SELECT COUNT(*) FROM SCATOLE WHERE POSIZIONE_ATTUALE=?", (p[0],))[0][0]
            with cols[index % 5]: st.info(f"{'🔵' if n==0 else '🟠'} **{p[0]}**\n\n_{p[1]}_\n\n📦 Scatole: {n}")

# --- 2. CERCA ---
elif st.session_state.pagina == "🔍 Cerca Oggetto":
    st.header("🔎 Ricerca")
    chiave = st.text_input("Cerca parola chiave:")
    if chiave:
        res = db_manager.esegui_query("""
            SELECT S.ID_SCATOLA, S.CONTENUTO, S.PROPRIETARIO, S.FOTO_COPERTINA, P.DESCRIZIONE, S.POSIZIONE_ATTUALE 
            FROM SCATOLE S 
            LEFT JOIN POSIZIONI P ON S.POSIZIONE_ATTUALE = P.ID_POSIZIONE
            WHERE LOWER(S.CONTENUTO) LIKE ? 
            OR S.ID_SCATOLA IN (SELECT ID_SCATOLA FROM CONTENUTO_DETTAGLIO WHERE LOWER(DESCRIZIONE_OGGETTO) LIKE ?)
        """, (f"%{chiave.lower()}%", f"%{chiave.lower()}%"))
        for r in res:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"### {r[1]} ({r[0]})")
                st.write(f"👤 Proprietario: **{r[2]}**")
                loc = f"{r[4]} / {r[5]}" if r[5] else "⚠️ NON UBICATA"
                st.warning(f"📍 Posizione: **{loc}**")
                if st.button(f"Vedi {r[0]}", key=f"v_{r[0]}"): st.session_state.focus = r[0]; st.session_state.pagina = "📦 Dettaglio Contenuto"; st.rerun()
            if r[3]: col2.image(os.path.join(inventario.FOTO_FOLDER, r[3]), width=150)
            st.divider()

# --- 3. CREA ---
elif st.session_state.pagina == "➕ Crea Nuova Scatola":
    st.header("➕ Nuova Scatola")
    prossimo = inventario.calcola_prossimo_id()
    c1, c2 = st.columns(2)
    id_s = c1.text_input("ID Scatola", prossimo).upper()
    desc = c1.text_input("Titolo Scatola")
    prop = c2.selectbox("Proprietario", lista_nomi)
    foto = c2.file_uploader("Foto Copertina", type=['jpg','png','jpeg'])
    if st.button("🚀 Salva"):
        fn = inventario.salva_foto_caricata(foto, id_s) if foto else ""
        db_manager.esegui_query("INSERT INTO SCATOLE (ID_SCATOLA, CONTENUTO, PROPRIETARIO, FOTO_COPERTINA) VALUES (?,?,?,?)", (id_s, desc, prop, fn))
        inventario.genera_qr(id_s, f"{id_s}.png")
        st.session_state.focus = id_s; st.session_state.pagina = "📦 Dettaglio Contenuto"; st.rerun()

# --- 4. DETTAGLIO ---
elif st.session_state.pagina == "📦 Dettaglio Contenuto":
    st.header("📦 Dettaglio Contenuto")
    scats = [r[0] for r in db_manager.esegui_query("SELECT ID_SCATOLA FROM SCATOLE")]
    if scats:
        idx = scats.index(st.session_state.focus) if st.session_state.focus in scats else 0
        id_sel = st.selectbox("Seleziona Scatola:", scats, index=idx)
        info = db_manager.esegui_query("SELECT CONTENUTO, PROPRIETARIO, FOTO_COPERTINA FROM SCATOLE WHERE ID_SCATOLA=?", (id_sel,))[0]
        c_a, c_b = st.columns([3,1])
        with c_a:
            st.subheader(f"{info[0]}")
            if st.button("⚠️ ELIMINA SCATOLA", type="primary"):
                db_manager.esegui_query("DELETE FROM SCATOLE WHERE ID_SCATOLA=?", (id_sel,))
                db_manager.esegui_query("DELETE FROM CONTENUTO_DETTAGLIO WHERE ID_SCATOLA=?", (id_sel,))
                st.session_state.focus = None; st.rerun()
        if info[2]: c_b.image(os.path.join(inventario.FOTO_FOLDER, info[2]), width=200)
        st.divider(); st.subheader("🔍 Oggetti Interni")
        with st.expander("➕ Aggiungi Oggetto"):
            n, s, f = st.columns(3)
            o_n, o_s, o_f = n.text_input("Nome"), s.text_input("Livello"), f.file_uploader("Foto", type=['jpg','png','jpeg'], key="oi")
            if st.button("Aggiungi"):
                fn_o = inventario.salva_foto_caricata(o_f, f"{id_sel}_{o_n}") if o_f else ""
                db_manager.esegui_query("INSERT INTO CONTENUTO_DETTAGLIO (ID_SCATOLA, DESCRIZIONE_OGGETTO, STRATO, FOTO_PATH) VALUES (?,?,?,?)", (id_sel, o_n, o_s, fn_o)); st.rerun()
        objs = db_manager.esegui_query("SELECT ID_DETTAGLIO, DESCRIZIONE_OGGETTO, STRATO, FOTO_PATH FROM CONTENUTO_DETTAGLIO WHERE ID_SCATOLA=?", (id_sel,))
        for o in objs:
            ca, cb, cc, cd = st.columns([2, 1, 1, 0.5])
            ca.write(o[1]); cb.write(o[2])
            if o[3]: cc.image(os.path.join(inventario.FOTO_FOLDER, o[3]), width=80)
            if cd.button("🗑️", key=f"d_{o[0]}"): db_manager.esegui_query("DELETE FROM CONTENUTO_DETTAGLIO WHERE ID_DETTAGLIO=?", (o[0],)); st.rerun()

# --- 5. CONFIGURA MAGAZZINO (CON EXCEL) ---
elif st.session_state.pagina == "⚙️ Configura Magazzino":
    st.header("⚙️ Gestione Ubicazioni")
    
    # 1. Recupero dati per Excel
    query_excel = """
        SELECT P.ID_POSIZIONE AS 'CODICE', P.DESCRIZIONE AS 'ZONA', COUNT(S.ID_SCATOLA) AS 'SCATOLE PRESENTI'
        FROM POSIZIONI P
        LEFT JOIN SCATOLE S ON P.ID_POSIZIONE = S.POSIZIONE_ATTUALE
        GROUP BY P.ID_POSIZIONE
    """
    dati = db_manager.esegui_query(query_excel)
    df = pd.DataFrame(dati, columns=["CODICE", "ZONA", "SCATOLE PRESENTI"])

    # 2. Pulsante Download Excel
    st.subheader("📊 Esporta in Excel")
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Magazzino')
        # Centratura automatica delle colonne (opzionale)
        workbook = writer.book
        worksheet = writer.sheets['Magazzino']
        format_centrato = workbook.add_format({'align': 'center', 'valign': 'vcenter'})
        worksheet.set_column('A:C', 20, format_centrato)
    
    st.download_button(
        label="📥 Scarica Lista Scaffali (Excel)",
        data=buffer,
        file_name="inventario_scaffali.xlsx",
        mime="application/vnd.ms-excel"
    )

    st.divider()
    
    # 3. Gestione Scaffali (Lista e Eliminazione)
    st.subheader("📍 Lista Attuale")
    pos = db_manager.esegui_query("SELECT DESCRIZIONE, ID_POSIZIONE FROM POSIZIONI")
    for p in pos:
        c1, c2, c3 = st.columns([3, 2, 1])
        c1.write(f"**{p[1]}** ({p[0]})")
        if c3.button("🗑️", key=f"del_p_{p[1]}"): 
            db_manager.esegui_query("DELETE FROM POSIZIONI WHERE ID_POSIZIONE=?", (p[1],)); st.rerun()

    st.divider()
    # 4. Aggiunta nuovo scaffale
    st.subheader("➕ Aggiungi Nuovo Scaffale")
    c1, c2 = st.columns(2)
    z, i = c1.text_input("Nome Zona (es. Garage)"), c2.text_input("Codice QR Scaffale").upper()
    if st.button("Salva Scaffale"):
        db_manager.esegui_query("INSERT OR IGNORE INTO POSIZIONI VALUES (?,?)", (i, z))
        inventario.genera_qr(i, f"{i}.png"); st.rerun()

# --- 6. SPOSTA ---
elif st.session_state.pagina == "🔄 Sposta Scatola":
    st.header("🔄 Sposta Scatola")
    s_id = st.text_input("ID Scatola (Spara QR)").upper()
    p_id = st.text_input("ID Scaffale (Spara QR)").upper()
    if p_id:
        check_posto = db_manager.esegui_query("SELECT DESCRIZIONE FROM POSIZIONI WHERE ID_POSIZIONE=?", (p_id,))
        if check_posto:
            gia_presenti = db_manager.esegui_query("SELECT ID_SCATOLA, CONTENUTO FROM SCATOLE WHERE POSIZIONE_ATTUALE=?", (p_id,))
            if gia_presenti:
                st.warning(f"⚠️ In questa posizione ci sono già: {', '.join([g[0] for g in gia_presenti])}")
            else: st.success(f"✅ Posto {p_id} libero.")
        else: st.error("❌ Ubicazione inesistente!")
    if st.button("Conferma Spostamento"):
        if s_id and p_id:
            db_manager.esegui_query("UPDATE SCATOLE SET POSIZIONE_ATTUALE=? WHERE ID_SCATOLA=?", (p_id, s_id))
            st.success("Spostato!"); st.rerun()

# --- 7. STAMPA ---
elif st.session_state.pagina == "🖨️ Stampa Etichette":
    st.header("🖨️ Stampa")
    if st.button("📂 Apri Cartella Stampe"): inventario.apri_cartella_stampe()
    t1, t2 = st.tabs(["Scatole", "Scaffali"])
    with t1:
        sl = [r[0] for r in db_manager.esegui_query("SELECT ID_SCATOLA FROM SCATOLE")]
        sels = [s for s in sl if st.checkbox(s, key=f"st_{s}")]
        if st.button("PDF Scatole") and sels:
            p = inventario.crea_pdf_etichette(sels, "SCATOLA"); st.success(f"Creato: {p}")
    with t2:
        pl = [r[0] for r in db_manager.esegui_query("SELECT ID_POSIZIONE FROM POSIZIONI")]
        selp = [p for p in pl if st.checkbox(p, key=f"pp_{p}")]
        if st.button("PDF Scaffali") and selp:
            p = inventario.crea_pdf_etichette(selp, "UBICAZIONE"); st.success(f"Creato: {p}")