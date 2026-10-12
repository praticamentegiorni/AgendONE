import calendar
import datetime
import html
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components


def genera_calendario_html_completo(
    df_impegni: pd.DataFrame, anno: int, mese: int
) -> str:
    """Genera una pagina HTML/CSS pulita ed isolata per la griglia del calendario.

    Gestisce in modo sicuro le date italiane (DD/MM/YYYY) ed i giorni vuoti di
    inizio/fine mese.
    """
    # 1. Copia e pulizia sicura del DataFrame
    if df_impegni is None or not isinstance(df_impegni, pd.DataFrame):
        df = pd.DataFrame()
    else:
        df = df_impegni.copy()

    if not df.empty and 'data' in df.columns:
        # dayfirst=True garantisce la conversione corretta per date tipo 01/10/2026
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

    # 2. CSS isolato
    css_style = """
    <style>
    body {
        margin: 0;
        padding: 5px;
        background-color: #0e1117;
        color: #e0e0e0;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    .cal-table {
        width: 100%;
        border-collapse: collapse;
        background-color: #121212;
        table-layout: fixed;
    }
    .cal-th {
        background-color: #1e1e1e;
        color: #ffffff;
        padding: 10px 4px;
        border: 1px solid #333333;
        text-align: center;
        font-size: 0.85em;
        font-weight: bold;
    }
    .cal-cell {
        height: 100px;
        vertical-align: top;
        padding: 6px;
        border: 1px solid #2a2a2a;
        position: relative;
        background-color: #141414;
    }
    .cal-cell-empty {
        height: 100px;
        background-color: #0d0d0d;
        border: 1px solid #1a1a1a;
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
        width: 250px;
        background-color: #1e1e1e;
        color: #f0f0f0;
        border: 1px solid #444444;
        border-radius: 6px;
        padding: 10px;
        position: absolute;
        z-index: 9999;
        bottom: 110%;
        left: 50%;
        transform: translateX(-50%);
        box-shadow: 0 4px 14px rgba(0,0,0,0.8);
        font-size: 0.8em;
        line-height: 1.4;
    }
    .tooltip-container:hover .tooltip-content {
        display: block;
    }
    </style>
    """

    # 3. Costruzione struttura HTML
    html_out = [
        '<!DOCTYPE html><html><head><meta charset="utf-8">',
        css_style,
        '</head><body>',
    ]
    html_out.append('<table class="cal-table"><thead><tr>')

    for g in giorni_settimana:
        html_out.append(f'<th class="cal-th">{g}</th>')
    html_out.append('</tr></thead><tbody>')

    # Genera matrice del mese (settimane)
    matrice = calendar.monthcalendar(anno, mese)

    for settimana in matrice:
        html_out.append('<tr>')
        for giorno in settimana:
            # Celle vuote prima del 1° del mese e dopo l'ultimo giorno del mese
            if giorno == 0:
                html_out.append('<td class="cal-cell-empty"></td>')
                continue

            data_curr = datetime.date(anno, mese, giorno)

            if not df.empty:
                sub_df = df[df['data_dt'] == data_curr]
            else:
                sub_df = pd.DataFrame()

            if sub_df.empty:
                html_out.append(
                    f'<td class="cal-cell"><div'
                    f' class="day-number">{giorno}</div></td>'
                )
            else:
                n_ev = len(sub_df)
                data_str = f'{giorno}/{mese}/{anno}'

                # Render del Badge
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

                # Contenuto del Tooltip
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
                    f' border-color:#444;">{tt_body}</div></div></td>'
                )
                html_out.append(cell)
        html_out.append('</tr>')

    html_out.append('</tbody></table></body></html>')
    return ''.join(html_out)


# --- ESEMPIO DI UTILIZZO E RENDERING IN STREAMLIT ---
st.set_page_config(layout='wide', page_title='Calendario Impegni')

st.title('Calendario Impegni - Ottobre 2026')

# Dati di test
dati_test = [
    {
        'data': '01/10/2026',
        'ora_inizio': '14:30',
        'ora_fine': '18:30',
        'durata': 4.0,
        'ente': 'Scuola Radio Elettra',
        'classe': '25032_14 Impianti elettrici civili',
        'sede': 'Ex Seminario',
        'modalita': 'Presenza',
        'note': 'con Landi',
    },
    {
        'data': '01/10/2026',
        'ora_inizio': '08:30',
        'ora_fine': '13:00',
        'durata': 4.5,
        'ente': 'Scuola Bufalini',
        'classe': 'AULA',
        'sede': 'Via San Bartolomeo',
        'modalita': 'Presenza',
        'note': None,
    },
    {
        'data': '02/10/2026',
        'ora_inizio': '09:00',
        'ora_fine': '18:00',
        'durata': 9.0,
        'ente': 'Scuola Radio Elettra',
        'classe': '25032_12 Impianti elettrici civili',
        'sede': 'Ex Seminario',
        'modalita': 'Presenza',
        'note': None,
    },
]

df_impegni = pd.DataFrame(dati_test)

# Genera il codice HTML completo
html_calendario = genera_calendario_html_completo(df_impegni, anno=2026, mese=10)

# Rendering sicuro dentro iframe
components.html(html_calendario, height=650, scrolling=True)
