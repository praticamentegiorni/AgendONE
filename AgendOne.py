import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

st.set_page_config(page_title="AgendOne", layout="wide")

# Configurazione Google Sheets
def get_gspread_client_and_sheet():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)
        spreadsheet_url = st.secrets["sheets"]["spreadsheet_url"]
        sheet = client.open_by_url(spreadsheet_url).sheet1
        return sheet
    except Exception as e:
        st.error(f"Errore di connessione a Google Sheets: {e}")
        return None

def carica_dati():
    worksheet = get_gspread_client_and_sheet()
    if worksheet is None:
        return pd.DataFrame()
    data = worksheet.get_all_records()
    cols_standard = ["Data", "Mese", "Orario Inizio", "Orario Fine", "Ore", "Ente", "Classe", "Sede", "Modalità", "Svolto", "Escludi_Conteggio", "Note", "Calendar_ID", "Reminder_Minuti"]
    if not data:
        return pd.DataFrame(columns=cols_standard)
    df = pd.DataFrame(data)
    for c in cols_standard:
        if c not in df.columns:
            df[c] = ""
    return df

def salva_dati(df_to_save):
    if "Data_dt" in df_to_save.columns:
        df_to_save = df_to_save.drop(columns=["Data_dt"])
    cols_standard = ["Data", "Mese", "Orario Inizio", "Orario Fine", "Ore", "Ente", "Classe", "Sede", "Modalità", "Svolto", "Escludi_Conteggio", "Note", "Calendar_ID", "Reminder_Minuti"]
    for c in cols_standard:
        if c not in df_to_save.columns:
            df_to_save[c] = ""
    df_to_save = df_to_save[cols_standard]
    df_to_save = df_to_save.fillna("")
    
    try:
        worksheet = get_gspread_client_and_sheet()
        if worksheet is None:
            st.error("Impossibile connettersi a Google Sheets. Verifica i Secrets.")
            return
        
        righe = [df_to_save.columns.values.tolist()] + df_to_save.values.tolist()
        
        # Pulisce e aggiorna in modo sicuro
        worksheet.clear()
        worksheet.update("A1", righe)
    except Exception as e:
        st.error(f"Errore durante il salvataggio su Google Sheets: {e}")

# Interfaccia Principale con Tab
st.title("AgendOne - Gestione Attività e Orari")

tab1, tab2, tab3 = st.tabs(["Inserimento", "Calendario & Report", "Storico & Gestione Attività"])

df_dati = carica_dati()

with tab1:
    st.header("Nuovo Appuntamento")
    with st.form("form_inserimento"):
        col1, col2 = st.columns(2)
        with col1:
            data_app = st.date_input("Data")
            ora_inizio = st.time_input("Orario Inizio")
            ora_fine = st.time_input("Orario Fine")
            ente = st.text_input("Ente")
            classe = st.text_input("Classe")
        with col2:
            sede = st.text_input("Sede")
            modalita = st.selectbox("Modalità", ["In presenza", "Online"])
            note = st.text_area("Note")
            escludi = st.checkbox("Escludi dal conteggio ore")
        
        submitted = st.form_submit_button("Salva Attività")
        if submitted:
            dt_inizio = datetime.combine(data_app, ora_inizio)
            dt_fine = datetime.combine(data_app, ora_fine)
            ore_diff = (dt_fine - dt_inizio).total_seconds() / 3600.0
            if ore_diff < 0:
                ore_diff = 0
            
            mese_str = data_app.strftime("%B %Y")
            
            nuova_riga = {
                "Data": data_app.strftime("%Y-%m-%d"),
                "Mese": mese_str,
                "Orario Inizio": ora_inizio.strftime("%H:%M"),
                "Orario Fine": ora_fine.strftime("%H:%M"),
                "Ore": round(ore_diff, 2),
                "Ente": ente,
                "Classe": classe,
                "Sede": sede,
                "Modalità": modalita,
                "Svolto": False,
                "Escludi_Conteggio": escludi,
                "Note": note,
                "Calendar_ID": "",
                "Reminder_Minuti": 30
            }
            
            df_dati = pd.concat([df_dati, pd.DataFrame([nuova_riga])], ignore_index=True)
            salva_dati(df_dati)
            st.success("Attività inserita con successo!")
            st.rerun()

with tab2:
    st.header("Calendario & Report")
    if not df_dati.empty:
        st.dataframe(df_dati, use_container_width=True)
    else:
        st.info("Nessun dato registrato.")

with tab3:
    st.header("Storico & Gestione Attività")
    if not df_dati.empty:
        df_editabile = df_dati.copy()
        df_editabile.insert(0, "ID", range(len(df_editabile)))
        df_editabile.insert(0, "Seleziona", False)
        
        st.info("Nota: Le colonne testuali (Ente, Classe, Note, ecc.) sono protette da modifica diretta in griglia per evitare perdite di dati. Utilizza le checkbox per aggiornare rapidamente lo stato.")
        
        # Configurazione protetta per st.data_editor per bloccare le celle testuali
        df_editato = st.data_editor(
            df_editabile,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Seleziona": st.column_config.CheckboxColumn(required=True),
                "ID": st.column_config.NumberColumn(disabled=True),
                "Data": st.column_config.TextColumn(disabled=True),
                "Mese": st.column_config.TextColumn(disabled=True),
                "Orario Inizio": st.column_config.TextColumn(disabled=True),
                "Orario Fine": st.column_config.TextColumn(disabled=True),
                "Ore": st.column_config.NumberColumn(format="%.2f h", disabled=True),
                "Ente": st.column_config.TextColumn(disabled=True),
                "Classe": st.column_config.TextColumn(disabled=True),
                "Sede": st.column_config.TextColumn(disabled=True),
                "Modalità": st.column_config.TextColumn(disabled=True),
                "Note": st.column_config.TextColumn(disabled=True),
                "Svolto": st.column_config.CheckboxColumn(required=True),
                "Escludi_Conteggio": st.column_config.CheckboxColumn(required=True),
            }
        )
        
        if st.button("Salva Modifiche Checkbox"):
            modificato = False
            for _, riga_ed in df_editato.iterrows():
                idx_orig = int(riga_ed["ID"])
                val_nuovo_svolto = bool(riga_ed["Svolto"])
                val_nuovo_escluso = bool(riga_ed["Escludi_Conteggio"])
                
                if df_dati.loc[idx_orig, "Svolto"] != val_nuovo_svolto or df_dati.loc[idx_orig, "Escludi_Conteggio"] != val_nuovo_escluso:
                    df_dati.loc[idx_orig, "Svolto"] = val_nuovo_svolto
                    df_dati.loc[idx_orig, "Escludi_Conteggio"] = val_nuovo_escluso
                    modificato = True
            
            if modificato:
                salva_dati(df_dati)
                st.success("Stato attività aggiornato con successo!")
                st.rerun()
            else:
                st.info("Nessuna modifica rilevata.")
    else:
        st.write("Nessun dato disponibile.")
