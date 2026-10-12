import calendar
import datetime
import html
import pandas as pd
import streamlit as st


def genera_calendario_html(df_impegni, anno: int, mese: int) -> str:
    """Genera la tabella HTML del calendario mensile per Streamlit.

    Gestisce in modo sicuro le date italiane (DD/MM/YYYY), i giorni vuoti e i
    valori mancanti (NaN/None).
    """
    # 1. Copia e parsing sicuro del DataFrame
    if df_impegni is None or not isinstance(df_impegni, pd.DataFrame):
        df = pd.DataFrame()
    else:
        df = df_impegni.copy()

    if not df.empty and 'data' in df.columns:
        # dayfirst=True evita l'errore tra Mesi/Giorni (es. 01/10/2026)
        df['data_dt'] = pd.to_datetime(
            df['data'], dayfirst=True, errors='coerce'
        ).dt.date
    else:
        df['data_dt'] = pd.Series(dtype='object')

    giorni_settimana = [
        'Lunedì',
        'Martedì',
        'Mercoledì',
        'Giovedì',
        'Venerdì',
        'Sabato',
        'Domenica',
    ]

    # 2. CSS isolato (Stringa normale SENZA f-string per non mandare in errore le graffe {})
    css_style = """
    <style>
    .cal-table {
        width: 100%;
        border-collapse: collapse;
        background-color: #121212;
        color: #e0e0e0;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        margin-bottom: 20px;
    }
    .cal-th {
        background-color: #1e1e1e;
        color: #ffffff;
        padding: 10px;
        border: 1px solid #333333;
        text-align: center;
        font-size: 0.9em;
    }
    .cal-cell {
        height: 95px;
        width: 14.28%;
        vertical-align: top;
        padding: 6px;
        border: 1px solid #2a2a2a;
        position: relative;
    }
    .cal-cell-empty {
        background-color: #0d0d0d;
        border: 1px solid #1f1f1f;
        width: 14.28%;
    }
    .day-number {
        font-weight: bold;
        font-size: 0.85em;
        color: #888888;
        margin-bottom: 4px;
    }
    .badge-impegno {
        display: block;
        font-size: 0.72em;
        padding: 3px 5px;
        border-radius: 4px;
        background-color: #1e4d35;
        color: #a3e635;
        border: 1px solid #2fa866;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        margin-top: 2px;
    }
    .badge-impegno-multi {
        display: block;
        font-size: 0.72em;
        padding: 3px 5px;
        border-radius: 4px;
        background-color: #183025;
        color: #2fa866;
        border: 1px solid #2fa866;
        font-weight: bold;
        text-align: center;
        margin-top: 2px;
    }
    .tooltip-container {
        position: relative;
        display: block;
        cursor: pointer;
    }
    .tooltip-container .tooltip-content {
        display: none;
        width: 260px;
        background-color: #1e1e1e;
        color: #f0f0f0;
        border: 1px solid #444444;
        border-radius: 6px;
        padding: 10px;
        position: absolute;
        z-index: 999;
        bottom: 110%;
        left: 50%;
        transform: translateX(-50%);
        box-shadow: 0 4px 12px rgba(0,0,0,0.6);
        font-size: 0.8em;
        line-height: 1.4;
    }
    .tooltip-container:hover .tooltip-content {
        display: block;
    }
    </style>
    """

    # 3. Costruzione HTML
    html_lines = [css_style, '<table class="cal-table"><thead><tr>']
    for g in giorni_settimana:
        html_lines.append(f'<th class="cal-th">{g}</th>')
    html_lines.append('</tr></thead><tbody>')

    matrice = calendar.monthcalendar(anno, mese)

    for settimana in matrice:
        html_lines.append('<tr>')
        for giorno in settimana:
            # Gestione sicura inizio e fine mese (giorno == 0)
            if giorno == 0:
                html_lines.append('<td class="cal-cell-empty"></td>')
                continue

            data_curr = datetime.date(anno, mese, giorno)

            if not df.empty:
                sub_df = df[df['data_dt'] == data_curr]
            else:
                sub_df = pd.DataFrame()

            if sub_df.empty:
                html_lines.append(
                    f'<td class="cal-cell" style="background-color:'
                    f' #141414;"><div class="day-number">{giorno}</div></td>'
                )
            else:
                n_ev = len(sub_df)
                data_str = f'{giorno}/{mese}/{anno}'

                # Badge
                if n_ev == 1:
                    row = sub_df.iloc[0]
                    oi = html.escape(
                        str(row.get('ora_inizio', ''))
                        if pd.notna(row.get('ora_inizio'))
                        else ''
                    )
                    of = html.escape(
                        str(row.get('ora_fine', ''))
                        if pd.notna(row.get('ora_fine'))
                        else ''
                    )
                    cl = html.escape(
                        str(row.get('classe', ''))
                        if pd.notna(row.get('classe'))
                        else ''
                    )
                    badge = f'<span class="badge-impegno">{oi} - {of} - {cl}</span>'
                else:
                    badge = f'<span class="badge-impegno-multi">{n_ev} Appuntamenti</span>'

                # Contenuto Tooltip
                items = []
                for _, row in sub_df.iterrows():
                    oi = html.escape(
                        str(row.get('ora_inizio', ''))
                        if pd.notna(row.get('ora_inizio'))
                        else ''
                    )
                    of = html.escape(
                        str(row.get('ora_fine', ''))
                        if pd.notna(row.get('ora_fine'))
                        else ''
                    )
                    dur = row.get('durata', 0)
                    dur_str = f'{float(dur):.1f}h' if pd.notna(dur) else ''
                    ente = html.escape(
                        str(row.get('ente', ''))
                        if pd.notna(row.get('ente'))
                        else ''
                    )
                    cl = html.escape(
                        str(row.get('classe', ''))
                        if pd.notna(row.get('classe'))
                        else ''
                    )
                    sede = html.escape(
                        str(row.get('sede', ''))
                        if pd.notna(row.get('sede'))
                        else ''
                    )
                    mod = html.escape(
                        str(row.get('modalita', 'Presenza'))
                        if pd.notna(row.get('modalita'))
                        else 'Presenza'
                    )

                    note_raw = row.get('note', '')
                    note = (
                        html.escape(str(note_raw).strip())
                        if pd.notna(note_raw) and str(note_raw).strip() != 'nan'
                        else ''
                    )

                    item_str = (
                        f"<div style='margin-bottom: 8px;'><b>{oi} - {of}</b>"
                        f' ({dur_str})<br><b>Ente:</b> {ente} | <b>Classe:</b>'
                        f' {cl}<br><b>Sede:</b> {sede} ({mod})'
                    )
                    if note:
                        item_str += f'<br><em>Note:</em> {note}'
                    item_str += '</div>'
                    items.append(item_str)

                tt_body = ''.join(items)

                cell = (
                    f'<td class="cal-cell" style="background-color: #183025;'
                    f' border: 1px solid #2fa866;"><div class="day-number"'
                    f' style="color: #ffffff;">{giorno}</div><div'
                    f' class="tooltip-container">{badge}<div'
                    f' class="tooltip-content"><b>Impegni del'
                    ' {data_str}</b><hr style="margin:4px 0;'
                    f' border-color:#444;">{tt_body}</div></div>td>'
                )
                html_lines.append(cell)
        html_lines.append('</tr>')

    html_lines.append('</tbody></table>')
    return ''.join(html_lines)
