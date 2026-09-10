import datetime
import io
import json
import os
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
        border-radius: 8px !important;
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

    button[data-baseweb="tab"][aria-selected="true"] {
        background-color: #2563eb !important;
        color: #ffffff !important;
        border: 1px solid #2563eb !important;
        box-shadow: 0 4px 10px rgba(37, 99, 235, 0.4) !important;
    }
    
    div[data-baseweb="tab-highlight"] { display: none !important; }
    div[data-baseweb="tab-border"] { display: none !important; }
    div[data-baseweb="tab-list"] { gap: 10px; }

    /* Sfondo delle caselle del calendario */
    .fc-daygrid-day, .fc-timegrid-slot, .fc-theme-standard td {
        background-color: #e6f2ff !important;
    }
    .fc-day-today { background-color: #cce5ff !important; }

    /* Compattezza estrema per i selettori orario multipli */
    .time-slot-group {
        display: flex;
        gap: 2px;
        align-items: center;
    }
    .time-slot-group [data-baseweb="select"] {
        min-width: 50px !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Dizionario per i mesi in italiano
MESI_ITALIANI = {
    "January": "Gennaio", "February": "Febbraio", "March": "Marzo", "April": "Aprile",
    "May": "Maggio", "June": "Giugno", "July": "Luglio", "August": "Agosto",
    "September": "Settembre", "October": "Ottobre", "November": "Novembre", "December": "Dicembre",
}

def traduci_mese(mese_en):
    return MESI_ITALIANI.get(mese_en, mese_en)

def parse_data_italiana(val):
    if pd.isna(val) or str(val).strip() == "" or str(val).lower() in ["none", "nan"]:
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
            return datetime.datetime(int(parti[2]), int(parti[1]), int(parti[0]))
    except:
        pass
    return pd.to_datetime(val_str, errors="coerce", dayfirst=True)

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

def genera_pdf_report(df_report):
    try:
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from collections import defaultdict
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=20)
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
                if not e_nome or e_nome.lower() == "nan": e_nome = "Non Specificato"
                c_nome = str(row.get("Classe", "")).strip()
                if not c_nome or c_nome.lower() == "nan": c_nome = "Non Specificata"
                gruppi_ente_classe[e_nome][c_nome].append(row)
                
            col_widths = [60, 75, 120, 100, 75, 220, 52]

            for ente_nome, classi_dict in gruppi_ente_classe.items():
                elements.append(Paragraph(f"Ente: <b>{ente_nome}</b>", ente_header_style))
                det_data = [[Paragraph("Data", th_style), Paragraph("Orario", th_style), Paragraph("Classe / Committente", th_style), Paragraph("Sede", th_style), Paragraph("Modalità", th_style), Paragraph("Note / Dettagli", th_style), Paragraph("Ore", th_style)]]
                
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
                    
                    det_data.append([Paragraph(f"<b>Totale parziale ({classe_nome}):</b>", style_subtot_classe), "", "", "", "", "", Paragraph(f"<b>{totale_ore_classe:.2f}h</b>", style_subtot_val_classe)])
                    table_styles.append(('SPAN', (0, row_idx), (5, row_idx)))
                    table_styles.append(('BACKGROUND', (0, row_idx), (-1, row_idx), colors.HexColor('#e6f2ff')))
                    row_idx += 1

                det_data.append([Paragraph(f"<b>Totale Ore Parziali ({ente_nome}):</b>", ParagraphStyle('SubTot', parent=styles['Normal'], alignment=2, fontSize=8, fontName='Helvetica-Bold', textColor=colors.HexColor('#1c3d73'))), "", "", "", "", "", Paragraph(f"<b>{totale_ore_ente:.2f}h</b>", ParagraphStyle('SubTotVal', parent=styles['Normal'], fontSize=8, fontName='Helvetica-Bold', textColor=colors.HexColor('#1c3d73')))])
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
        return spreadsheet.worksheet(nome_foglio)
    except Exception as e:
        st.error(f"Errore durante la connessione a Google Sheets ('{nome_foglio}'): {e}")
        return None

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
                'description': f"Ente: {dati_evento.get('Ente', '')}\nNote: {dati_evento.get('Note', '')}\n{dati_evento.get('Appunto_Multiplo', '')}\nGestito da AgendOne",
                'start': {'dateTime': start_datetime, 'timeZone': 'Europe/Rome'},
                'end': {'dateTime': end_datetime, 'timeZone': 'Europe/Rome'},
                'reminders': {'useDefault': True},
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
                if err.resp.status != 404: raise err
            return None
    except Exception as e:
        st.error(f"Errore di sincronizzazione Google Calendar: {e}")
        return None

def carica_config():
    default_config = {"enti": [], "classi": [], "sedi": [], "modalita": []}
    try:
        worksheet = get_gspread_client_and_sheet("Tabelle")
        if worksheet is None: return default_config
        all_values = worksheet.get_all_values()
        if not all_values or len(all_values) < 2: return default_config
        
        headers = [h.strip() for h in all_values[0]]
        idx_enti = headers.index("T_Enti") if "T_Enti" in headers else -1
        idx_classi = headers.index("T_Classi") if "T_Classi" in headers else -1
        idx_sedi = headers.index("T_Sedi") if "T_Sedi" in headers else -1
        idx_modalita = headers.index("T_Modalita") if "T_Modalita" in headers else -1

        enti, classi, sedi, modalita = [], [], [], []
        for row in all_values[1:]:
            if idx_enti != -1 and len(row) > idx_enti and row[idx_enti].strip(): enti.append(row[idx_enti].strip())
            if idx_classi != -1 and len(row) > idx_classi and row[idx_classi].strip(): classi.append(row[idx_classi].strip())
            if idx_sedi != -1 and len(row) > idx_sedi and row[idx_sedi].strip(): sedi.append(row[idx_sedi].strip())
            if idx_modalita != -1 and len(row) > idx_modalita and row[idx_modalita].strip(): modalita.append(row[idx_modalita].strip())

        return {"enti": enti, "classi": classi, "sedi": sedi, "modalita": modalita}
    except Exception as e:
        return default_config

def salva_config(config):
    try:
        worksheet = get_gspread_client_and_sheet("Tabelle")
        if worksheet is None: return
        enti, classi, sedi, modalita = config.get("enti", []), config.get("classi", []), config.get("sedi", []), config.get("modalita", [])
        max_len = max(len(enti), len(classi), len(sedi), len(modalita), 0)
        rows = [["T_Enti", "T_Classi", "T_Sedi", "T_Modalita"]]
        for i in range(max_len):
            rows.append([enti[i] if i < len(enti) else "", classi[i] if i < len(classi) else "", sedi[i] if i < len(sedi) else "", modalita[i] if i < len(modalita) else ""])
        worksheet.clear()
        worksheet.update("A1", rows)
    except Exception as e:
        st.error(f"Errore durante il salvataggio nel foglio 'Tabelle': {e}")

config = carica_config()

def carica_dati():
    cols_standard = ["Data", "Mese", "Orario Inizio", "Orario Fine", "Ore", "Ente", "Classe", "Sede", "Modalità", "Svolto", "Escludi_Conteggio", "Note", "Appunto_Multiplo", "Codice_Univoco", "Calendar_ID", "Reminder_Minuti"]
    empty_df = pd.DataFrame(columns=cols_standard)
    try:
        worksheet = get_gspread_client_and_sheet("Foglio1")
        if worksheet is None: return empty_df
        data = worksheet.get_all_records()
        if not data: return empty_df
        df = pd.DataFrame(data)
        
        if "Committente" in df.columns and "Classe" not in df.columns: df = df.rename(columns={"Committente": "Classe"})
        if "Luogo" in df.columns and "Sede" not in df.columns: df = df.rename(columns={"Luogo": "Sede"})
            
        if "Data" in df.columns:
            df["Data_dt"] = df["Data"].apply(parse_data_italiana)
            mask_valid = df["Data_dt"].notna()
            df.loc[mask_valid, "Data"] = df.loc[mask_valid, "Data_dt"].dt.strftime("%Y-%m-%d")
            df.loc[mask_valid, "Mese"] = df.loc[mask_valid, "Data_dt"].apply(lambda dt: traduci_mese(dt.strftime("%B")).capitalize())
            
        df["Svolto"] = df["Svolto"].apply(lambda x: True if str(x).lower() in ["true", "1", "yes", "vero", "on"] else False) if "Svolto" in df.columns else False
        df["Escludi_Conteggio"] = df["Escludi_Conteggio"].apply(lambda x: True if str(x).lower() in ["true", "1", "yes", "vero", "on"] else False) if "Escludi_Conteggio" in df.columns else False
        df["Calendar_ID"] = df["Calendar_ID"].fillna("").astype(str) if "Calendar_ID" in df.columns else ""
        df["Reminder_Minuti"] = pd.to_numeric(df["Reminder_Minuti"], errors="coerce").fillna(240).astype(int) if "Reminder_Minuti" in df.columns else 240
            
        if "Ore" not in df.columns or df["Ore"].isna().all():
            df["Ore"] = df.apply(lambda r: calcola_ore(r.get("Orario Inizio"), r.get("Orario Fine")), axis=1)
            
        for c in cols_standard:
            if c not in df.columns: df[c] = ""
        return df
    except Exception as e:
        return empty_df

def salva_dati(df_to_save):
    if "Data_dt" in df_to_save.columns: df_to_save = df_to_save.drop(columns=["Data_dt"])
    cols_standard = ["Data", "Mese", "Orario Inizio", "Orario Fine", "Ore", "Ente", "Classe", "Sede", "Modalità", "Svolto", "Escludi_Conteggio", "Note", "Appunto_Multiplo", "Codice_Univoco", "Calendar_ID", "Reminder_Minuti"]
    for c in cols_standard:
        if c not in df_to_save.columns: df_to_save[c] = ""
    df_to_save = df_to_save[cols_standard].fillna("")
    try:
        worksheet = get_gspread_client_and_sheet("Foglio1")
        if worksheet is None: return
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

# ================= TAB 1: INSERIMENTO =================
with tab1:
    st.subheader("Registrazione Nuova Attività")
    tipo_inserimento = st.radio("Seleziona modalità di inserimento:", options=["Inserimento Normale", "Inserimento Multiplo"], horizontal=True)

    with st.form("form_orario", clear_on_submit=True):
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            data_selezionata = st.date_input("Giorno", value=datetime.date.today(), format="DD/MM/YYYY")
            mese_str = traduci_mese(data_selezionata.strftime("%B"))
        with col_d2:
            st.info(f"Mese di riferimento: **{mese_str}**")

        st.markdown("**Selezione Orario**")
        col_o1, col_o2, col_o3, col_o4 = st.columns(4)
        with col_o1: ora_i = st.selectbox("Ora Inizio", options=list(range(0, 24)), index=9)
        with col_o2: min_i = st.selectbox("Minuti Inizio", options=list(range(0, 60)), index=0)
        with col_o3: ora_f = st.selectbox("Ora Fine", options=list(range(0, 24)), index=18)
        with col_o4: min_f = st.selectbox("Minuti Fine", options=list(range(0, 60)), index=0)

        orario_inizio_str = f"{ora_i:02d}:{min_i:02d}"
        orario_fine_str = f"{ora_f:02d}:{min_f:02d}"
        ore_calcolate = calcola_ore(orario_inizio_str, orario_fine_str)
        st.caption(f"Durata stimata: **{ore_calcolate} ore**")

        col_t0, col_t1, col_t2, col_t3 = st.columns(4)
        opts_enti, opts_classi, opts_sedi, opts_modalita = config.get("enti", []).copy(), config.get("classi", []).copy(), config.get("sedi", []).copy(), config.get("modalita", []).copy()

        with col_t0:
            ente = st.selectbox("Ente", options=opts_enti if opts_enti else [""], index=0, key="sel_ente")
            nuovo_ente_libero = st.text_input("O digita nuovo ente:", placeholder="Se non è in elenco...", key="lib_ente")
        with col_t1:
            classe = st.selectbox("Classe", options=opts_classi if opts_classi else [""], index=0, key="sel_classe")
            nuova_classe_libera = st.text_input("O digita nuova classe:", placeholder="Se non è in elenco...", key="lib_classe")
        with col_t2:
            sede = st.selectbox("Sede", options=opts_sedi if opts_sedi else [""], index=0, key="sel_sede")
            nuova_sede_libera = st.text_input("O digita nuova sede:", placeholder="Se non è in elenco...", key="lib_sede")
        with col_t3:
            modalita = st.selectbox("Modalità", options=opts_modalita if opts_modalita else [""], index=0, key="sel_mod")
            nuovo_mod_libero = st.text_input("O digita nuova modalità:", placeholder="Se non è in elenco...", key="lib_mod")

        st.selectbox("Avviso / Promemoria Calendar (Disabilitato)", options=["Funzione temporaneamente disabilitata"], index=0, disabled=True)
        minuti_scelti = 240

        svolto_iniziale = st.checkbox("Impegno già svolto", value=False)
        escludi_conteggio_iniziale = st.checkbox("Escludi dal conteggio ore", value=False)
        note = st.text_area("Note / Descrizione dettagliata", placeholder="Inserisci eventuali dettagli...")
        
        appunto_multiplo = ""
        if tipo_inserimento == "Inserimento Multiplo":
            st.markdown("---")
            st.markdown("### Sezione 8 Appuntamenti Multipli")
            st.caption("Compila le righe desiderate inserendo l'intervallo di orario e il testo associato.")
            
            righe_multiplo_lista = []
            for i in range(8):
                # Utilizziamo una struttura compatta a colonne (gruppo orari ridotto a sinistra, testo largo a destra)
                rc_orari, rc_testo = st.columns([1.6, 3.4])
                with rc_orari:
                    st.markdown('<div class="time-slot-group">', unsafe_allow_html=True)
                    sub_c1, sub_c2, sub_c3, sub_c4 = st.columns(4)
                    with sub_c1: m_ora_i = st.selectbox("OI", options=list(range(0, 24)), index=0, key=f"m_ora_i_{i}", label_visibility="collapsed")
                    with sub_c2: m_min_i = st.selectbox("MI", options=list(range(0, 60)), index=0, key=f"m_min_i_{i}", label_visibility="collapsed")
                    with sub_c3: m_ora_f = st.selectbox("OF", options=list(range(0, 24)), index=1, key=f"m_ora_f_{i}", label_visibility="collapsed")
                    with sub_c4: m_min_f = st.selectbox("MF", options=list(range(0, 60)), index=0, key=f"m_min_f_{i}", label_visibility="collapsed")
                    st.markdown('</div>', unsafe_allow_html=True)
                with rc_testo:
                    m_testo = st.text_input(f"Testo {i+1}", placeholder=f"Testo appuntamento {i+1}...", key=f"m_testo_{i}", label_visibility="collapsed")
                
                if m_testo.strip():
                    orario_slot_str = f"{m_ora_i:02d}:{m_min_i:02d}-{m_ora_f:02d}:{m_min_f:02d}"
                    righe_multiplo_lista.append(f"{orario_slot_str} {m_testo.strip()}")
            
            appunto_multiplo = "\n".join(righe_multiplo_lista)

        submit_button_label = "Salva Inserimento Multiplo" if tipo_inserimento == "Inserimento Multiplo" else "Salva Attività"
        submit_button = st.form_submit_button(label=submit_button_label, use_container_width=True)

        if submit_button:
            if orario_inizio_str >= orario_fine_str:
                st.error("L'orario di inizio non può essere successivo o uguale all'orario di fine.")
            else:
                val_ente = nuovo_ente_libero.strip() if nuovo_ente_libero else ente
                val_classe = nuova_classe_libera.strip() if nuova_classe_libera else classe
                val_sede = nuova_sede_libera.strip() if nuova_sede_libera else sede
                val_modalita = nuovo_mod_libero.strip() if nuovo_mod_libero else modalita

                if nuovo_ente_libero and nuovo_ente_libero not in config["enti"]: config["enti"].append(nuovo_ente_libero)
                if nuova_classe_libera and nuova_classe_libera not in config["classi"]: config["classi"].append(nuova_classe_libera)
                if nuova_sede_libera and nuova_sede_libera not in config["sedi"]: config["sedi"].append(nuova_sede_libera)
                if nuovo_mod_libero and nuovo_mod_libero not in config["modalita"]: config["modalita"].append(nuovo_mod_libero)
                salva_config(config)

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
    def gestisci_sezione_combo(titolo_sezione, chiave_config):
        st.markdown(f"### {titolo_sezione}")
        lista_corrente = config[chiave_config]
        col_sel, col_del = st.columns([3, 1])
        with col_sel:
            voce_selezionata = st.selectbox(f"Voci esistenti in {titolo_sezione}", options=["-- Seleziona per modificare/eliminare --"] + sorted(lista_corrente), key=f"sel_mod_{chiave_config}")
        
        with st.form(key=f"form_add_{chiave_config}", clear_on_submit=True):
            c_in1, c_in2 = st.columns([3, 1])
            with c_in1: nuova_voce = st.text_input(f"Aggiungi nuovo elemento a {titolo_sezione}", placeholder="Nuovo elemento...", label_visibility="collapsed")
            with c_in2: btn_aggiungi = st.form_submit_button("Aggiungi", use_container_width=True)
            
            if btn_aggiungi:
                nuova_pulita = nuova_voce.strip()
                if not nuova_pulita: st.warning("Il campo non può essere vuoto.")
                elif any(v.lower() == nuova_pulita.lower() for v in lista_corrente): st.error("Elemento già presente.")
                else:
                    lista_corrente.append(nuova_pulita)
                    salva_config(config)
                    st.success("Elemento aggiunto con successo!")
                    st.rerun()

        if voce_selezionata != "-- Seleziona per modificare/eliminare --":
            with st.form(key=f"form_edit_{chiave_config}"):
                c_ed1, c_ed2, c_ed3 = st.columns([3, 1, 1])
                with c_ed1: valore_modificato = st.text_input("Rinomina voce", value=voce_selezionata, label_visibility="collapsed")
                with c_ed2: btn_salva_mod = st.form_submit_button("Salva", use_container_width=True)
                with c_ed3: btn_elimina = st.form_submit_button("Elimina", use_container_width=True, type="primary")

                if btn_salva_mod:
                    valore_pulito = valore_modificato.strip()
                    if valore_pulito:
                        idx = lista_corrente.index(voce_selezionata)
                        lista_corrente[idx] = valore_pulito
                        salva_config(config)
                        st.success("Voce aggiornata!")
                        st.rerun()
                if btn_elimina:
                    lista_corrente.remove(voce_selezionata)
                    salva_config(config)
                    st.success("Voce eliminata!")
                    st.rerun()

    c1, c2, c3, c4 = st.columns(4, gap="medium")
    with c1: gestisci_sezione_combo("Enti", "enti")
    with c2: gestisci_sezione_combo("Classi", "classi")
    with c3: gestisci_sezione_combo("Sedi", "sedi")
    with c4: gestisci_sezione_combo("Modalità", "modalita")

# ================= TAB 3: ARCHIVIO, MODIFICA, REPORT & RIEPILOGO =================
with tab3:
    st.subheader("Storico, Modifica e Gestione Appuntamenti")
    if not df.empty:
        df_vis = df.copy()
        df_vis["ID_originale"] = df_vis.index
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
            if row.get("Svolto", False): return ['background-color: #2b2b2b; color: #7f7f7f; text-decoration: line-through'] * len(row)
            mod = str(row.get("Modalità", "")).lower()
            if "presenza" in mod: return ['background-color: #1c3d73; color: #ffffff'] * len(row)
            elif "video" in mod: return ['background-color: #155c32; color: #ffffff'] * len(row)
            return [''] * len(row)

        df_editato = st.data_editor(df_mostra.style.apply(colora_righe_tabella, axis=1), use_container_width=True, hide_index=True)

        modificato = False
        for _, riga_ed in df_editato.iterrows():
            idx_orig = int(riga_ed["ID"])
            if df.loc[idx_orig, "Svolto"] != bool(riga_ed["Svolto"]) or df.loc[idx_orig, "Escludi_Conteggio"] != bool(riga_ed["Escludi_Conteggio"]):
                df.loc[idx_orig, "Svolto"] = bool(riga_ed["Svolto"])
                df.loc[idx_orig, "Escludi_Conteggio"] = bool(riga_ed["Escludi_Conteggio"])
                modificato = True
        if modificato:
            salva_dati(df)
            st.rerun()

        righe_selezionate = df_editato[df_editato["Seleziona"] == True]["ID"].tolist()
        c_act1, c_act2 = st.columns(2)
        with c_act1:
            if st.button("Elimina Selezionati", type="primary", use_container_width=True):
                if righe_selezionate:
                    for r_idx in righe_selezionate:
                        cal_id = str(df.loc[r_idx, "Calendar_ID"])
                        if cal_id and cal_id.lower() not in ["nan", "none", ""]:
                            sincronizza_google_calendar("elimina", {}, cal_id)
                    df = df.drop(righe_selezionate).reset_index(drop=True)
                    salva_dati(df)
                    st.success("Eliminati con successo!")
                    st.rerun()
        with c_act2:
            if st.button("Duplica Selezionato", use_container_width=True):
                if len(righe_selezionate) == 1:
                    riga_idx = righe_selezionate[0]
                    nuova_riga = df.loc[riga_idx].copy()
                    nuova_riga["Note"] = str(nuova_riga.get("Note", "")) + " (Copia)"
                    cal_id = sincronizza_google_calendar("crea", nuova_riga.to_dict())
                    nuova_riga["Calendar_ID"] = str(cal_id) if cal_id else ""
                    df = pd.concat([df, pd.DataFrame([nuova_riga])], ignore_index=True)
                    salva_dati(df)
                    st.success("Duplicato!")
                    st.rerun()

        st.markdown("---")
        st.subheader("Generazione Report & Filtri Avanzati")
        c_t1, c_t2, c_t3 = st.columns(3)
        with c_t1: ricerca_libera = st.text_input("Ricerca libera", placeholder="Parole chiave...")
        with c_t2: data_inizio_filtro = st.date_input("Data Inizio", value=None, format="DD/MM/YYYY")
        with c_t3: data_fine_filtro = st.date_input("Data Fine", value=None, format="DD/MM/YYYY")

        df_report = df.copy()
        if "Data_dt" not in df_report.columns: df_report["Data_dt"] = df_report["Data"].apply(parse_data_italiana)
        if data_inizio_filtro: df_report = df_report[df_report["Data_dt"] >= pd.to_datetime(data_inizio_filtro)]
        if data_fine_filtro: df_report = df_report[df_report["Data_dt"] <= pd.to_datetime(data_fine_filtro)]
        
        ore_totali = df_report[df_report["Escludi_Conteggio"] != True]["Ore"].sum()
        st.success(f"**Totale Ore Report:** **{ore_totali:.2f} ore**")

        c_exp1, c_exp2, c_exp3 = st.columns(3)
        with c_exp1:
            st.download_button("Scarica CSV", data=df_report.to_csv(index=False).encode('utf-8'), file_name="report.csv", mime="text/csv", use_container_width=True)
        with c_exp2:
            pdf_data = genera_pdf_report(df_report)
            if pdf_data:
                st.download_button("Scarica PDF", data=pdf_data, file_name="report.pdf", mime="application/pdf", use_container_width=True)
        with c_exp3:
            if st.button("Sincronizza eventi mancanti", use_container_width=True):
                for idx, row in df.iterrows():
                    cal_id = str(row.get("Calendar_ID", ""))
                    if not cal_id or cal_id.lower() in ["nan", "none", ""]:
                        nuovo_id = sincronizza_google_calendar("crea", row.to_dict())
                        if nuovo_id: df.loc[idx, "Calendar_ID"] = str(nuovo_id)
                salva_dati(df)
                st.success("Sincronizzazione completata!")
                st.rerun()

# ================= TAB 4: CALENDARIO =================
with tab4:
    st.subheader("Vista Calendario Mensile")
    if "cal_anno" not in st.session_state: st.session_state["cal_anno"] = datetime.date.today().year
    if "cal_mese" not in st.session_state: st.session_state["cal_mese"] = datetime.date.today().month

    col_nav1, col_nav2, col_nav3, col_nav4, col_nav5 = st.columns([1, 1, 2, 1, 1])
    with col_nav1:
        if st.button("<< Anno -", use_container_width=True): st.session_state["cal_anno"] -= 1; st.rerun()
    with col_nav2:
        if st.button("< Mese -", use_container_width=True):
            if st.session_state["cal_mese"] == 1: st.session_state["cal_mese"] = 12; st.session_state["cal_anno"] -= 1
            else: st.session_state["cal_mese"] -= 1
            st.rerun()
    with col_nav3:
        st.markdown(f"<h3 style='text-align: center; margin: 0;'>{traduci_mese(datetime.date(st.session_state['cal_anno'], st.session_state['cal_mese'], 1).strftime('%B')).capitalize()} {st.session_state['cal_anno']}</h3>", unsafe_allow_html=True)
    with col_nav4:
        if st.button("Mese + >", use_container_width=True):
            if st.session_state["cal_mese"] == 12: st.session_state["cal_mese"] = 1; st.session_state["cal_anno"] += 1
            else: st.session_state["cal_mese"] += 1
            st.rerun()
    with col_nav5:
        if st.button("Anno + >>", use_container_width=True): st.session_state["cal_anno"] += 1; st.rerun()

    st.markdown("---")
    df_cal = df.copy()
    if not df_cal.empty:
        df_cal["Data_dt"] = df_cal["Data"].apply(parse_data_italiana)
        df_mese = df_cal[(df_cal["Data_dt"].notna()) & (df_cal["Data_dt"].dt.year == st.session_state["cal_anno"]) & (df_cal["Data_dt"].dt.month == st.session_state["cal_mese"])]
    else:
        df_mese = pd.DataFrame()

    import calendar
    cal = calendar.Calendar(firstweekday=0)
    giorni_mese = cal.monthdayscalendar(st.session_state["cal_anno"], st.session_state["cal_mese"])
    giorni_settimana = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
    
    impegni_per_giorno = {}
    if not df_mese.empty:
        for _, row in df_mese.iterrows():
            giorno_num = row["Data_dt"].day
            if giorno_num not in impegni_per_giorno: impegni_per_giorno[giorno_num] = []
            impegni_per_giorno[giorno_num].append({
                "ente": str(row.get("Ente", "")), "classe": str(row.get("Classe", "")),
                "orario": f"{str(row.get('Orario Inizio', ''))} - {str(row.get('Orario Fine', ''))}",
                "ore": row.get("Ore", 0.0), "sede": str(row.get("Sede", "")), "modalita": str(row.get("Modalità", ""))
            })

    html_righe = ""
    for settimana in giorni_mese:
        html_righe += "<tr>"
        for giorno in settimana:
            if giorno == 0: html_righe += '<td style="background-color: #121212; height: 90px;"></td>'
            else:
                ha_impegni = giorno in impegni_per_giorno
                bg = "background-color: #183025;" if ha_impegni else "background-color: #1e1e1e;"
                html_righe += f'<td style="{bg} height: 90px; vertical-align: top; padding: 6px; border: 1px solid #444;"><div style="font-weight: bold; color: #fff;">{giorno}</div>'
                if ha_impegni:
                    html_righe += f'<div style="background-color: #2fa866; color: white; font-size: 11px; padding: 2px 4px; border-radius: 4px; margin-top: 4px;">{len(impegni_per_giorno[giorno])} Impegno/i</div>'
                html_righe += '</td>'
        html_righe += "</tr>"

    th_html = "".join([f'<th style="background-color: #1c3d73; color: white; text-align: center; padding: 8px;">{gs}</th>' for gs in giorni_settimana])
    st.markdown(f'<table style="width: 100%; border-collapse: collapse;"><tr>{th_html}</tr>{html_righe}</table>', unsafe_allow_html=True)
