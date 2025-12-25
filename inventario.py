import qrcode, os, re, subprocess
from db_manager import esegui_query
from fpdf import FPDF

FOTO_FOLDER = 'immagini_scatole'
DOCS_FOLDER = 'documenti_stampa'

def inizializza_cartelle():
    for c in [FOTO_FOLDER, DOCS_FOLDER]:
        if not os.path.exists(c): os.makedirs(c)

def apri_cartella_stampe():
    path = os.path.abspath(DOCS_FOLDER)
    if os.path.exists(path): os.startfile(path)

def salva_foto_caricata(uploaded_file, nuovo_nome_base):
    if uploaded_file is not None:
        est = os.path.splitext(uploaded_file.name)[1]
        nome = f"{nuovo_nome_base}{est}"
        percorso = os.path.join(FOTO_FOLDER, nome)
        with open(percorso, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return nome
    return None

def genera_qr(testo, nome_file):
    qr = qrcode.make(testo)
    qr.save(os.path.join(DOCS_FOLDER, nome_file))

def calcola_prossimo_id(prefisso="SCAT_"):
    ris = esegui_query("SELECT ID_SCATOLA FROM SCATOLE WHERE ID_SCATOLA LIKE ? ORDER BY ID_SCATOLA DESC LIMIT 1", (f"{prefisso}%",))
    if not ris: return f"{prefisso}001"
    numeri = re.findall(r'\d+', ris[0][0])
    return f"{prefisso}{int(numeri[-1])+1:03d}" if numeri else f"{prefisso}001"

def crea_pdf_etichette(lista_id, tipo="SCATOLA"):
    pdf = FPDF(); pdf.set_margins(10, 10, 10)
    if tipo == "SCATOLA":
        for i in range(0, len(lista_id), 2):
            pdf.add_page()
            id1 = lista_id[i]
            genera_qr(id1, f"{id1}.png")
            info1 = esegui_query("SELECT CONTENUTO, PROPRIETARIO FROM SCATOLE WHERE ID_SCATOLA=?", (id1,))
            pdf.rect(5, 5, 200, 140)
            pdf.image(os.path.join(DOCS_FOLDER, f"{id1}.png"), x=15, y=20, w=60)
            pdf.set_font("Arial", 'B', 24); pdf.set_xy(80, 25); pdf.cell(100, 10, f"ID: {id1}")
            pdf.set_font("Arial", '', 18); pdf.set_xy(80, 45); pdf.multi_cell(100, 10, f"COSA: {info1[0][0] if info1 else 'N/A'}")
            pdf.set_font("Arial", 'B', 16); pdf.set_xy(80, 85); pdf.cell(100, 10, f"PROPR: {str(info1[0][1]).upper() if info1 else 'N/A'}")
            if i + 1 < len(lista_id):
                id2 = lista_id[i+1]
                genera_qr(id2, f"{id2}.png")
                info2 = esegui_query("SELECT CONTENUTO, PROPRIETARIO FROM SCATOLE WHERE ID_SCATOLA=?", (id2,))
                pdf.rect(5, 150, 200, 140)
                pdf.image(os.path.join(DOCS_FOLDER, f"{id2}.png"), x=15, y=165, w=60)
                pdf.set_font("Arial", 'B', 24); pdf.set_xy(80, 170); pdf.cell(100, 10, f"ID: {id2}")
                pdf.set_font("Arial", '', 18); pdf.set_xy(80, 190); pdf.multi_cell(100, 10, f"COSA: {info2[0][0] if info2 else 'N/A'}")
                pdf.set_font("Arial", 'B', 16); pdf.set_xy(80, 230); pdf.cell(100, 10, f"PROPR: {str(info2[0][1]).upper() if info2 else 'N/A'}")
    else:
        pdf.add_page()
        x, y, w, h = 10, 10, 45, 55
        col, row = 0, 0
        for id_cod in lista_id:
            if row > 4: pdf.add_page(); row, col = 0, 0
            cx, cy = x + (col*50), y + (row*60)
            pdf.set_draw_color(200, 200, 200); pdf.rect(cx, cy, w, h)
            genera_qr(id_cod, f"{id_cod}.png")
            pdf.image(os.path.join(DOCS_FOLDER, f"{id_cod}.png"), x=cx+5, y=cy+5, w=35)
            pdf.set_font("Arial", 'B', 10); pdf.set_xy(cx, cy+45); pdf.cell(w, 5, id_cod, align='C')
            col += 1
            if col > 1: col = 0; row += 1
    p = os.path.join(DOCS_FOLDER, f"stampa_{tipo.lower()}.pdf"); pdf.output(p); return p