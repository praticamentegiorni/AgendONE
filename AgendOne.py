from datetime import datetime, time, timedelta
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import streamlit as st

# Se modifiche gli scope, elimina il file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar']


def get_calendar_service():
  creds = None
  if os.path.exists('token.json'):
    creds = Credentials.from_authorized_user_file('token.json', SCOPES)
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
      creds = flow.run_local_server(port=0)
    with open('token.json', 'token') as token:
      token.write(creds.to_json())
  return build('calendar', 'v3', credentials=creds)


def main():
  st.set_page_config(
      page_title='AgendOne - Schedulazione', page_icon='📅', layout='centered'
  )

  st.title('📅 AgendOne')
  st.write('Pianifica i tuoi eventi e sincronizzali con Google Calendar.')

  # Input dell'utente
  summary = st.text_input('Titolo dell\'evento')
  description = st.text_area('Descrizione')
  event_date = st.date_input('Data dell\'evento', value=datetime.today())

  col1, col2 = st.columns(2)
  with col1:
    start_time = st.time_input(
        'Orario di inizio', value=time(9, 0)
    )  # Valido come oggetto datetime.time
  with col2:
    end_time = st.time_input('Orario di fine', value=time(10, 0))

  if st.button('Crea Evento'):
    # Validazione preventiva: controllo orari
    if start_time >= end_time:
      st.error(
          "⚠️ L'orario di inizio non può essere successivo o uguale all'orario"
          " di fine."
      )
    elif not summary.strip():
      st.warning("⚠️ Inserisci un titolo valido per l'evento.")
    else:
      try:
        service = get_calendar_service()

        # Unione di data e ora per creare oggetti datetime completi
        start_datetime = datetime.combine(event_date, start_time)
        end_datetime = datetime.combine(event_date, end_time)

        # Configurazione del corpo dell'evento con promemoria espliciti
        event_body = {
            'summary': summary,
            'description': description,
            'start': {
                'dateTime': start_datetime.isoformat(),
                'timeZone': 'Europe/Rome',
            },
            'end': {
                'dateTime': end_datetime.isoformat(),
                'timeZone': 'Europe/Rome',
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'popup', 'minutes': 15},
                    {'method': 'email', 'minutes': 60},
                ],
            },
        }

        # Chiamata API per inserire l'evento nel calendario principale
        event = (
            service.events()
            .insert(calendarId='primary', body=event_body)
            .execute()
        )
        st.success(
            f"✅ Evento creato con successo! Link: {event.get('htmlLink')}"
        )

      except Exception as e:
        st.error(f"❌ Si è verificato un errore durante la creazione: {e}")


if __name__ == '__main__':
  main()
