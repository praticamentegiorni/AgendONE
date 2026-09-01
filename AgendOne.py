import streamlit as st
import pandas as pd
from datetime import datetime, time, date
import io

# ---------------------------------------------------------
# CONFIGURAZIONE PAGINA
# ---------------------------------------------------------
st.set_page_config(
    page_title="AgendOne - Gestione Attività",
    page_icon="📅",
    layout="wide"
)

# ---------------------------------------------------------
# FUNZIONE DI SINCRONIZZAZIONE GOOGLE CALENDAR
# ---------------------------------------------------------
def sincronizza_google_calendar(azione, dati_evento, evento_id_esistente=None):
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        # Legge le credenziali dai secrets di Streamlit
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

        # Recupera il calendar_id dai secret (fallback su primary se assente)
        calendar_id = gsheets_secrets.get("calendar_id", "primary")

        if azione == "crea" and dati_evento:
            data_str = str(dati_evento.get("Data", ""))
            start_datetime = f"{data_str}T{dati_evento.get('Orario Inizio', '08:00')}:00"
            end_datetime = f"{data_str}T{dati_evento.get('Orario Fine', '09:00')}:00"

            body = {
                'summary': f"Lezione/Impegno: {dati_evento.get('Classe', '')} ({dati_evento.get('Modalità', '')})",
                'location': str(dati_evento.get('Sede', '')),
                'description': f"Note: {dati_evento.get('Note', '')}\nGestito da AgendOne",
                'start': {'dateTime': start_datetime, 'timeZone': 'Europe/Rome'},
                'end': {'dateTime': end_datetime, 'timeZone': 'Europe/Rome'},
            }
            event_result = service.events().insert(calendarId=calendar_id, body=body).execute()
            return event_result.get('id')

        elif azione == "elimina" and evento_id_esistente:
            try:
                service.events().delete(calendarId=calendar_id, calendarEventId=evento_id_esistente).execute()
            except Exception:
                pass # Ignora se l'evento è già stato rimosso direttamente da Google Calendar
            return None

    except Exception as e:
        st.warning(f"Avviso Google Calendar: {e}")
        return None
    return None

# ---------------------------------------------------------
# FUNZIONI DI GESTIONE DATI (Esempio strutturale)
# ---------------------------------------------------------
@st.cache_data(ttl=60)
def carica_dati():
    # Sostituisci o adatta con la logica di caricamento del tuo Google Sheets / CSV
    try:
        from streamlit_gsheets import GSheetsConnection
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(ttl=0)
        if "Calendar_ID" not in df.columns:
            df["Calendar_ID"] = ""
        return df
    except Exception:
        # Fallback DataFrame vuoto per sicurezza se manca la connessione fogli
        return pd.DataFrame(columns=["Data", "Orario Inizio", "Orario Fine", "Classe", "Sede", "Modalità", "Note", "Calendar_ID"])

def salva_dati(df):
    try:
        from streamlit_gsheets import GSheetsConnection
        conn = st.connection("gsheets", type=GSheetsConnection)
        conn.update(data=df)
        st.cache_data.clear()
    except Exception as e:
        st.error(f"Errore durante il salvataggio dei dati: {e}")

# Caricamento effettivo del DataFrame
df = carica_dati()

# ---------------------------------------------------------
# INTERFACCIA PRINCIPALE
# ---------------------------------------------------------
st.title("📅 AgendOne - Dashboard Attività")

tab1, tab2, tab3 = st.tabs(["➕ Nuovo Appuntamento", "📋 Visualizza / Modifica", "🔄 Report & Sincronizzazione"])

