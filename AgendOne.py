import datetime
import io
import json
import os
import re
import pandas as pd
import streamlit as st

# Impostazione pagina
st.set_page_config(page_title="AgendOne", layout="wide")

# CSS PERSONALIZZATO PER IL MENU IN ALTO E LA VISTA CALENDARIO
st.markdown(
    """
    <style>
    /* Ingrandimento e messa in evidenza dei Tab del Menu Principale a forma di Pulsante */
    button[data-baseweb="tab"] {
        font-size: 18px !important;
        font-weight: bold !important;
        background-color: #1e293b !important;
        color: #f8fafc !important;
        padding: 12px 24px !important;
        border-radius: 8px !important; /* Arrotondati su tutti i lati per sembrare bottoni */
        margin-right: 10px !important;
        border: 1px solid #334155 !important;
        transition: all 0.2s ease-in-out !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
    }

    button[data-baseweb="tab"]:hover {
        background-color: #334155 !important;
        color: #ffffff !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2) !important;
        transform: translateY(-2px) !important;
    }

    /* Stato del Tab Selezionato */
    button[data-baseweb="tab"][aria-selected="true"] {
        background-color: #2563eb !important;
        color: #ffffff !important;
        border: 1px solid #2563eb !important;
        box-shadow: 0 4px 10px rgba(37, 99, 235, 0.4) !important;
    }
    
    /* Nasconde la linea di base di Streamlit e l'animazione della riga sotto i tab */
    div[data-baseweb="tab-highlight"] {
        display: none !important;
    }
    div[data-baseweb="tab-border"] {
        display: none !important;
    }
    div[data-baseweb="tab-list"] {
        gap: 10px;
    }

    /* Sfondo delle caselle del calendario (celeste chiaro) */
    .fc-daygrid-day, .fc-timegrid-slot, .fc-theme-standard td {
        background-color: #e6f2ff !important;
    }

    /* Giorno corrente */
    .fc-day-today {
        background-color: #cce5ff !important;
    }

    /* Eventi / Appuntamenti doppi (Blu) */
    .fc-event.doppio-appuntamento, 
    .fc-event[data-type="doppio"], 
    .event-double {
        background-color: #0044cc !important;
        border-color: #002b80 !important;
        color: #ffffff !important;
    }

    /* Banner XL al passaggio del mouse */
    .fc-popover, .fc-tooltip, [data-baseweb="tooltip"], div[role="tooltip"] {
        font-size: 2.2rem !important;
        padding: 26px 36px !important;
        min-width: 450px !important;
        max-width: 750px !important;
        border-radius: 16px !important;
        box-shadow: 0px 10px 30px rgba(0, 0, 0, 0.5) !important;
    }

    .fc-popover-header, .tooltip-title {
        font-size: 2.6rem !important;
        font-weight: 900 !important;
        margin-bottom: 14px !important;
    }

    .fc-popover-body, .tooltip-inner {
        font-size: 2.0rem !important;
        line-height: 1.6 !important;
    }

    /* Pulsanti Frecce Moderni Carousel */
    .nav-btn {
      position: absolute;
      top: 50%;
      transform: translateY(-50%);
      width: 52px;
      height: 52px;
      border-radius: 50%;
      background: rgba(255, 255, 255, 0.9);
      backdrop-filter: blur(8px);
      border: 1px solid rgba(255, 255, 255, 0.3);
      color: #1e293b;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      z-index: 10;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
      transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    }

    .nav-btn:hover {
      background: #ffffff;
      transform: translateY(-50%) scale(1.1);
      box-shadow: 0 6px 20px rgba(0, 0, 0, 0.2);
      color: #2563eb;
    }

    .nav-btn-prev { left: 16px; }
    .nav-btn-next { right: 16px; }

    .nav-btn svg {
      width: 24px;
      height: 24px;
      fill: none;
      stroke: currentColor;
      stroke-width: 2.5;
      stroke-linecap: round;
      stroke-linejoin: round;
    }

    /* Banner Popup Ingrandito */
    .preview-banner {
      position: absolute;
      bottom: 24px;
      left: 50%;
      transform: translateX(-50%) translateY(20px);
      width: 85%;
      max-width: 600px;
      background: rgba(255, 255, 255, 0.95);
      backdrop-filter: blur(12px);
      padding: 20px 24px;
      border-radius: 14px;
      box-shadow: 0 20px 30px -10px rgba(0, 0, 0, 0.25);
      border: 1px solid rgba(255, 255, 255, 0.8);
      opacity: 0;
      visibility: hidden;
      transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
      z-index: 20;
    }

    .carousel-container:hover .preview-banner {
      opacity: 1;
      visibility: visible;
      transform: translateX(-50%) translateY(0);
    }

    .preview-title {
      font-size: 1.25rem;
      font-weight: 700;
      color: #1e293b;
      margin: 0 0 8px 0;
    }

    .preview-description {
      font-size: 1.0rem;
      color: #64748b;
      margin: 0;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Dizionario per i mesi in italiano
MESI_ITALIANI = {
    "January": "Gennaio",
    "February": "Febbraio",
    "March": "Marzo",
    "April": "Aprile",
    "May": "Maggio",
    "June": "Giugno",
    "July": "Luglio",
    "August": "Agosto",
    "September": "Settembre",
    "October": "Ottobre",
    "November": "Novembre",
    "December": "Dicembre",
}

def traduci_mese(mese_en):
    return MESI_ITALIANI.get(mese_en, mese_en)

# Funzione per validare e scomporre la stringa oraria nel formato obbligatorio 00:00-00:00
def valida_e_seleziona_orario(stringa_orario):
    """
    Verifica che la stringa rispetti il formato HH:MM-HH:MM con ore (0-23) e minuti (0-59).
    Restituisce (ora_inizio, ora_fine) se valido, altrimenti (None, None).
    """
    if not stringa_orario:
        return None, None
    
    pattern = r"^([0-1]?[0-9]|2[0-3]):([0-5][0-9])-([0-1]?[0-9]|2[0-3]):([0-5][0-9])$"
    match = re.match(pattern, stringa_orario.strip())
    
    if not match:
        return None, None
    
    h_i, m_i, h_f, m_f = match.groups()
    ora_inizio = f"{int(h_i):02d}:{int(m_i):02d}"
    ora_fine = f"{int(h_f):02d}:{int(m_f):02d}"
    return ora_inizio, ora_fine

# Parser per date in formato italiano DD/MM/YYYY o ISO YYYY-MM-DD
def parse_data_italiana(val):
    if pd.isna(val) or str(val).strip() == "" or str(val).lower() == "none" or str(val).lower() == "nan":
        return pd.NaT
    val_str = str(val).strip()
    
    if "-" in val_str and len(val_str.split("-")[0]) == 4:
        try:
            return pd.to_datetime(val_str, format="%Y-%m-%d")
        except:
            pass
            
    try:
        parti = val_str.split("/")
        if len(parti) == 3:
            giorno, mese, anno = int(parti[0]), int(parti[1]), int(parti[2])
            return datetime.datetime(anno, mese, giorno)
    except:
        pass
        
    return pd.to_datetime(val_str, errors="coerce", dayfirst=True)

# Calcolo automatico delle ore tra inizio e fine
def calcola_ore(ora_inizio, ora_fine):
    try:
        t_i = datetime.datetime.strptime(str(ora_inizio).strip(), "%H:%M")
    except:
        try:
            t_i = datetime.datetime.strptime(str(ora_inizio).strip(), "%H:%M:%S")
        except:
            return 0.0
    try:
        t_f = datetime.datetime.strptime(str(ora_fine).strip(), "%H:%M")
    except:
        try:
            t_f = datetime.datetime.strptime(str(ora_fine).strip(), "%H:%M:%S")
        except:
            return 0.0
    diff = (datetime.datetime.combine(datetime.date.min, t_f.time()) - 
            datetime.datetime.combine(datetime.date.min, t_i.time())).total_seconds() / 3600.0
    return max(0.0, round(diff, 2))

# Funzione per generare il Report PDF raggruppato per Ente e Classe
def genera_pdf_report(df_report):
    try:
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from collections import defaultdict
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=landscape(A4), 
            rightMargin=20, 
            leftMargin=20, 
            topMargin=20, 
            bottomMargin=20
        )
        elements = []
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=15, textColor=colors.HexColor('#1c3d73'), spaceAfter=6)
        subtitle_style = ParagraphStyle('SubTitleStyle', parent=styles['Heading2'], fontSize=11, textColor=colors.HexColor('#1c3d73'), spaceAfter=4)
        ente_header_style = ParagraphStyle('EnteHeaderStyle', parent=styles['Heading3'], fontSize=10, textColor=colors.HexColor('#0f172a'), spaceAfter=3, fontName='Helvetica-Bold')
        
        th_style = ParagraphStyle('TH', parent=styles['Normal'], fontSize=9, fontName='Helvetica-Bold', textColor=colors.white)
        td_style = ParagraphStyle('TD', parent=styles['Normal'], fontSize=8, fontName='Helvetica', textColor=colors.HexColor('#333333'))
        td_excl_style = ParagraphStyle('TDExcl', parent=styles['Normal'], fontSize=8, fontName='Helvetica-Oblique', textColor=colors.HexColor('#b91c1c'))
        td_summary_style = ParagraphStyle('TDSummary', parent=styles['Normal'], fontSize=9, fontName='Helvetica', textColor=colors.HexColor('#333333'))
        
        style_subtot_classe = ParagraphStyle('SubTotClasse', parent=styles['Normal'], alignment=2, fontSize=8, fontName='Helvetica-Bold', textColor=colors.HexColor('#2563eb'))
        style_subtot_val_classe = ParagraphStyle('SubTotValClasse', parent=styles['Normal'], fontSize=8, fontName='Helvetica-Bold', textColor=colors.HexColor('#2563eb'))

        elements.append(Paragraph("Report Attività e Riepilogo Ore - AgendOne", title_style))
        elements.append(Spacer(1, 6))
        
        df_validi = df_report[df_report["Escludi_Conteggio"] != True] if "Escludi_Conteggio" in df_report.columns else df_report
        
        elements.append(Paragraph("Riepilogo Totale Parziali per Ente di Appartenenza", subtitle_style))
        if not df_validi.empty and "Ente" in df_validi.columns and "Ore" in df_validi.columns:
            df_summary_ente = df_validi.groupby("Ente")["Ore"].sum().reset_index()
            summary_ente_data = [[Paragraph("Ente di Appartenenza", th_style), Paragraph("Ore Totali Parziali", th_style)]]
            
            for _, row in df_summary_ente.iterrows():
                summary_ente_data.append([
                    Paragraph(str(row["Ente"]) if row["Ente"] else "Non Specificato", td_summary_style),
                    Paragraph(f"{row['Ore']:.2f} h", td_summary_style)
                ])
            
            t_summary_ente = Table(summary_ente_data, colWidths=[600, 180])
            t_summary_ente.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1c3d73')),
                ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('BOTTOMPADDING', (0,0), (-1,-1), 4),
                ('TOPPADDING', (0,0), (-1,-1), 4),
                ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#f8fafc')),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
            ]))
            elements.append(t_summary_ente)
            elements.append(Spacer(1, 10))

        elements.append(Paragraph("Elenco Dettagliato Attività Raggruppate per Ente e Classe", subtitle_style))
        elements.append(Spacer(1, 4))
        
        if not df_report.empty:
            gruppi_ente_classe = defaultdict(lambda: defaultdict(list))
            for _, row in df_report.iterrows():
                e_nome = str(row.get("Ente", "")).strip()
                if not e_nome or e_nome.lower() == "nan":
                    e_nome = "Non Specificato"
                
                c_nome = str(row.get("Classe", "")).strip()
                if not c_nome or c_nome.lower() == "nan":
                    c_nome = "Non Specificata"
                    
                gruppi_ente_classe[e_nome][c_nome].append(row)
                
            col_widths = [60, 75, 120, 100, 75, 220, 52]

            for ente_nome, classi_dict in gruppi_ente_classe.items():
                elements.append(Paragraph(f"Ente: <b>{ente_nome}</b>", ente_header_style))
                
                det_data = [[
                    Paragraph("Data", th_style),
                    Paragraph("Orario", th_style),
                    Paragraph("Classe / Committente", th_style),
                    Paragraph("Sede", th_style),
                    Paragraph("Modalità", th_style),
                    Paragraph("Note / Dettagli", th_style),
                    Paragraph("Ore", th_style)
                ]]
                
                table_styles = [
                    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#334155')),
                    ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                    ('VALIGN', (0,0), (-1,-1), 'TOP'),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 4),
                    ('TOPPADDING', (0,0), (-1,-1), 4),
                    ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f1f5f9')),
                ]
                
                totale_ore_ente = 0.0
                row_idx = 1
                
                for classe_nome, lista_attivita in classi_dict.items():
                    totale_ore_classe = 0.0
                    
                    for row in lista_attivita:
                        parsed_dt = parse_data_italiana(row.get("Data", ""))
                        data_str = parsed_dt.strftime("%d/%m/%Y") if pd.notnull(parsed_dt) else str(row.get("Data", ""))
                        is_esclusa = bool(row.get("Escludi_Conteggio", False))
                        ore_val = float(row.get("Ore", 0.0))
                        
                        if not is_esclusa:
                            totale_ore_classe += ore_val
                            totale_ore_ente += ore_val
                            ore_str = f"{ore_val:.2f}h"
                            cur_td_style = td_style
                            note_str = str(row.get("Note", ""))
                        else:
                            ore_str = "0.00h"
                            cur_td_style = td_excl_style
                            note_str = f"[ESCLUSA DAL CONTEGGIO] {str(row.get('Note', ''))}"

                        det_data.append([
                            Paragraph(data_str, cur_td_style),
                            Paragraph(f"{row.get('Orario Inizio', '')} - {row.get('Orario Fine', '')}", cur_td_style),
                            Paragraph(str(row.get("Classe", "")), cur_td_style),
                            Paragraph(str(row.get("Sede", "")), cur_td_style),
                            Paragraph(str(row.get("Modalità", "")), cur_td_style),
                            Paragraph(note_str, cur_td_style),
                            Paragraph(ore_str, cur_td_style)
                        ])
                        row_idx += 1
                    
                    det_data.append([
                        Paragraph(f"<b>Totale parziale ({classe_nome}):</b>", style_subtot_classe),
                        "", "", "", "", "",
                        Paragraph(f"<b>{totale_ore_classe:.2f}h</b>", style_subtot_val_classe)
                    ])
                    table_styles.append(('SPAN', (0, row_idx), (5, row_idx)))
                    table_styles.append(('BACKGROUND', (0, row_idx), (-1, row_idx), colors.HexColor('#e6f2ff')))
                    row_idx += 1

                det_data.append([
                    Paragraph(f"<b>Totale Ore Parziali ({ente_nome}):</b>", ParagraphStyle('SubTot', parent=styles['Normal'], alignment=2, fontSize=8, fontName='Helvetica-Bold', textColor=colors.HexColor('#1c3d73'))),
                    "", "", "", "", "",
                    Paragraph(f"<b>{totale_ore_ente:.2f}h</b>", ParagraphStyle('SubTotVal', parent=styles['Normal'], fontSize=8, fontName='Helvetica-Bold', textColor=colors.HexColor('#1c3d73')))
                ])
                table_styles.append(('SPAN', (0, row_idx), (5, row_idx)))
                table_styles.append(('BACKGROUND', (0, row_idx), (-1, row_idx), colors.HexColor('#e2e8f0')))
                row_idx += 1

                t_det = Table(det_data, colWidths=col_widths)
                t_det.setStyle(TableStyle(table_styles))
                elements.append(t_det)
                elements.append(Spacer(1, 8))
            
            totale_generale = df_validi["Ore"].sum() if not df_validi.empty else 0.0
            t_tot = Table([[Paragraph(f"<b>TOTALE GENERALE ORE VALIDE: {totale_generale:.2f} h</b>", ParagraphStyle('TotStyle', parent=styles['Normal'], alignment=2, textColor=colors.HexColor('#1c3d73'), fontSize=10))]], colWidths=[802])
            t_tot.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#e2e8f0')),
                ('ALIGN', (0,0), (-1,-1), 'RIGHT'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('BOTTOMPADDING', (0,0), (-1,-1), 6),
                ('TOPPADDING', (0,0), (-1,-1), 6),
            ]))
            elements.append(t_tot)
        
        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()
    except Exception as e:
        return None

# Funzione per ottenere il client gspread e il foglio desiderato
def get_gspread_client_and_sheet(nome_foglio="Foglio1"):
    try:
        import gspread
        gsheets_secrets = st.secrets["connections"]["gsheets"]
        spreadsheet_url = gsheets_secrets["spreadsheet"]
        
        creds_dict = {
            "type": gsheets_secrets.get("type", "service_account"),
            "project_id": gsheets_secrets.get("project_id"),
            "private_key_id": gsheets_secrets.get("private_key_id"),
            "private_key": gsheets_secrets.get("private_key", "").replace("\\n", "\n"),
            "client_email": gsheets_secrets.get("client_email"),
            "client_id": gsheets_secrets.get("client_id"),
            "auth_uri": gsheets_secrets.get("auth_uri", "https://accounts.google.com/o/oauth2/auth"),
            "token_uri": gsheets_secrets.get("token_uri", "https://oauth2.googleapis.com/token"),
            "auth_provider_x509_cert_url": gsheets_secrets.get("auth_provider_x509_cert_url", "https://www.googleapis.com/oauth2/v1/certs"),
            "client_x509_cert_url": gsheets_secrets.get("client_x509_cert_url"),
            "universe_domain": gsheets_secrets.get("universe_domain", "googleapis.com"),
        }
        
        client = gspread.service_account_from_dict(creds_dict)
        spreadsheet = client.open_by_url(spreadsheet_url)
        worksheet = spreadsheet.worksheet(nome_foglio)
        return worksheet
    except Exception as e:
        st.error(f"Errore durante la connessione a Google Sheets ('{nome_foglio}'): {e}")
        return None

# Funzione per sincronizzare l'evento su Google Calendar
def sincronizza_google_calendar(azione, dati_evento, evento_id_esistente=None):
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        from googleapiclient.errors import HttpError

        gsheets_secrets = st.secrets["connections"]["gsheets"]
        creds_dict = {
            "type": gsheets_secrets.get("type", "service_account"),
            "project_id": gsheets_secrets.get("project_id"),
            "private_key_id": gsheets_secrets.get("private_key_id"),
            "private_key": gsheets_secrets.get("private_key", "").replace("\\n", "\n"),
            "client_email": gsheets_secrets.get("client_email"),
            "client_id": gsheets_secrets.get("client_id"),
            "auth_uri": gsheets_secrets.get("auth_uri", "https://accounts.google.com/o/oauth2/auth"),
            "token_uri": gsheets_secrets.get("token_uri", "https://oauth2.googleapis.com/token"),
            "auth_provider_x509_cert_url": gsheets_secrets.get("auth_provider_x509_cert_url", "https://www.googleapis.com/oauth2/v1/certs"),
            "client_x509_cert_url": gsheets_secrets.get("client_x509_cert_url"),
            "universe_domain": gsheets_secrets.get("universe_domain", "googleapis.com"),
        }

        SCOPES = ['https://www.googleapis.com/auth/calendar']
        credentials = service_account.Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        service = build('calendar', 'v3', credentials=credentials)

        calendar_id = gsheets_secrets.get("calendar_id", "primary")

        if evento_id_esistente:
            evento_id_esistente = str(evento_id_esistente).strip()
            if evento_id_esistente.lower() in ["nan", "none", ""]:
                evento_id_esistente = None

        if azione != "elimina":
            data_str = dati_evento["Data"]
            start_datetime = f"{data_str}T{dati_evento['Orario Inizio']}:00"
            end_datetime = f"{data_str}T{dati_evento['Orario Fine']}:00"

            body = {
                'summary': f"Lezione/Impegno: [{dati_evento.get('Ente', '')}] {dati_evento['Classe']} ({dati_evento['Modalità']})",
                'location': str(dati_evento['Sede']),
                'description': f"Ente: {dati_evento.get('Ente', '')}\nNote: {dati_evento.get('Note', '')}\nAppunto/Multi-impegno: {dati_evento.get('Appunto_Multiplo', '')}\nGestito da AgendOne",
                'start': {
                    'dateTime': start_datetime,
                    'timeZone': 'Europe/Rome',
                },
                'end': {
                    'dateTime': end_datetime,
                    'timeZone': 'Europe/Rome',
                },
                'reminders': {
                    'useDefault': True,
                },
            }

        if azione == "crea":
            event_result = service.events().insert(calendarId=calendar_id, body=body).execute()
            return event_result.get('id')
        elif azione == "aggiorna" and evento_id_esistente:
            try:
                service.events().update(calendarId=calendar_id, eventId=evento_id_esistente, body=body).execute()
                return evento_id_esistente
            except HttpError as err:
                if err.resp.status == 404:
                    event_result = service.events().insert(calendarId=calendar_id, body=body).execute()
                    return event_result.get('id')
                else:
                    raise err
        elif azione == "aggiorna" and not evento_id_esistente:
            event_result = service.events().insert(calendarId=calendar_id, body=body).execute()
            return event_result.get('id')
        elif azione == "elimina" and evento_id_esistente:
            try:
                service.events().delete(calendarId=calendar_id, eventId=evento_id_esistente).execute()
            except HttpError as err:
                if err.resp.status != 404:
                    raise err
            return None
    except Exception as e:
        st.error(f"Errore di sincronizzazione Google Calendar: {e}")
        return None

# Gestione configurazione tabelle (caricamento e salvataggio dal foglio "Tabelle")
def carica_config():
    default_config = {
        "enti": [],
        "classi": [],
        "sedi": [],
        "modalita": [],
    }
    try:
        worksheet = get_gspread_client_and_sheet("Tabelle")
        if worksheet is None:
            return default_config
        
        all_values = worksheet.get_all_values()
        if not all_values or len(all_values) < 2:
            return default_config
        
        headers = [h.strip() for h in all_values[0]]
        
        idx_enti = headers.index("T_Enti") if "T_Enti" in headers else -1
        idx_classi = headers.index("T_Classi") if "T_Classi" in headers else -1
        idx_sedi = headers.index("T_Sedi") if "T_Sedi" in headers else -1
        idx_modalita = headers.index("T_Modalita") if "T_Modalita" in headers else -1

        enti, classi, sedi, modalita = [], [], [], []
        for row in all_values[1:]:
            if idx_enti != -1 and len(row) > idx_enti and row[idx_enti].strip():
                enti.append(row[idx_enti].strip())
            if idx_classi != -1 and len(row) > idx_classi and row[idx_classi].strip():
                classi.append(row[idx_classi].strip())
            if idx_sedi != -1 and len(row) > idx_sedi and row[idx_sedi].strip():
                sedi.append(row[idx_sedi].strip())
            if idx_modalita != -1 and len(row) > idx_modalita and row[idx_modalita].strip():
                modalita.append(row[idx_modalita].strip())

        return {
            "enti": enti,
            "classi": classi,
            "sedi": sedi,
            "modalita": modalita
        }
    except Exception as e:
        st.error(f"Errore durante il caricamento dal foglio 'Tabelle': {e}")
        return default_config

def salva_config(config):
    try:
        worksheet = get_gspread_client_and_sheet("Tabelle")
        if worksheet is None:
            st.error("Impossibile connettersi al foglio 'Tabelle' per salvare.")
            return
        
        enti = config.get("enti", [])
        classi = config.get("classi", [])
        sedi = config.get("sedi", [])
        modalita = config.get("modalita", [])
        
        max_len = max(len(enti), len(classi), len(sedi), len(modalita), 0)
        
        headers = ["T_Enti", "T_Classi", "T_Sedi", "T_Modalita"]
        rows = [headers]
        
        for i in range(max_len):
            e = enti[i] if i < len(enti) else ""
            c = classi[i] if i < len(classi) else ""
            s = sedi[i] if i < len(sedi) else ""
            m = modalita[i] if i < len(modalita) else ""
            rows.append([e, c, s, m])
        
        worksheet.clear()
        worksheet.update("A1", rows)
    except Exception as e:
        st.error(f"Errore durante il salvataggio nel foglio 'Tabelle': {e}")

config = carica_config()

# Caricamento dati da Google Sheets (da Foglio1)
def carica_dati():
    cols_standard = ["Data", "Mese", "Orario Inizio", "Orario Fine", "Ore", "Ente", "Classe", "Sede", "Modalità", "Svolto", "Escludi_Conteggio", "Note", "Appunto_Multiplo", "Codice_Univoco", "Calendar_ID", "Reminder_Minuti"]
    empty_df = pd.DataFrame(columns=cols_standard)
    try:
        worksheet = get_gspread_client_and_sheet("Foglio1")
        if worksheet is None:
            return empty_df
        
        data = worksheet.get_all_records()
        if not data:
            return empty_df
        df = pd.DataFrame(data)
        
        if "Committente" in df.columns and "Classe" not in df.columns:
            df = df.rename(columns={"Committente": "Classe"})
        if "Luogo" in df.columns and "Sede" not in df.columns:
            df = df.rename(columns={"Luogo": "Sede"})
            
        if "Data" in df.columns:
            df["Data_dt"] = df["Data"].apply(parse_data_italiana)
            
            mask_valid = df["Data_dt"].notna()
            df.loc[mask_valid, "Data"] = df.loc[mask_valid, "Data_dt"].dt.strftime("%Y-%m-%d")
            df.loc[mask_valid, "Mese"] = df.loc[mask_valid, "Data_dt"].apply(
                lambda dt: traduci_mese(dt.strftime("%B")).capitalize()
            )
            
        if "Svolto" not in df.columns:
            df["Svolto"] = False
        else:
            df["Svolto"] = df["Svolto"].apply(lambda x: True if str(x).lower() in ["true", "1", "yes", "vero", "on"] else False)

        if "Escludi_Conteggio" not in df.columns:
            df["Escludi_Conteggio"] = False
        else:
            df["Escludi_Conteggio"] = df["Escludi_Conteggio"].apply(lambda x: True if str(x).lower() in ["true", "1", "yes", "vero", "on"] else False)

        if "Calendar_ID" not in df.columns:
            df["Calendar_ID"] = ""
        else:
            df["Calendar_ID"] = df["Calendar_ID"].fillna("").astype(str)

        if "Reminder_Minuti" not in df.columns:
            df["Reminder_Minuti"] = 240
        else:
            df["Reminder_Minuti"] = pd.to_numeric(df["Reminder_Minuti"], errors="coerce").fillna(240).astype(int)
            
        if "Ore" not in df.columns or df["Ore"].isna().all():
            df["Ore"] = df.apply(lambda r: calcola_ore(r.get("Orario Inizio"), r.get("Orario Fine")), axis=1)
            
        for c in cols_standard:
            if c not in df.columns:
                df[c] = ""
                
        return df
    except Exception as e:
        return empty_df

# Salvataggio dati su Google Sheets (su Foglio1)
def salva_dati(df_to_save):
    if "Data_dt" in df_to_save.columns:
        df_to_save = df_to_save.drop(columns=["Data_dt"])
    cols_standard = ["Data", "Mese", "Orario Inizio", "Orario Fine", "Ore", "Ente", "Classe", "Sede", "Modalità", "Svolto", "Escludi_Conteggio", "Note", "Appunto_Multiplo", "Codice_Univoco", "Calendar_ID", "Reminder_Minuti"]
    for c in cols_standard:
        if c not in df_to_save.columns:
            df_to_save[c] = ""
    df_to_save = df_to_save[cols_standard]
    df_to_save = df_to_save.fillna("")
    try:
        worksheet = get_gspread_client_and_sheet("Foglio1")
        if worksheet is None:
            st.error("Impossibile connettersi a Google Sheets. Verifica i Secrets.")
            return
            
        worksheet.clear()
        righe = [df_to_save.columns.values.tolist()] + df_to_save.values.tolist()
        worksheet.update("A1", righe)
    except Exception as e:
        st.error(f"Errore durante il salvataggio su Google Sheets: {e}")

df = carica_dati()

st.title("Gestione Orari e Classi - AgendOne")
st.markdown("---")

tab1, tab2, tab3, tab4 = st.tabs([
    "Inserisci Attività",
    "Gestione Tabelle & Combo",
    "Archivio, Modifica, Report & Riepilogo",
    "Calendario",
])

opzioni_promemoria = {
    "15 minuti prima": 15,
    "30 minuti prima": 30,
    "1 ora prima": 60,
    "2 ore prima": 120,
    "4 ore prima": 240,
    "1 giorno prima": 1440
}

# ================= TAB 1: INSERIMENTO =================
with tab1:
    st.subheader("Registrazione Nuova Attività")
    
    # Flag per inserimento Normale o Multiplo
    tipo_inserimento = st.radio("Seleziona modalità di inserimento:", options=["Inserimento Normale", "Inserimento Multiplo"], horizontal=True)

    with st.form("form_orario", clear_on_submit=True):
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            data_selezionata = st.date_input("Giorno", value=datetime.date.today(), format="DD/MM/YYYY")
            mese_str = traduci_mese(data_selezionata.strftime("%B"))
        with col_d2:
            st.info(f"Mese di riferimento: **{mese_str}**")

        st.markdown("**Orario (Formato obbligatorio: HH:MM-HH:MM, es. 09:00-18:00)**")
        stringa_orario_input = st.text_input(
            "Inserisci orario",
            value="09:00-18:00",
            placeholder="00:00-00:00",
            help="Inserisci l'intervallo orario con ore da 0 a 23 e minuti da 0 a 59 (es. 08:30-13:00)"
        )

        orario_inizio_str, orario_fine_str = valida_e_seleziona_orario(stringa_orario_input)
        
        if orario_inizio_str and orario_fine_str:
            ore_calcolate = calcola_ore(orario_inizio_str, orario_fine_str)
            st.caption(f"Intervallo valido riconosciuto — Durata stimata: **{ore_calcolate} ore**")
        else:
            ore_calcolate = 0.0
            st.warning("Formato orario non valido. Utilizza rigorosamente il formato **00:00-00:00** (es. 09:00-17:30).")

        col_t0, col_t1, col_t2, col_t3 = st.columns(4)
        
        opts_enti = config.get("enti", []).copy()
        opts_classi = config.get("classi", []).copy()
        opts_sedi = config.get("sedi", []).copy()
        opts_modalita = config.get("modalita", []).copy()

        with col_t0:
            ente = st.selectbox("Ente", options=opts_enti if opts_enti else [""], index=0 if opts_enti else 0, key="sel_ente")
            nuovo_ente_libero = st.text_input("O digita nuovo ente:", placeholder="Se non è in elenco...", key="lib_ente")
        with col_t1:
            classe = st.selectbox("Classe", options=opts_classi if opts_classi else [""], index=0 if opts_classi else 0, key="sel_classe")
            nuova_classe_libera = st.text_input("O digita nuova classe:", placeholder="Se non è in elenco...", key="lib_classe")
        with col_t2:
            sede = st.selectbox("Sede", options=opts_sedi if opts_sedi else [""], index=0 if opts_sedi else 0, key="sel_sede")
            nuova_sede_libera = st.text_input("O digita nuova sede:", placeholder="Se non è in elenco...", key="lib_sede")
        with col_t3:
            modalita = st.selectbox("Modalità", options=opts_modalita if opts_modalita else [""], index=0 if opts_modalita else 0, key="sel_mod")
            nuovo_mod_libero = st.text_input("O digita nuova modalità:", placeholder="Se non è in elenco...", key="lib_mod")

        st.selectbox("Avviso / Promemoria Calendar (Disabilitato)", options=["Funzione temporaneamente disabilitata"], index=0, disabled=True)
        st.caption("Nota: La modifica dell'orario di notifica è momentaneamente disabilitata.")
        minuti_scelti = 240

        svolto_iniziale = st.checkbox("Impegno già svolto", value=False)
        escludi_conteggio_iniziale = st.checkbox("Escludi dal conteggio ore", value=False)
        
        note = st.text_area("Note / Descrizione dettagliata", placeholder="Inserisci eventuali dettagli...")
        
        # Casella testo aggiuntiva condizionale per inserimento multiplo
        appunto_multiplo = ""
        if tipo_inserimento == "Inserimento Multiplo":
            st.markdown("---")
            st.markdown("### Sezione Inserimento Multiplo Appuntamenti")
            appunto_multiplo = st.text_area(
                "Testo Appuntamenti Multipli (puoi andare a capo, usa lo scroll)",
                placeholder="Scrivi qui i testi da inserire nella stessa cella...",
                height=150,
                key="textarea_multiplo"
            )

        submit_button_label = "Salva Inserimento Multiplo" if tipo_inserimento == "Inserimento Multiplo" else "Salva Attività"
        submit_button = st.form_submit_button(label=submit_button_label, use_container_width=True)

        if submit_button:
            if not orario_inizio_str or not orario_fine_str:
                st.error("Formato ora obbligatorio non valido. Assicurati di inserire il formato corretto 00:00-00:00 (es. 08:00-14:00).")
            elif orario_inizio_str >= orario_fine_str:
                st.error("L'orario di inizio non può essere successivo o uguale all'orario di fine.")
            else:
                val_ente = nuovo_ente_libero.strip() if nuovo_ente_libero else ente
                val_classe = nuova_classe_libera.strip() if nuova_classe_libera else classe
                val_sede = nuova_sede_libera.strip() if nuova_sede_libera else sede
                val_modalita = nuovo_mod_libero.strip() if nuovo_mod_libero else modalita

                if nuovo_ente_libero and nuovo_ente_libero not in config["enti"]:
                    config["enti"].append(nuovo_ente_libero)
                if nuova_classe_libera and nuova_classe_libera not in config["classi"]:
                    config["classi"].append(nuova_classe_libera)
                if nuova_sede_libera and nuova_sede_libera not in config["sedi"]:
                    config["sedi"].append(nuova_sede_libera)
                if nuovo_mod_libero and nuovo_mod_libero not in config["modalita"]:
                    config["modalita"].append(nuovo_mod_libero)
                salva_config(config)

                # Generazione codice univoco composto da data (DDMMYYYY) + ora (HH:MM:SS senza i due punti o con i due punti)
                now_ts = datetime.datetime.now()
                codice_univoco_generato = data_selezionata.strftime("%d%m%Y") + now_ts.strftime("%H%M%S")

                dati_evento = {
                    "Data": data_selezionata.strftime("%Y-%m-%d"),
                    "Orario Inizio": orario_inizio_str,
                    "Orario Fine": orario_fine_str,
                    "Ente": val_ente,
                    "Classe": val_classe,
                    "Sede": val_sede,
                    "Modalità": val_modalita,
                    "Note": note,
                    "Appunto_Multiplo": appunto_multiplo,
                    "Reminder_Minuti": minuti_scelti
                }
                
                cal_id = sincronizza_google_calendar("crea", dati_evento)

                nuovo_dato = pd.DataFrame({
                    "Data": [data_selezionata.strftime("%Y-%m-%d")],
                    "Mese": [mese_str],
                    "Orario Inizio": [orario_inizio_str],
                    "Orario Fine": [orario_fine_str],
                    "Ore": [ore_calcolate],
                    "Ente": [val_ente],
                    "Classe": [val_classe],
                    "Sede": [val_sede],
                    "Modalità": [val_modalita],
                    "Svolto": [svolto_iniziale],
                    "Escludi_Conteggio": [escludi_conteggio_iniziale],
                    "Note": [note],
                    "Appunto_Multiplo": [appunto_multiplo],
                    "Codice_Univoco": [codice_univoco_generato],
                    "Calendar_ID": [str(cal_id) if cal_id else ""],
                    "Reminder_Minuti": [minuti_scelti]
                })

                df = pd.concat([df, nuovo_dato], ignore_index=True)
                salva_dati(df)
                st.success("Attività salvata e sincronizzata con Google Calendar!")
                st.rerun()

# ================= TAB 2: GESTIONE TABELLE & COMBO =================
with tab2:
    st.subheader("Gestione Avanzata Voci (Enti, Classi, Sedi e Modalità)")
    st.markdown("Gestisci gli elenchi a tendina per l'inserimento rapido delle attività. Il sistema impedisce automaticamente l'inserimento di voci duplicate.")

    def gestisci_sezione_combo(titolo_sezione, chiave_config):
        st.markdown(f"### {titolo_sezione}")
        lista_corrente = config[chiave_config]

        col_sel, col_del = st.columns([3, 1])
        with col_sel:
            voce_selezionata = st.selectbox(
                f"Voci esistenti in {titolo_sezione}",
                options=["-- Seleziona per modificare/eliminare --"] + sorted(lista_corrente),
                key=f"sel_mod_{chiave_config}"
            )
        
        with st.form(key=f"form_add_{chiave_config}", clear_on_submit=True):
            c_in1, c_in2 = st.columns([3, 1])
            with c_in1:
                nuova_voce = st.text_input(f"Aggiungi nuovo elemento a {titolo_sezione}", placeholder=esci_placeholder(titolo_sezione), label_visibility="collapsed")
            with c_in2:
                btn_aggiungi = st.form_submit_button("Aggiungi", use_container_width=True)
            
            if btn_aggiungi:
                nuova_pulita = nuova_voce.strip()
                if not nuova_pulita:
                    st.warning("Il campo non può essere vuoto.")
                elif any(v.lower() == nuova_pulita.lower() for v in lista_corrente):
                    st.error(restituisci_messaggio_duplicato(titolo_sezione, nuova_pulita))
                else:
                    lista_corrente.append(nuova_pulita)
                    salva_config(config)
                    st.success(f"Elemento '{nuova_pulita}' aggiunto con successo!")
                    st.rerun()

        if voce_selezionata != "-- Seleziona per modificare/eliminare --":
            st.markdown(f"**Modifica o rimuovi:** `{voce_selezionata}`")
            with st.form(key=f"form_edit_{chiave_config}"):
                c_ed1, c_ed2, c_ed3 = st.columns([3, 1, 1])
                with c_ed1:
                    valore_modificato = st.text_input("Rinomina voce", value=voce_selezionata, label_visibility="collapsed")
                with c_ed2:
                    btn_salva_mod = st.form_submit_button("Salva", use_container_width=True)
                with c_ed3:
                    btn_elimina = st.form_submit_button("Elimina", use_container_width=True, type="primary")

                if btn_salva_mod:
                    valore_pulito = valore_modificato.strip()
                    if not valore_pulito:
                        st.warning("Il nome non può essere vuoto.")
                    elif valore_pulito.lower() != voce_selezionata.lower() and any(v.lower() == valore_pulito.lower() for v in lista_corrente):
                        st.error("Esiste già una voce con questo nome.")
                    else:
                        idx = lista_corrente.index(voce_selezionata)
                        lista_corrente[idx] = valore_pulito
                        salva_config(config)
                        st.success("Voce aggiornata con successo!")
                        st.rerun()

                if btn_elimina:
                    if voce_selezionata in lista_corrente:
                        lista_corrente.remove(voce_selezionata)
                        salva_config(config)
                        st.success(f"Voce '{voce_selezionata}' eliminata!")
                        st.rerun()

    def esci_placeholder(t):
        if "Enti" in t: return "Es. Scuola Bufalini..."
        if "Classi" in t: return "Es. Classe 4A..."
        if "Sedi" in t: return "Es. Aula Magna..."
        return "Es. Presenza / Online..."

    def restituisci_messaggio_duplicato(t, nome):
        return f"Attenzione: '{nome}' è già presente nell'elenco degli {t.lower()}." if t == "Enti" else f"Attenzione: '{nome}' è già presente nell'elenco delle {t.lower()}."

    col1, col2, col3, col4 = st.columns(4, gap="medium")
    with col1:
        gestisci_sezione_combo("Enti", "enti")
    with col2:
        gestisci_sezione_combo("Classi", "classi")
    with col3:
        gestisci_sezione_combo("Sedi", "sedi")
    with col4:
        gestisci_sezione_combo("Modalità", "modalita")

# ================= TAB 3: ARCHIVIO, MODIFICA, REPORT & RIEPILOGO =================
with tab3:
    st.subheader("Storico, Modifica e Gestione Appuntamenti")

    if not df.empty:
        df_vis = df.copy()
        df_vis["ID_originale"] = df_vis.index
        
        if "Data" in df_vis.columns:
            df_vis["Data_dt"] = df_vis["Data"].apply(parse_data_italiana)
            df_vis["Mese"] = df_vis["Data_dt"].apply(lambda dt: traduci_mese(dt.strftime("%B")).capitalize() if pd.notnull(dt) else "")
            df_vis["Data"] = df_vis["Data_dt"].dt.strftime("%d/%m/%Y").fillna(df_vis["Data"])
            
            df_vis["Ore"] = df_vis.apply(lambda r: calcola_ore(r.get("Orario Inizio"), r.get("Orario Fine")), axis=1)
            df_vis = df_vis.sort_values(by=["Data_dt", "Orario Inizio"], ascending=[True, True])
            
            cols = ["Data"] + [c for c in df_vis.columns if c not in ["Data", "Data_dt", "ID_originale", "Calendar_ID", "Reminder_Minuti"]]
            df_vis = df_vis[cols + ["ID_originale"]]

        filtro = st.text_input("Cerca rapidamente nell'archivio:", placeholder="Filtra per parole chiave...")
        df_mostra = df_vis.copy()
        if filtro:
            df_mostra = df_mostra[df_mostra.apply(lambda r: r.astype(str).str.contains(filtro, case=False).any(), axis=1)]

        df_mostra.insert(0, "Seleziona", False)
        df_mostra.insert(1, "ID", df_mostra["ID_originale"])
        df_mostra = df_mostra.drop(columns=["ID_originale"])

        def colora_righe_tabella(row):
            svolto = row.get("Svolto", False)
            if svolto:
                return ['background-color: #2b2b2b; color: #7f7f7f; text-decoration: line-through'] * len(row)
            mod = str(row.get("Modalità", "")).lower()
            if "presenza" in mod:
                return ['background-color: #1c3d73; color: #ffffff'] * len(row)
            elif "video" in mod:
                return ['background-color: #155c32; color: #ffffff'] * len(row)
            return [''] * len(row)

        df_styled = df_mostra.style.apply(colora_righe_tabella, axis=1)

        df_editato = st.data_editor(
            df_styled,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Seleziona": st.column_config.CheckboxColumn(required=True),
                "ID": st.column_config.NumberColumn(disabled=True),
                "Svolto": st.column_config.CheckboxColumn(required=True),
                "Escludi_Conteggio": st.column_config.CheckboxColumn(required=True),
                "Ore": st.column_config.NumberColumn(format="%.2f h", disabled=True),
            }
        )

        ore_totali_archivio = df_mostra[df_mostra["Escludi_Conteggio"] != True]["Ore"].sum() if "Ore" in df_mostra.columns else 0.0
        st.info(f"**Totale ore (visualizzate in archivio, escluse quelle flaggate):** {ore_totali_archivio:.2f} ore")

        modificato = False
        for _, riga_ed in df_editato.iterrows():
            idx_orig = int(riga_ed["ID"])
            val_nuovo_svolto = bool(riga_ed["Svolto"])
            val_nuovo_escluso = bool(riga_ed["Escludi_Conteggio"])
            if df.loc[idx_orig, "Svolto"] != val_nuovo_svolto or df.loc[idx_orig, "Escludi_Conteggio"] != val_nuovo_escluso:
                df.loc[idx_orig, "Svolto"] = val_nuovo_svolto
                df.loc[idx_orig, "Escludi_Conteggio"] = val_nuovo_escluso
                modificato = True
        if modificato:
            salva_dati(df)
            st.rerun()

        righe_selezionate = df_editato[df_editato["Seleziona"] == True]["ID"].tolist()

        col_act1, col_act2 = st.columns(2)
        with col_act1:
            if st.button("Elimina Selezionati", type="primary", use_container_width=True):
                if righe_selezionate:
                    for r_idx in righe_selezionate:
                        cal_id_esistente = str(df.loc[r_idx, "Calendar_ID"]) if "Calendar_ID" in df.columns else ""
                        if cal_id_esistente and cal_id_esistente.lower() not in ["nan", "none", ""]:
                            sincronizza_google_calendar("elimina", {}, cal_id_esistente)
                    df = df.drop(righe_selezionate).reset_index(drop=True)
                    salva_dati(df)
                    st.success("Righe eliminate e rimosse da Calendar!")
                    st.rerun()
                else:
                    st.warning("Seleziona almeno un appuntamento da eliminare.")
        with col_act2:
            if st.button("Duplica Selezionato", use_container_width=True):
                if len(righe_selezionate) == 1:
                    riga_idx = righe_selezionate[0]
                    nuova_riga = df.loc[riga_idx].copy()
                    if "Note" in nuova_riga and pd.notnull(nuova_riga["Note"]) and str(nuova_riga["Note"]).strip() != "":
                        nuova_riga["Note"] = str(nuova_riga["Note"]) + " (Copia)"
                    else:
                        nuova_riga["Note"] = "Copia"
                    
                    dati_evento = {
                        "Data": str(nuova_riga["Data"]),
                        "Orario Inizio": str(nuova_riga["Orario Inizio"]),
                        "Orario Fine": str(nuova_riga["Orario Fine"]),
                        "Ente": str(nuova_riga.get("Ente", "")),
                        "Classe": str(nuova_riga["Classe"]),
                        "Sede": str(nuova_riga["Sede"]),
                        "Modalità": str(nuova_riga["Modalità"]),
                        "Note": str(nuova_riga["Note"]),
                        "Appunto_Multiplo": str(nuova_riga.get("Appunto_Multiplo", "")),
                        "Reminder_Minuti": int(nuova_riga.get("Reminder_Minuti", 240))
                    }
                    cal_id = sincronizza_google_calendar("crea", dati_evento)
                    nuova_riga["Calendar_ID"] = str(cal_id) if cal_id else ""
                    
                    df = pd.concat([df, pd.DataFrame([nuova_riga])], ignore_index=True)
                    salva_dati(df)
                    st.success("Appuntamento duplicato e aggiunto a Calendar!")
                    st.rerun()
                elif len(righe_selezionate) > 1:
                    st.warning("Seleziona un solo appuntamento alla volta per la duplicazione rapida.")
                else:
                    st.warning("Seleziona un appuntamento da duplicare.")

        st.markdown("---")

        if len(righe_selezionate) == 1:
            riga_idx = righe_selezionate[0]
            riga_corrente = df.loc[riga_idx]

            st.markdown(f"### Modifica Appuntamento (Riga ID {riga_idx})")
            with st.form("form_modifica_multipla"):
                try:
                    data_default = datetime.datetime.strptime(str(riga_corrente["Data"]), "%Y-%m-%d").date()
                except:
                    data_default = datetime.date.today()

                orario_esistente_default = f"{riga_corrente.get('Orario Inizio', '09:00')}-{riga_corrente.get('Orario Fine', '18:00')}"

                mod_data = st.date_input("Data", value=data_default, format="DD/MM/YYYY")

                st.markdown("**Orario (Formato obbligatorio: HH:MM-HH:MM, es. 09:00-18:00)**")
                mod_stringa_orario = st.text_input(
                    "Modifica orario",
                    value=orario_esistente_default,
                    placeholder="00:00-00:00"
                )

                mod_orario_i_str, mod_orario_f_str = valida_e_seleziona_orario(mod_stringa_orario)
                if mod_orario_i_str and mod_orario_f_str:
                    mod_ore_calc = calcola_ore(mod_orario_i_str, mod_orario_f_str)
                    st.caption(f"Intervallo valido riconosciuto — Durata stimata: **{mod_ore_calc} ore**")
                else:
                    mod_ore_calc = 0.0
                    st.warning("Formato orario non valido. Utilizza rigorosamente il formato **00:00-00:00**.")

                # Gestione Enti
                enti_esistenti = config.get("enti", []).copy()
                val_ente_corrente = str(riga_corrente.get("Ente", "")).strip()
                if val_ente_corrente and val_ente_corrente not in enti_esistenti:
                    enti_esistenti.append(val_ente_corrente)
                idx_ente = enti_esistenti.index(val_ente_corrente) if val_ente_corrente in enti_esistenti else 0
                mod_ente_sel = st.selectbox("Ente", options=enti_esistenti if enti_esistenti else [""], index=idx_ente if enti_esistenti else 0, key="mod_sel_ente")
                mod_ente_libero = st.text_input("O digita nuovo ente (Modifica):", placeholder="Se non è in elenco...", key="mod_lib_ente")

                # Gestione Classi
                classi_esistenti = config.get("classi", []).copy()
                val_classe_corrente = str(riga_corrente.get("Classe", "")).strip()
                if val_classe_corrente and val_classe_corrente not in classi_esistenti:
                    classi_esistenti.append(val_classe_corrente)
                idx_classe = classi_esistenti.index(val_classe_corrente) if val_classe_corrente in classi_esistenti else 0
                mod_classe_sel = st.selectbox("Classe", options=classi_esistenti if classi_esistenti else [""], index=idx_classe if classi_esistenti else 0, key="mod_sel_classe")
                mod_classe_libera = st.text_input("O digita nuova classe (Modifica):", placeholder="Se non è in elenco...", key="mod_lib_classe")

                # Gestione Sedi
                sedi_esistenti = config.get("sedi", []).copy()
                val_sede_corrente = str(riga_corrente.get("Sede", "")).strip()
                if val_sede_corrente and val_sede_corrente not in sedi_esistenti:
                    sedi_esistenti.append(val_sede_corrente)
                idx_sede = sedi_esistenti.index(val_sede_corrente) if val_sede_corrente in sedi_esistenti else 0
                mod_sede_sel = st.selectbox("Sede", options=sedi_esistenti if sedi_esistenti else [""], index=idx_sede if sedi_esistenti else 0, key="mod_sel_sede")
                mod_sede_libera = st.text_input("O digita nuova sede (Modifica):", placeholder="Se non è in elenco...", key="mod_lib_sede")

                # Gestione Modalità
                modalita_esistenti = config.get("modalita", []).copy()
                val_mod_corrente = str(riga_corrente.get("Modalità", "")).strip()
                if val_mod_corrente and val_mod_corrente not in modalita_esistenti:
                    modalita_esistenti.append(val_mod_corrente)
                idx_mod = modalita_esistenti.index(val_mod_corrente) if val_mod_corrente in modalita_esistenti else 0
                mod_modalita_sel = st.selectbox("Modalità", options=modalita_esistenti if modalita_esistenti else [""], index=idx_mod if modalita_esistenti else 0, key="mod_sel_mod")
                mod_modalita_libera = st.text_input("O digita nuova modalità (Modifica):", placeholder="Se non è in elenco...", key="mod_lib_mod")
                
                attuale_minuti = int(riga_corrente.get("Reminder_Minuti", 240))
                
                st.selectbox("Modifica Avviso / Promemoria Calendar (Disabilitato)", options=["Funzione temporaneamente disabilitata"], index=0, disabled=True)
                st.caption("Nota: La modifica dell'orario di notifica è momentaneamente disabilitata.")
                minuti_scelti_mod = attuale_minuti

                svolto_corrente = bool(riga_corrente["Svolto"]) if "Svolto" in riga_corrente else False
                mod_svolto = st.checkbox("Impegno svolto", value=svolto_corrente)

                escluso_corrente = bool(riga_corrente["Escludi_Conteggio"]) if "Escludi_Conteggio" in riga_corrente else False
                mod_escluso = st.checkbox("Escludi dal conteggio ore", value=escluso_corrente)
                
                mod_note = st.text_area("Note", value=str(riga_corrente["Note"]))
                
                # Modifica del testo inserito per il multi-impegno (richiesta specifica)
                attuale_appunto_multiplo = str(riga_corrente.get("Appunto_Multiplo", "")) if pd.notnull(riga_corrente.get("Appunto_Multiplo", "")) else ""
                mod_appunto_multiplo = st.text_area("Modifica Testo Inserito (Multi-impegno / Nota multipla)", value=attuale_appunto_multiplo, height=120)

                if st.form_submit_button("Salva Modifiche", use_container_width=True):
                    if not mod_orario_i_str or not mod_orario_f_str:
                        st.error("Formato ora obbligatorio non valido. Utilizza il formato 00:00-00:00.")
                    elif mod_orario_i_str >= mod_orario_f_str:
                        st.error("L'orario di inizio non può essere successivo o uguale all'orario di fine.")
                    else:
                        val_ente_finale = mod_ente_libero.strip() if mod_ente_libero else mod_ente_sel
                        val_classe_finale = mod_classe_libera.strip() if mod_classe_libera else mod_classe_sel
                        val_sede_finale = mod_sede_libera.strip() if mod_sede_libera else mod_sede_sel
                        val_modalita_finale = mod_modalita_libera.strip() if mod_modalita_libera else mod_modalita_sel

                        if mod_ente_libero and mod_ente_libero not in config["enti"]:
                            config["enti"].append(mod_ente_libero)
                        if mod_classe_libera and mod_classe_libera not in config["classi"]:
                            config["classi"].append(mod_classe_libera)
                        if mod_sede_libera and mod_sede_libera not in config["sedi"]:
                            config["sedi"].append(mod_sede_libera)
                        if mod_modalita_libera and mod_modalita_libera not in config["modalita"]:
                            config["modalita"].append(mod_modalita_libera)
                        salva_config(config)

                        df.loc[riga_idx, "Data"] = mod_data.strftime("%Y-%m-%d")
                        df.loc[riga_idx, "Mese"] = traduci_mese(mod_data.strftime("%B"))
                        df.loc[riga_idx, "Orario Inizio"] = mod_orario_i_str
                        df.loc[riga_idx, "Orario Fine"] = mod_orario_f_str
                        df.loc[riga_idx, "Ore"] = mod_ore_calc
                        df.loc[riga_idx, "Ente"] = val_ente_finale
                        df.loc[riga_idx, "Classe"] = val_classe_finale
                        df.loc[riga_idx, "Sede"] = val_sede_finale
                        df.loc[riga_idx, "Modalità"] = val_modalita_finale
                        df.loc[riga_idx, "Svolto"] = mod_svolto
                        df.loc[riga_idx, "Escludi_Conteggio"] = mod_escluso
                        df.loc[riga_idx, "Note"] = mod_note
                        df.loc[riga_idx, "Appunto_Multiplo"] = mod_appunto_multiplo
                        df.loc[riga_idx, "Reminder_Minuti"] = minuti_scelti_mod

                        dati_evento = {
                            "Data": mod_data.strftime("%Y-%m-%d"),
                            "Orario Inizio": mod_orario_i_str,
                            "Orario Fine": mod_orario_f_str,
                            "Ente": val_ente_finale,
                            "Classe": val_classe_finale,
                            "Sede": val_sede_finale,
                            "Modalità": val_modalita_finale,
                            "Note": mod_note,
                            "Appunto_Multiplo": mod_appunto_multiplo,
                            "Reminder_Minuti": minuti_scelti_mod
                        }

                        cal_id_esistente = str(df.loc[riga_idx, "Calendar_ID"]) if "Calendar_ID" in df.columns else ""
                        if cal_id_esistente and cal_id_esistente.lower() not in ["nan", "none", ""]:
                            res_id = sincronizza_google_calendar("aggiorna", dati_evento, cal_id_esistente)
                            df.loc[riga_idx, "Calendar_ID"] = str(res_id) if res_id else cal_id_esistente
                        else:
                            cal_id = sincronizza_google_calendar("crea", dati_evento)
                            df.loc[riga_idx, "Calendar_ID"] = str(cal_id) if cal_id else ""

                        salva_dati(df)
                        st.success("Modifiche salvate e calendario aggiornato!")
                        st.rerun()

        st.markdown("---")
        st.subheader("Generazione Report, Ricerca & Ordinamento")

        col_t1, col_t2, col_t3 = st.columns(3)
        with col_t1:
            ricerca_libera = st.text_input("Ricerca libera", placeholder="Parole chiave...")
        with col_t2:
            data_inizio_filtro = st.date_input("Data Inizio", value=None, format="DD/MM/YYYY")
        with col_t3:
            data_fine_filtro = st.date_input("Data Fine", value=None, format="DD/MM/YYYY")

        col_f0, col_f1, col_f2, col_f3 = st.columns(4)
        with col_f0:
            enti_disponibili = ["Tutti"] + sorted(df["Ente"].dropna().unique().tolist() if "Ente" in df.columns else [])
            filtro_ente = st.selectbox("Filtra per Ente", options=enti_disponibili)
        with col_f1:
            classi_disponibili = ["Tutti"] + sorted(df["Classe"].dropna().unique().tolist())
            filtro_classe = st.selectbox("Filtra per Classe", options=classi_disponibili)
        with col_f2:
            sedi_disponibili = ["Tutti"] + sorted(df["Sede"].dropna().unique().tolist())
            filtro_sede = st.selectbox("Filtra per Sede", options=sedi_disponibili)
        with col_f3:
            modalita_disponibili = ["Tutti"] + sorted(df["Modalità"].dropna().unique().tolist())
            filtro_modalita = st.selectbox("Filtra per Modalità", options=modalita_disponibili)

        st.markdown("##### Opzioni di Ordinamento Report")
        col_ord1, col_ord2 = st.columns(2)
        with col_ord1:
            campi_ordinamento = {
                "Data": "Data_dt",
                "Ente": "Ente",
                "Classe": "Classe",
                "Sede": "Sede",
                "Tipologia / Modalità": "Modalità"
            }
            scelta_ordinamento = st.selectbox("Ordina per", options=list(campi_ordinamento.keys()))
        with col_ord2:
            direzione_ordinamento = st.radio("Direzione", options=["Crescente (A-Z / Dal più vecchio)", "Decrescente (Z-A / Dal più recente)"], horizontal=True)
        crescente = "Crescente" in direzione_ordinamento

        df_report = df.copy()
        if "Data_dt" not in df_report.columns:
            df_report["Data_dt"] = df_report["Data"].apply(parse_data_italiana)
        df_report["Ore"] = df_report.apply(lambda r: calcola_ore(r.get("Orario Inizio"), r.get("Orario Fine")), axis=1)

        if data_inizio_filtro:
            df_report = df_report[df_report["Data_dt"] >= pd.to_datetime(data_inizio_filtro)]
        if data_fine_filtro:
            df_report = df_report[df_report["Data_dt"] <= pd.to_datetime(data_fine_filtro)]

        if filtro_ente != "Tutti":
            df_report = df_report[df_report["Ente"] == filtro_ente]
        if filtro_classe != "Tutti":
            df_report = df_report[df_report["Classe"] == filtro_classe]
        if filtro_sede != "Tutti":
            df_report = df_report[df_report["Sede"] == filtro_sede]
        if filtro_modalita != "Tutti":
            df_report = df_report[df_report["Modalità"] == filtro_modalita]

        if ricerca_libera:
            termini = [t.strip() for t in ricerca_libera.split(",") if t.strip()]
            if termini:
                def match_multipli(row):
                    riga_str = " ".join(row.astype(str).values).lower()
                    return any(termine.lower() in riga_str for termine in termini)
                df_report = df_report[df_report.apply(match_multipli, axis=1)]

        colonna_ordinamento = campi_ordinamento[scelta_ordinamento]
        if colonna_ordinamento in df_report.columns:
            if colonna_ordinamento == "Data_dt":
                df_report = df_report.sort_values(by=["Data_dt", "Orario Inizio"], ascending=[crescente, True])
            else:
                df_report = df_report.sort_values(by=[colonna_ordinamento, "Data_dt"], ascending=[crescente, True])

        ore_totali = df_report[df_report["Escludi_Conteggio"] != True]["Ore"].sum()

        st.success(f"**Risultati Report Filtrati:** {len(df_report)} attività trovate | **Totale Ore Report (escluse quelle flaggate):** **{ore_totali:.2f} ore**")

        if not df_report.empty:
            st.markdown("---")
            st.markdown("### Elenco Attività in Evidenza")

            for _, row in df_report.iterrows():
                parsed_dt = parse_data_italiana(row["Data"])
                data_formattata = parsed_dt.strftime("%d/%m/%Y") if pd.notnull(parsed_dt) else str(row["Data"])
                ente = str(row.get("Ente", ""))
                classe = str(row["Classe"])
                sede = str(row["Sede"])
                modalita = str(row["Modalità"])
                orario_i = str(row["Orario Inizio"])
                orario_f = str(row["Orario Fine"])
                ore_val = row["Ore"]
                svolto_card = bool(row["Svolto"]) if "Svolto" in row else False
                escluso_card = bool(row["Escludi_Conteggio"]) if "Escludi_Conteggio" in row else False
                note = str(row["Note"]) if pd.notnull(row["Note"]) else ""
                appunto_mult = str(row.get("Appunto_Multiplo", "")) if pd.notnull(row.get("Appunto_Multiplo", "")) else ""

                if svolto_card:
                    bg_color = "#2b2b2b"
                    border_color = "#444444"
                    text_style = "color: #7f7f7f; text-decoration: line-through;"
                else:
                    mod_lower = modalita.lower()
                    if "presenza" in mod_lower:
                        bg_color = "#1c3d73"
                        border_color = "#3b73c4"
                    elif "video" in mod_lower:
                        bg_color = "#155c32"
                        border_color = "#2fa866"
                    else:
                        bg_color = "#262626"
                        border_color = "#555555"
                    text_style = "color: #ffffff;"

                badge_escluso = " | <span style='color: #ff9999;'>[Escluso conteggio]</span>" if escluso_card else ""
                multiplo_html = f"<br><em>Testo Multi-impegno:</em> <pre style='background: rgba(0,0,0,0.2); padding: 5px; border-radius: 4px; color: inherit; white-space: pre-wrap;'>{appunto_mult}</pre>" if appunto_mult else ""

                st.markdown(
                    f"""
                    <div style="background-color: {bg_color}; border: 1px solid {border_color}; padding: 15px; border-radius: 8px; margin-bottom: 10px; {text_style}">
                        <strong>{data_formattata}</strong> | {orario_i} - {orario_f} ({ore_val:.2f}h){badge_escluso}<br>
                        <strong>Ente:</strong> {ente if ente else 'N/D'} | <strong>Classe/Committente:</strong> {classe} | <strong>Sede:</strong> {sede} | <strong>Modalità:</strong> {modalita}<br>
                        <em>Note:</em> {note if note else 'Nessuna nota'}
                        {multiplo_html}
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        st.markdown("---")
        c_exp1, c_exp2, c_exp3, c_exp4 = st.columns(4)

        with c_exp1:
            df_export = df_report.drop(columns=["Data_dt"], errors="ignore")
            csv_data = df_export.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Scarica Report CSV",
                data=csv_data,
                file_name="report_attivita.csv",
                mime="text/csv",
                use_container_width=True
            )

        with c_exp2:
            buffer_excel = io.BytesIO()
            with pd.ExcelWriter(buffer_excel, engine='xlsxwriter') as writer:
                df_export.to_excel(writer, index=False, sheet_name='Report')
                
                worksheet = writer.sheets['Report']
                for i, col in enumerate(df_export.columns):
                    lunghezza_massima = max(
                        df_export[col].astype(str).map(len).max(),
                        len(str(col))
                    )
                    worksheet.set_column(i, i, max(lunghezza_massima + 3, 12))
                    
            buffer_excel.seek(0)
            st.download_button(
                label="Scarica Excel (Report)",
                data=buffer_excel,
                file_name="report_attivita.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

        with c_exp3:
            pdf_data = genera_pdf_report(df_report)
            if pdf_data:
                st.download_button(
                    label="Scarica Report PDF",
                    data=pdf_data,
                    file_name="report_attivita.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            else:
                st.button("PDF non disponibile", disabled=True, use_container_width=True, help="Installa reportlab per abilitare l'esportazione PDF")

        with c_exp4:
            if st.button("Sincronizza eventi mancanti", use_container_width=True, help="Invia a Google Calendar gli eventi salvati che non hanno ancora un ID Calendar"):
                count_sinc = 0
                for idx, row in df.iterrows():
                    cal_id = str(row.get("Calendar_ID", ""))
                    if not cal_id or cal_id.lower() in ["nan", "none", ""]:
                        dati_evento = {
                            "Data": str(row["Data"]),
                            "Orario Inizio": str(row["Orario Inizio"]),
                            "Orario Fine": str(row["Orario Fine"]),
                            "Ente": str(row.get("Ente", "")),
                            "Classe": str(row.get("Classe", "")),
                            "Sede": str(row.get("Sede", "")),
                            "Modalità": str(row.get("Modalità", "")),
                            "Note": str(row.get("Note", "")),
                            "Appunto_Multiplo": str(row.get("Appunto_Multiplo", "")),
                            "Reminder_Minuti": int(row.get("Reminder_Minuti", 240))
                        }
                        nuovo_id = sincronizza_google_calendar("crea", dati_evento)
                        if nuovo_id:
                            df.loc[idx, "Calendar_ID"] = str(nuovo_id)
                            count_sinc += 1
                if count_sinc > 0:
                    salva_dati(df)
                    st.success(f"Sincronizzati con successo {count_sinc} eventi su Google Calendar!")
                    st.rerun()
                else:
                    st.info("Tutti gli eventi risultano già sincronizzati.")

# ================= TAB 4: CALENDARIO =================
with tab4:
    st.subheader("Vista Calendario Mensile")
    
    if "cal_anno" not in st.session_state:
        st.session_state["cal_anno"] = datetime.date.today().year
    if "cal_mese" not in st.session_state:
        st.session_state["cal_mese"] = datetime.date.today().month

    col_nav1, col_nav2, col_nav3, col_nav4, col_nav5 = st.columns([1, 1, 2, 1, 1])
    with col_nav1:
        if st.button("<< Anno -", use_container_width=True):
            st.session_state["cal_anno"] -= 1
            st.rerun()
    with col_nav2:
        if st.button("< Mese -", use_container_width=True):
            if st.session_state["cal_mese"] == 1:
                st.session_state["cal_mese"] = 12
                st.session_state["cal_anno"] -= 1
            else:
                st.session_state["cal_mese"] -= 1
            st.rerun()
    with col_nav3:
        mese_corrente_nome = traduci_mese(datetime.date(st.session_state["cal_anno"], st.session_state["cal_mese"], 1).strftime("%B")).capitalize()
        st.markdown(f"<h3 style='text-align: center; margin: 0;'>{mese_corrente_nome} {st.session_state['cal_anno']}</h3>", unsafe_allow_html=True)
    with col_nav4:
        if st.button("Mese + >", use_container_width=True):
            if st.session_state["cal_mese"] == 12:
                st.session_state["cal_mese"] = 1
                st.session_state["cal_anno"] += 1
            else:
                st.session_state["cal_mese"] += 1
            st.rerun()
    with col_nav5:
        if st.button("Anno + >>", use_container_width=True):
            st.session_state["cal_anno"] += 1
            st.rerun()

    st.markdown("---")

    df_cal = df.copy()
    if not df_cal.empty:
        df_cal["Data_dt"] = df_cal["Data"].apply(parse_data_italiana)
        df_cal["Ore"] = df_cal.apply(lambda r: calcola_ore(r.get("Orario Inizio"), r.get("Orario Fine")), axis=1)
        
        df_mese = df_cal[
            (df_cal["Data_dt"].notna()) & 
            (df_cal["Data_dt"].dt.year == st.session_state["cal_anno"]) & 
            (df_cal["Data_dt"].dt.month == st.session_state["cal_mese"])
        ]
    else:
        df_mese = pd.DataFrame()

    num_appuntamenti_mensili = len(df_mese)
    df_ore_valide = df_mese[df_mese["Escludi_Conteggio"] != True] if not df_mese.empty else pd.DataFrame()
    ore_appuntamenti_mensili = df_ore_valide["Ore"].sum() if not df_ore_valide.empty else 0.0

    st.markdown(
        f"""
        <div style="display: flex; gap: 20px; margin-bottom: 20px;">
            <div style="background-color: #1c3d73; color: white; padding: 12px 20px; border-radius: 8px; flex: 1; text-align: center;">
                <span style="font-size: 14px; opacity: 0.8;">Numero Appuntamenti Mensili</span><br>
                <span style="font-size: 22px; font-weight: bold;">{num_appuntamenti_mensili}</span>
            </div>
            <div style="background-color: #155c32; color: white; padding: 12px 20px; border-radius: 8px; flex: 1; text-align: center;">
                <span style="font-size: 14px; opacity: 0.8;">Ore Appuntamenti Mensili (Valide)</span><br>
                <span style="font-size: 22px; font-weight: bold;">{ore_appuntamenti_mensili:.2f} h</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    import calendar
    cal = calendar.Calendar(firstweekday=0)
    giorni_mese = cal.monthdayscalendar(st.session_state["cal_anno"], st.session_state["cal_mese"])
    giorni_settimana = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
    
    impegni_per_giorno = {}
    if not df_mese.empty:
        for _, row in df_mese.iterrows():
            giorno_num = row["Data_dt"].day
            if giorno_num not in impegni_per_giorno:
                impegni_per_giorno[giorno_num] = []
            
            impegni_per_giorno[giorno_num].append({
                "ente": str(row.get("Ente", "")),
                "classe": str(row.get("Classe", "")),
                "orario": f"{str(row.get('Orario Inizio', ''))} - {str(row.get('Orario Fine', ''))}",
                "ore": row.get("Ore", 0.0),
                "sede": str(row.get("Sede", "")),
                "modalita": str(row.get("Modalità", "")),
                "note": str(row.get("Note", "")),
                "svolto": bool(row.get("Svolto", False)),
                "escluso": bool(row.get("Escludi_Conteggio", False))
            })

    html_righe = ""
    for settimana in giorni_mese:
        html_righe += "<tr>"
        for giorno in settimana:
            if giorno == 0:
                html_righe += '<td class="cal-cell-empty"></td>'
            else:
                ha_impegni = giorno in impegni_per_giorno
                bg_style = "background-color: #183025; border: 1px solid #2fa866;" if ha_impegni else "background-color: #1e1e1e;"
                
                html_righe += f'<td class="cal-cell" style="{bg_style}">'
                html_righe += f'<div class="day-number">{giorno}</div>'

                if ha_impegni:
                    lista_imp = impegni_per_giorno[giorno]
                    dettaglio_html = f"<b>Impegni del {giorno}/{st.session_state['cal_mese']}/{st.session_state['cal_anno']}</b>"
                    dettaglio_html += "<hr style='margin: 4px 0; border-color: #444;'>"
                    
                    for imp in lista_imp:
                        barrato_stile = "text-decoration: line-through; color: #aaa;" if imp["svolto"] else ""
                        escl_nota = " [Escluso]" if imp["escluso"] else ""
                        dettaglio_html += f"<div style='margin-bottom: 6px; {barrato_stile}'>"
                        dettaglio_html += f"<b>{imp['orario']}</b> ({imp['ore']}h){escl_nota}<br>"
                        dettaglio_html += f"<b>Ente:</b> {imp['ente']} | <b>Classe:</b> {imp['classe']}<br>"
                        dettaglio_html += f"<b>Sede:</b> {imp['sede']} ({imp['modalita']})"
                        if imp['note']:
                            dettaglio_html += f"<br><em>Note:</em> {imp['note']}"
                        dettaglio_html += "</div>"

                    html_righe += '<div class="tooltip-container">'
                    if len(lista_imp) == 1:
                        imp_singolo = lista_imp[0]
                        testo_badge = f"{imp_singolo['orario']} - {imp_singolo['classe']}"
                        html_righe += f'<span class="badge-impegno">{testo_badge}</span>'
                    else:
                        html_righe += f'<span class="badge-impegno-multi">{len(lista_imp)} Appuntamenti</span>'
                    
                    html_righe += f'<div class="tooltip-content">{dettaglio_html}</div>'
                    html_righe += '</div>'

                html_righe += '</td>'
        html_righe += "</tr>"

    th_html = "".join([f'<th class="cal-th">{gs}</th>' for gs in giorni_settimana])

    html_cal = f"""
    <style>
      .cal-table {{
        width: 100%;
        border-collapse: collapse;
        table-layout: fixed;
      }}
      .cal-th {{
        background-color: #1c3d73;
        color: white;
        text-align: center;
        padding: 10px;
        font-size: 14px;
        border: 1px solid #333333;
      }}
      .cal-cell {{
        height: 90px;
        vertical-align: top;
        padding: 6px;
        border: 1px solid #444444;
        background-color: #1e1e1e;
        position: relative;
      }}
      .cal-cell-empty {{
        background-color: #121212;
        border: 1px solid #2a2a2a;
        height: 90px;
      }}
      .day-number {{
        font-weight: bold;
        font-size: 13px;
        color: #ffffff;
        margin-bottom: 4px;
      }}
      .badge-impegno {{
        background-color: #2fa866;
        color: white;
        font-size: 11px;
        padding: 2px 6px;
        border-radius: 4px;
        display: block;
        margin-bottom: 2px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }}
      .badge-impegno-multi {{
        background-color: #c0392b;
        color: white;
        font-size: 11px;
        padding: 2px 6px;
        border-radius: 4px;
        display: block;
        margin-bottom: 2px;
        text-align: center;
        font-weight: bold;
      }}
      .tooltip-container {{
        position: relative;
        display: block;
        cursor: pointer;
      }}
      .tooltip-content {{
        visibility: hidden;
        width: 260px;
        background-color: #2c3e50;
        color: #fff;
        text-align: left;
        border-radius: 6px;
        padding: 8px 10px;
        position: absolute;
        z-index: 100;
        bottom: 125%;
        left: 50%;
        transform: translateX(-50%);
        opacity: 0;
        transition: opacity 0.3s;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.5);
        font-size: 12px;
        line-height: 1.4;
      }}
      .tooltip-container:hover .tooltip-content {{
        visibility: visible;
        opacity: 1;
      }}
    </style>
    <table class="cal-table">
      <tr>{th_html}</tr>
      {html_righe}
    </table>
    """

    st.markdown(html_cal, unsafe_allow_html=True)
