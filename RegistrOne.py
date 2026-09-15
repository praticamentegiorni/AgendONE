import datetime
import pandas as pd
import streamlit as st
from streamlit_gsheets import GSheetsConnection


def main():
  # Impostazione pagina (se richiamato da modulo principale, gestito in sicurezza)
  try:
    st.set_page_config(page_title="RegistrOne - Registro di Classe", layout="wide")
  except Exception:
    pass

  # CSS PERSONALIZZATO IDENTICO AD AGENDONE PER MANTENERE COERENZA GRAFICA
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

      /* Tab attivo evidenziato */
      button[data-baseweb="tab"][aria-selected="true"] {
          background-color: #2563eb !important;
          color: #ffffff !important;
          border-color: #3b82f6 !important;
          box-shadow: 0 4px 12px rgba(37, 99, 235, 0.4) !important;
      }

      .stCard {
          background-color: #ffffff;
          padding: 20px;
          border-radius: 10px;
          box-shadow: 0 2px 4px rgba(0,0,0,0.05);
          margin-bottom: 15px;
      }
      </style>
      """,
      unsafe_allow_html=True,
  )

  # Connessione a Google Sheets dedicata a RegistrOne
  try:
    conn = st.connection("gsheets_registrone", type=GSheetsConnection)
  except Exception as e:
    st.error(
        "Errore nella configurazione della connessione Google Sheets nei"
        f" secrets: {e}"
    )
    st.stop()

  def carica_tabella(worksheet_name):
    """Legge un foglio specifico da Google Sheets e restituisce un DataFrame pulito."""
    try:
      df = conn.read(worksheet=worksheet_name, ttl=0)
      df = df.dropna(how="all")
      return df
    except Exception:
      return pd.DataFrame()

  def salva_tabella(df, worksheet_name):
    """Sovrascrive il foglio Google Sheets con i dati aggiornati del DataFrame."""
    try:
      conn.update(worksheet=worksheet_name, data=df)
      st.cache_data.clear()
    except Exception as e:
      st.error(f"Errore durante il salvataggio sul foglio {worksheet_name}: {e}")

  # --- CARICAMENTO DATI DAL DATABASE GOOGLE SHEETS ---
  df_classi = carica_tabella("Classi")
  df_alunni = carica_tabella("Alunni")
  df_presenze = carica_tabella("Presenze")
  df_voti = carica_tabella("Voti")
  df_note = carica_tabella("Note")
  df_materie = carica_tabella("Materie")
  df_scuole = carica_tabella("Scuole")

  # Liste di supporto estratte dai DataFrame (con fallback di default se vuote)
  lista_classi = (
      df_classi["nome_classe"].dropna().astype(str).tolist()
      if not df_classi.empty and "nome_classe" in df_classi.columns
      else []
  )
  lista_materie = (
      df_materie["Materia"].dropna().astype(str).tolist()
      if not df_materie.empty and "Materia" in df_materie.columns
      else ["Informatica", "Laboratorio", "Sistemi e Reti"]
  )
  lista_scuole = (
      df_scuole["Scuola"].dropna().astype(str).tolist()
      if not df_scuole.empty and "Scuola" in df_scuole.columns
      else [
          "Scuola Media Statale",
          "Altro Istituto Professionale",
          "Liceo Scientifico",
      ]
  )

  # --- INTESTAZIONE PRINCIPALE ---
  st.title("📚 RegistrOne - Registro di Classe Professionale")
  st.markdown("---")

  # MENU PRINCIPALE A TAB (Stile AgendOne)
  tabs = st.tabs([
      "🏫 Gestione Classi",
      "👨‍🎓 Anagrafica Alunni",
      "📅 Registro Presenze",
      "📝 Voti & Note",
      "⚙️ Tabelle & Config",
  ])

  # ==========================================
  # 1. GESTIONE CLASSI
  # ==========================================
  with tabs[0]:
    st.subheader("Gestione Sezioni / Classi")
    col1, col2 = st.columns([2, 1])

    with col1:
      st.markdown("### Elenco Classi Attive")
      if lista_classi:
        for c in lista_classi:
          st.info(f"📁 **{c}**")
      else:
        st.warning(
            "Nessuna classe inserita. Crea la prima utilizzando il modulo a"
            " destra."
        )

    with col2:
      st.markdown("### Aggiungi Classe")
      nuova_classe = st.text_input("Nome Classe (es. 1A Informatica)")
      if st.button("Crea Classe"):
        if nuova_classe and nuova_classe not in lista_classi:
          nuovo_id = str(len(df_classi) + 1)
          nuova_riga = pd.DataFrame(
              [{"id_classe": nuovo_id, "nome_classe": nuova_classe}]
          )
          df_classi = pd.concat([df_classi, nuova_riga], ignore_index=True)
          salva_tabella(df_classi, "Classi")
          st.success(f"Classe {nuova_classe} aggiunta con successo!")
          st.rerun()
        else:
          st.error("Inserisci un nome valido o già esistente.")

    # Sezione di Modifica ed Eliminazione Classi esistenti
    if lista_classi:
      st.markdown("---")
      st.markdown("### Modifica o Elimina Classe Esistente")
      classe_selezionata_gestione = st.selectbox(
          "Seleziona classe", lista_classi, key="ges_cl"
      )

      col_m1, col_m2 = st.columns(2)
      with col_m1:
        nuovo_nome_classe = st.text_input(
            "Rinomina classe", value=classe_selezionata_gestione
        )
        if st.button("Aggiorna Nome Classe"):
          if nuovo_nome_classe and nuovo_nome_classe not in lista_classi:
            vecchio_nome = classe_selezionata_gestione
            df_classi.loc[
                df_classi["nome_classe"] == vecchio_nome, "nome_classe"
            ] = nuovo_nome_classe
            salva_tabella(df_classi, "Classi")

            if not df_alunni.empty and "classe" in df_alunni.columns:
              df_alunni.loc[df_alunni["classe"] == vecchio_nome, "classe"] = (
                  nuovo_nome_classe
              )
              salva_tabella(df_alunni, "Alunni")

            st.success("Classe aggiornata con successo!")
            st.rerun()
          else:
            st.error("Nome non valido o già esistente.")

      with col_m2:
        st.write("")
        st.write("")
        if st.button("Elimina Classe", type="primary"):
          alunni_nella_classe = (
              [
                  a
                  for a in df_alunni.to_dict("records")
                  if a.get("classe") == classe_selezionata_gestione
              ]
              if not df_alunni.empty and "classe" in df_alunni.columns
              else []
          )
          if alunni_nella_classe:
            st.error(
                "Impossibile eliminare la classe: contiene ancora studenti"
                " iscritti. Sposta o elimina prima gli studenti."
            )
          else:
            df_classi = df_classi[
                df_classi["nome_classe"] != classe_selezionata_gestione
            ]
            salva_tabella(df_classi, "Classi")
            st.success("Classe eliminata.")
            st.rerun()

  # ==========================================
  # 2. ANAGRAFICA ALUNNI
  # ==========================================
  with tabs[1]:
    st.subheader("Gestione Anagrafica Studenti")

    if not lista_classi:
      st.warning(
          "Prima di inserire alunni, devi creare almeno una classe nella scheda"
          " 'Gestione Classi'."
      )
    else:
      classe_filtro = st.selectbox(
          "Seleziona Classe per Anagrafica", ["Tutte"] + lista_classi
      )

      with st.expander(
          "➕ Inserisci Nuovo Alunno / Modifica Scheda", expanded=False
      ):
        with st.form("form_alunno"):
          col_a, col_b = st.columns(2)
          with col_a:
            nome = st.text_input("Nome")
            cognome = st.text_input("Cognome")
            classe_assegnata = st.selectbox("Classe", lista_classi)
            data_ins = st.date_input(
                "Data Inserimento", datetime.date.today()
            ).strftime("%Y-%m-%d")

          with col_b:
            altra_scuola = st.checkbox("Provenienza da altra scuola")
            scuola_prec = st.selectbox(
                "Scuola di provenienza",
                lista_scuole if lista_scuole else ["Nessuna"],
            )
            parla_italiano = st.selectbox(
                "Parla la lingua italiana?", ["Sì", "No / Parzialmente"]
            )
            provenienza_orig = st.text_input(
                "Provenienza originaria (Paese/Città)"
            )

          col_c, col_d = st.columns(2)
          with col_c:
            famiglia_comunita = st.selectbox(
                "Situazione Abitativa", ["Famiglia", "Comunità", "Altro"]
            )
            dimesso = st.checkbox("Studente Dimesso")
            motivo_dim = st.text_input(
                "Motivo dimissione (se attivo)", disabled=not dimesso
            )

          with col_d:
            problemi_apprendimento = st.checkbox(
                "Problemi di apprendimento / DSA / BES"
            )
            dettagli_app = st.text_area(
                "Se sì, specificare i problemi / piano di supporto",
                disabled=not problemi_apprendimento,
            )

          nota_testo = st.text_area("Note generali sull'alunno")

          submitted = st.form_submit_button("Salva Alunno")
          if submitted and nome and cognome:
            nuovo_id = (
                str(len(df_alunni) + 1)
                + "_"
                + str(int(datetime.datetime.now().timestamp()))
            )
            nuovo_alunno_dict = {
                "id": nuovo_id,
                "nome": nome,
                "cognome": cognome,
                "classe": classe_assegnata,
                "data_inserimento": data_ins,
                "dimesso": str(dimesso),
                "motivo_dimissione": motivo_dim if dimesso else "",
                "altra_scuola": str(altra_scuola),
                "scuola_prec": scuola_prec if altra_scuola else "",
                "parla_italiano": parla_italiano,
                "provenienza_orig": provenienza_orig,
                "famiglia_comunita": famiglia_comunita,
                "problemi_apprendimento": str(problemi_apprendimento),
                "dettagli_apprendimento": dettagli_app
                if problemi_apprendimento
                else "",
                "nota_testo": nota_testo,
            }
            df_alunni = pd.concat(
                [df_alunni, pd.DataFrame([nuovo_alunno_dict])], ignore_index=True
            )
            salva_tabella(df_alunni, "Alunni")
            st.success(f"Alunno {nome} {cognome} salvato con successo!")
            st.rerun()

      st.markdown("### Elenco Studenti Registrati")
      records_alunni = (
          df_alunni.to_dict("records")
          if not df_alunni.empty and "id" in df_alunni.columns
          else []
      )
      alunni_filtrati = (
          records_alunni
          if classe_filtro == "Tutte"
          else [
              a for a in records_alunni if str(a.get("classe")) == classe_filtro
          ]
      )

      if alunni_filtrati:
        df_mostra = pd.DataFrame(alunni_filtrati)
        colonne_visibili = [
            c
            for c in [
                "nome",
                "cognome",
                "classe",
                "dimesso",
                "parla_italiano",
                "famiglia_comunita",
            ]
            if c in df_mostra.columns
        ]
        st.dataframe(df_mostra[colonne_visibili], use_container_width=True)

        st.markdown("---")
        scelta_alunno = st.selectbox(
            "Seleziona studente per dettagli o eliminazione",
            options=alunni_filtrati,
            format_func=lambda x: f"{x.get('cognome', '')} {x.get('nome', '')} ({x.get('classe', '')})",
        )
        if scelta_alunno:
          with st.expander(
              f"Scheda Dettaglio: {scelta_alunno.get('cognome')} {scelta_alunno.get('nome')}"
          ):
            st.write(
                f"**Data Inserimento:** {scelta_alunno.get('data_inserimento', 'N/D')}"
            )
            st.write(
                f"**Provenienza Altra Scuola:** {'Sì (' + str(scelta_alunno.get('scuola_prec','')) + ')' if str(scelta_alunno.get('altra_scuola'))=='True' else 'No'}"
            )
            st.write(
                f"**Parla Italiano:** {scelta_alunno.get('parla_italiano', 'Sì')}"
            )
            st.write(
                f"**Provenienza Originaria:** {scelta_alunno.get('provenienza_orig', 'N/D')}"
            )
            st.write(
                f"**Abitazione:** {scelta_alunno.get('famiglia_comunita', 'Famiglia')}"
            )
            st.write(
                f"**Problemi Apprendimento:** {'Sì - ' + str(scelta_alunno.get('dettagli_apprendimento','')) if str(scelta_alunno.get('problemi_apprendimento'))=='True' else 'No'}"
            )
            st.write(
                f"**Dimesso:** {'Sì (Motivo: ' + str(scelta_alunno.get('motivo_dimissione','')) + ')' if str(scelta_alunno.get('dimesso'))=='True' else 'No'}"
            )
            st.info(f"**Note:** {scelta_alunno.get('nota_testo', '')}")

            if st.button("Elimina Alunno", type="primary"):
              id_da_rimuovere = str(scelta_alunno.get("id"))
              df_alunni = df_alunni[
                  df_alunni["id"].astype(str) != id_da_rimuovere
              ]
              salva_tabella(df_alunni, "Alunni")
              st.success("Alunno eliminato.")
              st.rerun()
      else:
        st.info("Nessun alunno trovato per i filtri selezionati.")

  # ==========================================
  # 3. REGISTRO PRESENZE
  # ==========================================
  with tabs[2]:
    st.subheader("Registro Presenze e Assenze Giornaliere")

    if not lista_classi:
      st.warning("Crea prima almeno una classe.")
    else:
      c_sel_cl, c_sel_dt = st.columns(2)
      with c_sel_cl:
        classe_pres = st.selectbox(
            "Seleziona Classe per Registro",
            lista_classi,
            key="pres_classe_selezionata",
        )
      with c_sel_dt:
        data_registro = st.date_input(
            "Data Registro", datetime.date.today()
        ).strftime("%Y-%m-%d")

      records_alunni_tutti = (
          df_alunni.to_dict("records")
          if not df_alunni.empty and "id" in df_alunni.columns
          else []
      )
      alunni_classe = [
          a for a in records_alunni_tutti if str(a.get("classe")) == classe_pres
      ]

      if alunni_classe:
        st.markdown(f"### Appello del giorno: {data_registro}")
        with st.form("form_appello"):
          stili_presenza = {}
          records_presenze = (
              df_presenze.to_dict("records")
              if not df_presenze.empty and "alunno_id" in df_presenze.columns
              else []
          )

          for al in alunni_classe:
            esistente = next(
                (
                    p
                    for p in records_presenze
                    if str(p.get("alunno_id")) == str(al["id"])
                    and str(p.get("data")) == data_registro
                ),
                None,
            )
            idx_default = 0
            if esistente:
              stato_esistente = str(esistente.get("stato"))
              if stato_esistente == "Assente":
                idx_default = 1
              elif stato_esistente == "Giustificato":
                idx_default = 2

            stili_presenza[al["id"]] = st.selectbox(
                f"{al.get('cognome', '')} {al.get('nome', '')}",
                ["Presente", "Assente", "Giustificato"],
                index=idx_default,
                key=f"pres_{al['id']}",
            )

          salva_appello = st.form_submit_button("Registra Presenze Giornaliere")
          if salva_appello:
            if not df_presenze.empty and "data" in df_presenze.columns:
              ids_classe = [str(a["id"]) for a in alunni_classe]
              df_presenze = df_presenze[
                  ~(
                      (df_presenze["data"].astype(str) == data_registro)
                      & (
                          df_presenze["alunno_id"]
                          .astype(str)
                          .isin(ids_classe)
                      )
                  )
              ]

            nuove_presenze_list = []
            for al_id, stato in stili_presenza.items():
              nuove_presenze_list.append({
                  "alunno_id": str(al_id),
                  "data": data_registro,
                  "stato": stato,
              })

            df_presenze = pd.concat(
                [df_presenze, pd.DataFrame(nuove_presenze_list)],
                ignore_index=True,
            )
            salva_tabella(df_presenze, "Presenze")
            st.success("Presenze salvate correttamente!")

        st.markdown("---")
        st.markdown("### 🔍 Ricerca e Statistiche Assenze per Intervallo di Date")
        col_f1, col_f2 = st.columns(2)
        with col_f1:
          data_inizio = st.date_input(
              "Data Inizio", datetime.date.today() - datetime.timedelta(days=30)
          )
        with col_f2:
          data_fine = st.date_input("Data Fine", datetime.date.today())

        if st.button("Calcola Conteggio Assenze"):
          st.markdown(
              f"**Report assenze dal {data_inizio} al {data_fine} per la classe"
              f" {classe_pres}:**"
          )
          report_assenze = []
          records_presenze_tot = (
              df_presenze.to_dict("records")
              if not df_presenze.empty and "alunno_id" in df_presenze.columns
              else []
          )
          for al in alunni_classe:
            tot_assenze = sum(
                1
                for p in records_presenze_tot
                if str(p.get("alunno_id")) == str(al["id"])
                and str(p.get("stato")) == "Assente"
                and data_inizio.strftime("%Y-%m-%d")
                <= str(p.get("data"))
                <= data_fine.strftime("%Y-%m-%d")
            )
            report_assenze.append({
                "Alunno": f"{al.get('cognome', '')} {al.get('nome', '')}",
                "Giorni Assente": tot_assenze,
            })
          st.table(pd.DataFrame(report_assenze))
      else:
        st.warning("Nessun alunno presente in questa classe.")

  # ==========================================
  # 4. VOTI & NOTE
  # ==========================================
  with tabs[3]:
    st.subheader("Gestione Voti e Note Disciplinari")

    if not lista_classi:
      st.warning("Crea prima almeno una classe.")
    else:
      classe_voti = st.selectbox(
          "Seleziona Classe", lista_classi, key="classe_voti_sel"
      )
      records_alunni_voti = (
          df_alunni.to_dict("records")
          if not df_alunni.empty and "id" in df_alunni.columns
          else []
      )
      alunni_voti = [
          a for a in records_alunni_voti if str(a.get("classe")) == classe_voti
      ]

      if alunni_voti:
        tab_v, tab_n = st.tabs(
            ["📊 Inserimento Voti", "📌 Note di Merito / Demerito"]
        )

        with tab_v:
          with st.form("form_voto"):
            alunno_selezionato = st.selectbox(
                "Studente",
                alunni_voti,
                format_func=lambda x: f"{x.get('cognome', '')} {x.get('nome', '')}",
            )
            col_v1, col_v2 = st.columns(2)
            with col_v1:
              materia_scelta = st.selectbox(
                  "Materia", lista_materie if lista_materie else ["Generale"]
              )
              voto_num = st.slider(
                  "Voto", min_value=3, max_value=10, value=6, step=1
              )
            with col_v2:
              data_voto = st.date_input(
                  "Data Voto", datetime.date.today(), key="dv"
              ).strftime("%Y-%m-%d")
              nota_voto = st.text_input(
                  "Motivo / Spiegazione del voto (es. Interrogazione, Verifica"
                  " scritta)"
              )

            if st.form_submit_button("Assegna Voto"):
              nuovo_voto = {
                  "alunno_id": str(alunno_selezionato["id"]),
                  "materia": materia_scelta,
                  "voto": str(voto_num),
                  "data": data_voto,
                  "nota_voto": nota_voto,
              }
              df_voti = pd.concat(
                  [df_voti, pd.DataFrame([nuovo_voto])], ignore_index=True
              )
              salva_tabella(df_voti, "Voti")
              st.success("Voto inserito con successo!")

          st.markdown("### Storico Voti Studente Selezionato")
          st_sel_storico = st.selectbox(
              "Seleziona studente per visualizzare i voti",
              alunni_voti,
              format_func=lambda x: f"{x.get('cognome', '')} {x.get('nome', '')}",
              key="storico_voti",
          )
          records_voti = (
              df_voti.to_dict("records")
              if not df_voti.empty and "alunno_id" in df_voti.columns
              else []
          )
          voti_studente = [
              v
              for v in records_voti
              if str(v.get("alunno_id")) == str(st_sel_storico["id"])
          ]
          if voti_studente:
            st.dataframe(pd.DataFrame(voti_studente), use_container_width=True)
          else:
            st.info("Nessun voto registrato per questo studente.")

        with tab_n:
          with st.form("form_nota"):
            alunno_nota = st.selectbox(
                "Studente",
                alunni_voti,
                format_func=lambda x: f"{x.get('cognome', '')} {x.get('nome', '')}",
                key="al_nota",
            )
            tipo_nota = st.selectbox(
                "Tipo Nota", ["Merito", "Demerito / Disciplinare"]
            )
            desc_nota = st.text_area("Testo della nota")
            data_nota = st.date_input(
                "Data Nota", datetime.date.today()
            ).strftime("%Y-%m-%d")

            if st.form_submit_button("Registra Nota"):
              nuova_nota = {
                  "alunno_id": str(alunno_nota["id"]),
                  "tipo": tipo_nota,
                  "descrizione": desc_nota,
                  "data": data_nota,
              }
              df_note = pd.concat(
                  [df_note, pd.DataFrame([nuova_nota])], ignore_index=True
              )
              salva_tabella(df_note, "Note")
              st.success("Nota registrata!")

          st.markdown("### Elenco Note per Studente")
          st_nota_storico = st.selectbox(
              "Seleziona studente per note",
              alunni_voti,
              format_func=lambda x: f"{x.get('cognome', '')} {x.get('nome', '')}",
              key="storico_note",
          )
          records_note = (
              df_note.to_dict("records")
              if not df_note.empty and "alunno_id" in df_note.columns
              else []
          )
          note_studente = [
              n
              for n in records_note
              if str(n.get("alunno_id")) == str(st_nota_storico["id"])
          ]
          if note_studente:
            for n in note_studente:
              tipo = str(n.get("tipo", ""))
              data = str(n.get("data", ""))
              desc = str(n.get("descrizione", ""))
              if "Merito" in tipo:
                st.success(f"[{data}] **{tipo}**: {desc}")
              else:
                st.error(f"[{data}] **{tipo}**: {desc}")
          else:
            st.info("Nessuna nota registrata.")
      else:
        st.warning("Seleziona una classe con alunni.")

  # ==========================================
  # 5. TABELLE & CONFIGURAZIONE
  # ==========================================
  with tabs[4]:
    st.subheader("Gestione Tabelle di Configurazione")

    col_t1, col_t2 = st.columns(2)

    with col_t1:
      st.markdown("### 📚 Gestione Materie")
      nuova_materia = st.text_input("Nome Materia")
      if st.button("Aggiungi Materia"):
        if nuova_materia and nuova_materia not in lista_materie:
          nuova_materia_row = {"Materia": nuova_materia}
          df_materie = pd.concat(
              [df_materie, pd.DataFrame([nuova_materia_row])],
              ignore_index=True,
          )
          salva_tabella(df_materie, "Materie")
          st.success("Materia aggiunta!")
          st.rerun()

      st.write("Materie attuali:")
      for m in lista_materie:
        st.write(f"- {m}")

    with col_t2:
      st.markdown("### 🏫 Scuole di Provenienza")
      nuova_scuola = st.text_input("Nome Scuola")
      if st.button("Aggiungi Scuola"):
        if nuova_scuola and nuova_scuola not in lista_scuole:
          nuova_scuola_row = {"Scuola": nuova_scuola}
          df_scuole = pd.concat(
              [df_scuole, pd.DataFrame([nuova_scuola_row])], ignore_index=True
          )
          salva_tabella(df_scuole, "Scuole")
          st.success("Scuola aggiunta!")
          st.rerun()

      st.write("Scuole attuali:")
      for s in lista_scuole:
        st.write(f"- {s}")


if __name__ == "__main__":
  main()