with tab1:
    st.header("Inserisci Nuova Attività")
    with st.form("form_nuovo"):
        col1, col2 = st.columns(2)
        with col1:
            data_app = st.date_input("Data", value=date.today())
            ora_inizio = st.time_input("Orario Inizio", value=time(8, 0))
            classe = st.text_input("Classe / Titolo")
        with col2:
            ora_fine = st.time_input("Orario Fine", value=time(9, 0))
            sede = st.text_input("Sede")
            modalità = st.selectbox("Modalità", ["In presenza", "Online", "Misto"])
        
        note = st.text_area("Note aggiuntive")
        submit = st.form_submit_button("Salva e Sincronizza")

        if submit:
            nuovo_dict = {
                "Data": str(data_app),
                "Orario Inizio": str(ora_inizio),
                "Orario Fine": str(ora_fine),
                "Classe": classe,
                "Sede": sede,
                "Modalità": modalità,
                "Note": note
            }
            
            # Crea evento su Google Calendar
            cal_id = sincronizza_google_calendar("crea", nuovo_dict)
            
            # Aggiunge al dataframe
            nuova_riga = pd.DataFrame([{
                "Data": str(data_app),
                "Orario Inizio": str(ora_inizio),
                "Orario Fine": str(ora_fine),
                "Classe": classe,
                "Sede": sede,
                "Modalità": modalità,
                "Note": note,
                "Calendar_ID": cal_id if cal_id else ""
            }])
            
            df = pd.concat([df, nuova_riga], ignore_index=True)
            salva_dati(df)
            st.success("Attività salvata e sincronizzata con successo!")
            st.rerun()

with tab2:
    st.header("Archivio e Gestione Attività")
    if df.empty:
        st.info("Nessuna attività registrata nell'archivio.")
    else:
        # Mostra tabella modificabile o interattiva per la cancellazione
        st.dataframe(df, use_container_width=True)
        
        st.subheader("Elimina un Appuntamento")
        indice_da_eliminare = st.number_input("Inserisci l'indice (Row Index) della riga da eliminare:", min_value=0, max_value=max(0, len(df)-1), step=1)
        
        if st.button("🗑️ Elimina Riga Selezionata", use_container_width=True):
            row_to_delete = df.loc[indice_da_eliminare]
            cal_id_da_rimuovere = row_to_delete.get("Calendar_ID", "")
            
            # Tenta la rimozione da Google Calendar se ha un ID valido
            if pd.notnull(cal_id_da_rimuovere) and str(cal_id_da_rimuovere).strip() != "":
                sincronizza_google_calendar("elimina", None, evento_id_esistente=str(cal_id_da_rimuovere))
            
            # Rimuove localmente
            df = df.drop(indice_da_eliminare).reset_index(drop=True)
            salva_dati(df)
            st.success("Attività eliminata con successo!")
            st.rerun()

with tab3:
    st.header("Report e Sincronizzazione Storico")
    st.markdown("Usa questo pulsante per sincronizzare massivamente tutti i vecchi appuntamenti che non sono ancora presenti sul calendario Google.")
    
    if st.button("🔄 Sincronizza eventi mancanti su Google Calendar", use_container_width=True):
        eventi_da_sincronizzare = []
        for idx, row in df.iterrows():
            cal_id_esistente = row.get("Calendar_ID", "")
            if not cal_id_esistente or str(cal_id_esistente).strip() == "" or str(cal_id_esistente).lower() == "nan":
                eventi_da_sincronizzare.append(idx)
                
        totale = len(eventi_da_sincronizzare)
        
        if totale == 0:
            st.info("Tutti gli eventi risultano già sincronizzati con Google Calendar.")
        else:
            barra_progresso = st.progress(0)
            conteggio_sinc = 0
            
            for i, idx in enumerate(eventi_da_sincronizzare):
                row = df.loc[idx]
                dati_evento = {
                    "Data": str(row["Data"]),
                    "Orario Inizio": str(row["Orario Inizio"]),
                    "Orario Fine": str(row["Orario Fine"]),
                    "Classe": str(row["Classe"]),
                    "Sede": str(row["Sede"]),
                    "Modalità": str(row["Modalità"]),
                    "Note": str(row["Note"]) if pd.notnull(row["Note"]) else ""
                }
                
                nuovo_id = sincronizza_google_calendar("crea", dati_evento)
                if nuovo_id:
                    df.loc[idx, "Calendar_ID"] = nuovo_id
                    conteggio_sinc += 1
                
                barra_progresso.progress((i + 1) / totale)
            
            if conteggio_sinc > 0:
                salva_dati(df)
                st.success(f"Sincronizzati con successo {conteggio_sinc} eventi su Google Calendar!")
                st.rerun()
            else:
                st.warning("Non è stato possibile sincronizzare gli eventi. Controlla la connessione o i permessi.")
