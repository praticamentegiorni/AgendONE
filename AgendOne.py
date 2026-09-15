import datetime
import io
import json
import os
import pandas as pd
import streamlit as st
import RegistOne  # Sotto-procedura esterna per la gestione dei registri di classe

# Impostazione pagina
st.set_page_config(page_title="AgendOne", layout="wide")

# CSS PERSONALIZZATO E OTTIMIZZAZIONE RESPONSIVE PER SMARTPHONE
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

    /* Ridimensionamento colonne data-editor (Orario, Selezione, Svolto, Escludi_Conteggio) */
    div[data-testid="stDataEditor"] th div[title*="Orario"],
    div[data-testid="stDataEditor"] th div[title*="Selezione"],
    div[data-testid="stDataEditor"] th div[title*="Svolto"],
    div[data-testid="stDataEditor"] th div[title*="Escludi"] {
        white-space: pre-wrap !important;
        font-size: 11px !important;
        line-height: 1.1 !important;
    }

    /* ========================================================== */
    /* OTTIMIZZAZIONI SPECIFICHE PER SMARTPHONE (Schermi stretti) */
    /* ========================================================== */
    @media screen and (max-width: 768px) {
        .stColumns {
            flex-direction: column !important;
        }
        div[data-testid="column"] {
            width: 100% !important;
            flex: 1 1 100% !important;
            min-width: 100% !important;
            margin-bottom: 8px !important;
        }
        
        .block-container {
            padding-left: 0.8rem !important;
            padding-right: 0.8rem !important;
            padding-top: 1rem !important;
        }

        button[data-baseweb="tab"] {
            font-size: 14px !important;
            padding: 8px 12px !important;
            margin-right: 4px !important;
        }

        .cal-cell {
            height: 75px !important;
            padding: 3px !important;
        }
        .day-number {
            font-size: 11px !important;
        }
        .badge-impegno, .badge-impegno-multi {
            font-size: 9px !important;
            padding: 1px 3px !important;
        }
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

# Parser per date in formato italiano DD/MM/YYYY o ISO YYYY-MM-DD
def parse_data_italiana(val):
    if pd.isna(val) or str(val).strip() == "" or str(val).lower() == "none" or str(val).lower() == "nan":
        return pd.NaT
    val_str = str(val).strip()
    
    if "-" in val_str and len(val_str.split("-")[0]) == 4:
        try:
            dt = pd.to_datetime(val_str, format="%Y-%m-%d", errors="coerce")
            if pd.notnull(dt):
                return dt
        except:
            pass
            
    try:
        parti = val_str.split("/")
        if len(parti) == 3:
            giorno, mese, anno = int(parti[0]), int(parti[1]), int(parti[2])
            return pd.Timestamp(datetime.datetime(anno, mese, giorno))
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

# Funzione per generare il Report PDF raggruppato per Ente e Classe o in Ordine Cronologico
def genera_pdf_report(df_report, ordina_cronologico=False):
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

        if ordina_cronologico:
            elements.append(Paragraph("Elenco Dettagliato Attività in Ordine Cronologico (Orario di Lavoro)", subtitle_style))
            elements.append(Spacer(1, 4))
            
            if not df_report.empty:
                col_widths = [60, 75, 100, 120, 75, 220, 52]
                det_data = [[
                    Paragraph("Data", th_style),
                    Paragraph("Orario", th_style),
                    Paragraph("Ente", th_style),
                    Paragraph("Classe / Committente", th_style),
                    Paragraph("Sede", th_style),
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
                
                df_sorted = df_report.copy()
                if "Data_dt" not in df_sorted.columns:
                    df_sorted["Data_dt"] = df_sorted["Data"].apply(parse_data_italiana)
                df_sorted = df_sorted.sort_values(by=["Data_dt", "Orario Inizio"], ascending=[True, True])
                
                row_idx = 1
                for _, row in df_sorted.iterrows():
                    parsed_dt = parse_data_italiana(row.get("Data", ""))
                    data_str = parsed_dt.strftime("%d/%m/%Y") if pd.notnull(parsed_dt) else str(row.get("Data", ""))
                    is_esclusa = bool(row.get("Escludi_Conteggio", False))
                    ore_val = float(row.get("Ore", 0.0))
                    
                    if not is_esclusa:
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
                        Paragraph(str(row.get("Ente", "")), cur_td_style),
                        Paragraph(str(row.get("Classe", "")), cur_td_style),
                        Paragraph(str(row.get("Sede", "")), cur_td_style),
                        Paragraph(note_str, cur_td_style),
                        Paragraph(ore_str, cur_td_style)
                    ])
                    row_idx += 1
                
                t_det = Table(det_data, colWidths=col_widths)
                t_det.setStyle(TableStyle(table_styles))
                elements.append(t_det)
                elements.append(Spacer(1, 8))
        else:
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
                    
                    for classe_nome in sorted(classi_dict.keys()):
                        lista_attivita = sorted(
                            classi_dict[classe_nome],
                            key=lambda r: (
                                parse_data_italiana(r.get("Data", "")) if pd.notnull(parse_data_italiana(r.get("Data", ""))) else pd.Timestamp.min,
                                str(r.get("Orario Inizio", ""))
                            )
                        )
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
        
        body = {
            'summary': dati_evento.get('summary'),
            'description': dati_evento.get('description'),
            'location': dati_evento.get('location'),
            'start': {'dateTime': dati_evento.get('start_datetime')},
            'end': {'dateTime': dati_evento.get('end_datetime')},
        }
        
        if azione == "crea":
            event = service.events().insert(calendarId=calendar_id, body=body).execute()
            return event.get('id')
        elif azione == "aggiorna" and evento_id_esistente:
            event = service.events().update(calendarId=calendar_id, eventId=evento_id_esistente, body=body).execute()
            return event.get('id')
        elif azione == "elimina" and evento_id_esistente:
            service.events().delete(calendarId=calendar_id, eventId=evento_id_esistente).execute()
            return True
    except Exception as e:
        print(f"Errore sincronizzazione Google Calendar: {e}")
    return None

# ==========================================
# CORPO PRINCIPALE DELL'APPLICAZIONE
# ==========================================
def main():
    # MENU PRINCIPALE A TAB (Aggiunto il Tab per i Registri di classe che richiama RegistOne)
    tab_appuntamenti, tab_registri = st.tabs(["Agenda & Appuntamenti", "Registri di classe"])
    
    with tab_appuntamenti:
        st.title("AgendOne - Gestione Appuntamenti e Attività")
        
        # Recupero dei dati da Google Sheets (Foglio1)
        worksheet = get_gspread_client_and_sheet("Foglio1")
        if worksheet:
            try:
                data = worksheet.get_all_records()
                df = pd.DataFrame(data)
            except Exception as e:
                st.error(f"Errore nel recupero dei record: {e}")
                df = pd.DataFrame()
        else:
            df = pd.DataFrame()

        # Inserimento della visualizzazione o dei filtri presenti nell'app originaria
        if not df.empty:
            st.write("Elenco appuntamenti e gestione:")
            
            # Gestione colonne data se presenti
            if "Data" in df.columns:
                df["Data_dt"] = df["Data"].apply(parse_data_italiana)
            
            # Filtro rapido o visualizzazione dataframe principale
            st.dataframe(df, use_container_width=True)
            
            # Sezione per statistiche rapide o calcolo ore se le colonne esistono
            if "Ore" in df.columns:
                totale_ore = df["Ore"].sum()
                st.metric("Totale Ore Registrate", f"{totale_ore:.2f} h")
        else:
            st.info("Nessun appuntamento trovato nel foglio Google (Foglio1).")

    with tab_registri:
        # Chiamata alla sotto-procedura esterna per la gestione del registro di classe
        RegistOne.render_registri()

if __name__ == "__main__":
    main()
