import calendar
from datetime import datetime
import pandas as pd
import streamlit as st

# Supponiamo che tu abbia un DataFrame 'df_impegni' con le colonne:
# ['Data', 'Titolo', 'Ore', 'Escluso_Conteggio']
# Gestione dello stato per la navigazione del calendario (Mese e Anno)
if "cal_anno" not in st.session_state:
  st.session_state.cal_anno = datetime.now().year
if "cal_mese" not in st.session_state:
  st.session_state.cal_mese = datetime.now().month

# Funzioni di navigazione
col_prec, col_testo, col_succ = st.columns([1, 2, 1])
if col_prec.button("◀ Mese Precedente"):
  if st.session_state.cal_mese == 1:
    st.session_state.cal_mese = 12
    st.session_state.cal_anno -= 1
  else:
    st.session_state.cal_mese -= 1
  st.rerun()

if col_succ.button("Mese Successivo ▶"):
  if st.session_state.cal_mese == 12:
    st.session_state.cal_mese = 1
    st.session_state.cal_anno += 1
  else:
    st.session_state.cal_mese += 1
  st.rerun()

# Nomi dei mesi in italiano
nomi_mesi = [
    "",
    "Gennaio",
    "Febbraio",
    "Marzo",
    "Aprile",
    "Maggio",
    "Giugno",
    "Luglio",
    "Agosto",
    "Settembre",
    "Ottobre",
    "Novembre",
    "Dicembre",
]
col_testo.markdown(
    f"<h3 style='text-align: center;'>{nomi_mesi[st.session_state.cal_mese]}"
    f" {st.session_state.cal_anno}</h3>",
    unsafe_allow_html=True,
)

# Filtro impegni per il mese e anno selezionati (sostituisci df_impegni con il tuo DataFrame reale)
# Esempio di struttura dati fittizia se non ancora caricata:
if "df_impegni" not in st.session_state:
  st.session_state.df_impegni = pd.DataFrame(
      columns=["Data", "Titolo", "Ore", "Escluso_Conteggio"]
  )

df = st.session_state.df_impegni
# Converti la colonna data in datetime se non lo è già
if not df.empty:
  df["Data_dt"] = pd.to_datetime(df["Data"], errors="coerce")
  df_mese = df[
      (df["Data_dt"].dt.year == st.session_state.cal_anno)
      & (df["Data_dt"].dt.month == st.session_state.cal_mese)
  ]
else:
  df_mese = pd.DataFrame(
      columns=["Data", "Titolo", "Ore", "Escluso_Conteggio", "Data_dt"]
  )

# Calcoli per la barra delle informazioni mensili
df_validi_conteggio = (
    df_mese[df_mese["Escluso_Conteggio"] != True]
    if not df_mese.empty
    else df_mese
)
num_appuntamenti = len(df_validi_conteggio)
ore_appuntamenti = (
    df_validi_conteggio["Ore"].sum() if not df_validi_conteggio.empty else 0
)

# Mostra metriche mensili
m1, m2 = st.columns(2)
m1.metric("Numero Appuntamenti Mensili", num_appuntamenti)
m2.metric("Ore Appuntamenti Mensili", f"{ore_appuntamenti:.1f} h")

st.markdown("---")

# Generazione della griglia del calendario
cal = calendar.Calendar(firstweekday=0)  # Lunedì come primo giorno
giorni_mese = cal.monthdayscalendar(
    st.session_state.cal_anno, st.session_state.cal_mese
)

# Intestazione giorni della settimana
giorni_settimana = ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"]
header_cols = st.columns(7)
for idx, g in enumerate(giorni_settimana):
  header_cols[idx].markdown(
      f"<div style='text-align: center; font-weight: bold;'>{g}</div>",
      unsafe_allow_html=True,
  )

# Mostra i giorni a griglia con HTML/CSS e supporto per il tooltip (hover)
for settimana in giorni_mese:
  cols = st.columns(7)
  for idx, giorno in enumerate(settimana):
    with cols[idx]:
      if giorno == 0:
        st.markdown(
            "<div style='height: 70px; background-color: transparent;'></div>",
            unsafe_allow_html=True,
        )
      else:
        # Cerca impegni per questo giorno specifico
        data_corrente = pd.Timestamp(
            st.session_state.cal_anno, st.session_state.cal_mese, giorno
        )
        impegni_giorno = (
            df_mese[df_mese["Data_dt"].dt.date == data_corrente.date()]
            if not df_mese.empty
            else pd.DataFrame()
        )

        ha_impegni = not impegni_giorno.empty
        colore_sfondo = (
            "#d1e7dd" if ha_impegni else "#f8f9fa"
        )  # Verde chiaro se impegnato, grigio chiaro se vuoto
        colore_bordo = "#198754" if ha_impegni else "#dee2e6"
        colore_testo = "#0f5132" if ha_impegni else "#212529"

        # Crea il testo del dettaglio per il tooltip (attributo title di HTML)
        tooltip_testo = f"Data: {giorno}/{st.session_state.cal_mese}/{st.session_state.cal_anno}\n"
        if ha_impegni:
          for _, row in impegni_giorno.iterrows():
            escluso_str = (
                " (Escluso)" if row.get("Escluso_Conteggio", False) else ""
            )
            tooltip_testo += (
                f"- {row.get('Titolo', 'Impegno')} ({row.get('Ore', 0)}h){escluso_str}\n"
            )
        else:
          tooltip_testo += "Nessun impegno"

        # Renderizza il quadratino/rettangolo cliccabile/hoverabile con HTML
        card_html = f"""
                <div title="{tooltip_testo}" style="
                    height: 75px; 
                    border: 1px solid {colore_bordo}; 
                    background-color: {colore_sfondo}; 
                    color: {colore_testo};
                    border-radius: 6px; 
                    padding: 5px; 
                    margin-bottom: 5px;
                    cursor: pointer;
                    overflow: hidden;
                    font-size: 13px;">
                    <b>{giorno}</b><br>
                    <span style="font-size: 11px;">{'📅 ' + str(len(impegni_giorno)) + ' alt.' if ha_impegni else ''}</span>
                </div>
                """
        st.markdown(card_html, unsafe_allow_html=True)
