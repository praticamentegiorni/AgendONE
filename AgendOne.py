import calendar
from datetime import datetime
import pandas as pd
import html
import streamlit as st  # Se utilizzato in ambiente Streamlit

def genera_calendario_html(df_impegni: pd.DataFrame, anno: int, mese: int) -> str:
    """
    Genera la struttura HTML della tabella calendario mensile con badge e tooltip.
    Gestisce correttamente i giorni vuoti a inizio e fine mese.
    """
    # Copia di sicurezza e conversione della colonna data in datetime.date
    df = df_impegni.copy() if df_impegni is not None else pd.DataFrame()
    if not df.empty and 'data' in df.columns:
        df['data'] = pd.to_datetime(df['data']).dt.date

    # Intestazioni dei giorni della settimana
    giorni_settimana = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
    
    html_out = ['<table class="cal-table">']
    html_out.append('  <thead>')
    html_out.append('    <tr>' + ''.join([f'<th class="cal-th">{g}</th>' for g in giorni_settimana]) + '</tr>')
    html_out.append('  </thead>')
    html_out.append('  <tbody>')
    
    # Matrice del mese: lista di settimane, dove 0 indica giorno fuori mese
    matrice_mese = calendar.monthcalendar(anno, mese)
    
    for settimana in matrice_mese:
        html_out.append('    <tr>')
        for giorno in settimana:
            # 1. Gestione celle vuote (inizio o fine mese)
            if giorno == 0:
                html_out.append('<td class="cal-cell-empty"></td>')
                continue
            
            # Data corrente sicura
            data_corrente = datetime(anno, mese, giorno).date()
            
            # 2. Filtra gli impegni del giorno
            if not df.empty:
                impegni_giorno = df[df['data'] == data_corrente]
            else:
                impegni_giorno = pd.DataFrame()
            
            # 3. Renderizzazione cella senza impegni
            if impegni_giorno.empty:
                cell_html = f'<td class="cal-cell" style="background-color: #1e1e1e;"><div class="day-number">{giorno}</div></td>'
            else:
                # 4. Renderizzazione cella con impegni
                num_impegni = len(impegni_giorno)
                data_str = f"{giorno}/{mese}/{anno}"
                
                # Generazione Badge
                if num_impegni == 1:
                    ev = impegni_giorno.iloc[0]
                    ora_i = html.escape(str(ev.get('ora_inizio', '')))
                    ora_f = html.escape(str(ev.get('ora_fine', '')))
                    classe = html.escape(str(ev.get('classe', '')))
                    badge_html = f'<span class="badge-impegno">{ora_i} - {ora_f} - {classe}</span>'
                else:
                    badge_html = f'<span class="badge-impegno-multi">{num_impegni} Appuntamenti</span>'
                
                # Generazione contenuto Tooltip
                dettagli_impegni = []
                for _, ev in impegni_giorno.iterrows():
                    ora_i = html.escape(str(ev.get('ora_inizio', '')))
                    ora_f = html.escape(str(ev.get('ora_fine', '')))
                    durata = float(ev.get('durata', 0.0))
                    ente = html.escape(str(ev.get('ente', '')))
                    classe = html.escape(str(ev.get('classe', '')))
                    sede = html.escape(str(ev.get('sede', '')))
                    modalita = html.escape(str(ev.get('modalita', 'Presenza')))
                    note = str(ev.get('note', '')).strip() if pd.notna(ev.get('note', '')) else ''
                    
                    item = f"<div style='margin-bottom: 6px; '><b>{ora_i} - {ora_f}</b> ({durata:.1f}h)<br>"
                    item += f"<b>Ente:</b> {ente} | <b>Classe:</b> {classe}<br>"
                    item += f"<b>Sede:</b> {sede} ({modalita})"
                    if note:
                        item += f"<br><em>Note:</em> {html.escape(note)}"
                    item += "</div>"
                    dettagli_impegni.append(item)
                
                tooltip_body = ''.join(dettagli_impegni)
                
                cell_html = (
                    f'<td class="cal-cell" style="background-color: #183025; border: 1px solid #2fa866;">'
                    f'<div class="day-number">{giorno}</div>'
                    f'<div class="tooltip-container">'
                    f'{badge_html}'
                    f'<div class="tooltip-content">'
                    f'<b>Impegni del {data_str}</b>'
                    f"<hr style='margin: 4px 0; border-color: #444;'>"
                    f'{tooltip_body}'
                    f'</div></div></td>'
                )
            
            html_out.append(cell_html)
        html_out.append('    </tr>')
        
    html_out.append('  </tbody>')
    html_out.append('</table>')
    
    return '\n'.join(html_out)
