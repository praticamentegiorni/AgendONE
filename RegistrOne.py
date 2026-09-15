import datetime
import pandas as pd
import streamlit as st
from streamlit_gsheets import GSheetsConnection


def main():
  try:
    st.set_page_config(page_title="RegistrOne - Registro di Classe", layout="wide")
  except Exception:
    pass

  # CSS PERSONALIZZATO PER COERENZA GRAFICA CON AGENDONE
  st.markdown(
      """
      <style>
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
          border-color: #3b82f6 !important;
          box-shadow: 0 4px 12px rgba(37, 99, 235, 0.4) !important;
      }
      </style>
      """,
      unsafe_allow_html=True,
  )

  # Connessione a Google Sheets
  try:
    conn = st.connection("gsheets_registrone", type=GSheetsConnection)
  except Exception as e:
    st.error(
        "Errore nella configurazione della connessione Google Sheets nei"
        f" secrets: {e}"
    )
    st.stop()

  def carica_tabella(worksheet_name):
    try:
      df = conn.read(worksheet=worksheet_name, ttl=0)
      df = df.dropna(how="all")
      return df
    except Exception:
      return pd.DataFrame()

  def salva_tabella(df, worksheet_name):
    try:
      conn.update(worksheet=worksheet_name, data=df)
      st.cache_data.clear()
    except Exception as e:
      st.error(f"Errore durante il salvataggio sul foglio {worksheet_name}: {e}")

  # --- CARICAMENTO DATI DAI FOGLI GOOGLE ---
  df_classi = carica_tabella("Classi")
  df_alunni = carica_tabella("Alunni")
  df_presenze = carica_tabella("Presenze")
  df_voti = carica_tabella("Voti")
  df_note = carica_tabella("Note")
  df_materie = carica_tabella("Materie")
  df_scuole = carica_tabella("Scuole")

  # Estrazione liste di supporto basate sui tuoi fogli
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
      else ["Scuola Media", "Altro Istituto"]
  )

  st.title("📚 RegistrOne - Registro di Classe Professionale")
  st.markdown("---")

  # MENU PRINCIPALE A TAB
  tabs = st.tabs([
      "🏫 Gestione Classi",
      "👨‍🎓 Anagrafica Alunni",
      "📅 Registro Presenze",
      "📝 Voti & Note",
      "⚙️ Tabelle & Config",
  ])

  # ==========================================
  # 1. GESTIONE CLASSI (Foglio: Classi -> id_classe, nome_classe)
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
        st.warning("Nessuna classe inserita.")

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

  # ==========================================
  # 2. ANAGRAFICA ALUNNI (Foglio: Alunni -> id, nome, cognome, classe, data_inserimento, motivo_dimissione, scuola_prec, provenienza_orig, famiglia_comunita, dettagli_apprendi, nota_testo)
  # ==========================================
  with tabs[1]:
    st.subheader("Gestione Anagrafica Studenti")

    if not lista_classi:
      st.warning(
          "Crea prima almeno una classe nella scheda 'Gestione Classi'."
      )
    else:
      classe_filtro = st.selectbox(
          "Seleziona Classe per Anagrafica", ["Tutte"] + lista_classi
      )

      with st.expander("➕ Inserisci Nuovo Alunno", expanded=False):
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
            scuola_prec = st.selectbox(
                "Scuola di provenienza",
                lista_scuole if lista_scuole else ["Nessuna"],
            )
            provenienza_orig = st.text_input(
                "Provenienza originaria (Paese/Città)"
            )
            famiglia_comunita = st.selectbox(
                "Famiglia / Comunità", ["Famiglia", "Comunità", "Altro"]
            )

          motivo_dim = st.text_input(
              "Motivo dimissione (lascia vuoto se attivo)"
          )
          dettagli_app = st.text_area(
              "Dettagli apprendimento / BES / DSA (opzionale)"
          )
          nota_testo = st.text_area("Note generali sull'alunno")

          submitted = st.form_submit_button("Salva Alunno")
          if submitted and nome and cognome:
            nuovo_id = str(int(datetime.datetime.now().timestamp()))
            nuovo_alunno_dict = {
                "id": nuovo_id,
                "nome": nome,
                "cognome": cognome,
                "classe": classe_assegnata,
                "data_inserimento": data_ins,
                "motivo_dimissione": motivo_dim,
                "scuola_prec": scuola_prec,
                "provenienza_orig": provenienza_orig,
                "famiglia_comunita": famiglia_comunita,
                "dettagli_apprendi": dettagli_app,
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
                "famiglia_comunita",
                "scuola_prec",
            ]
            if c in df_mostra.columns
        ]
        st.dataframe(df_mostra[colonne_visibili], use_container_width=True)
      else:
        st.info("Nessun alunno trovato per i filtri selezionati.")

  # ==========================================
  # 3. REGISTRO PRESENZE (Foglio: Presenze -> alunno_id, data, stato)
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

          if st.form_submit_button("Registra Presenze Giornaliere"):
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

            nuove_presenze_list = [
                {
                    "alunno_id": str(al_id),
                    "data": data_registro,
                    "stato": stato,
                }
                for al_id, stato in stili_presenza.items()
            ]
            df_presenze = pd.concat(
                [df_presenze, pd.DataFrame(nuove_presenze_list)],
                ignore_index=True,
            )
            salva_tabella(df_presenze, "Presenze")
            st.success("Presenze salvate correttamente!")
      else:
        st.warning("Nessun alunno presente in questa classe.")

  # ==========================================
  # 4. VOTI & NOTE (Foglio Voti: alunno_id, materia, voto, data, nota_voto | Foglio Note: alunno_id, tipo, descrizione, data)
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
              nota_voto = st.text_input("Nota sul voto (opzionale)")

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
            desc_nota = st.text_area("Descrizione della nota")
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
      else:
        st.warning("Seleziona una classe con alunni.")

  # ==========================================
  # 5. TABELLE & CONFIGURAZIONE (Materie: Materia, Docente, CoDocente | Scuole: Scuola, Comune, Provincia, Telefono, Telefono2, Email)
  # ==========================================
  with tabs[4]:
    st.subheader("Gestione Tabelle di Configurazione")

    col_t1, col_t2 = st.columns(2)

    with col_t1:
      st.markdown("### 📚 Gestione Materie")
      with st.form("form_materia"):
        materia_nome = st.text_input("Nome Materia")
        docente_nome = st.text_input("Docente")
        codocente_nome = st.text_input("CoDocente (opzionale)")
        if st.form_submit_button("Aggiungi Materia"):
          if materia_nome and materia_nome not in lista_materie:
            nuova_mat = {
                "Materia": materia_nome,
                "Docente": docente_nome,
                "CoDocente": codocente_nome,
            }
            df_materie = pd.concat(
                [df_materie, pd.DataFrame([nuova_mat])], ignore_index=True
            )
            salva_tabella(df_materie, "Materie")
            st.success("Materia aggiunta!")
            st.rerun()

      st.write("Materie attuali:")
      if not df_materie.empty:
        st.dataframe(df_materie, use_container_width=True)

    with col_t2:
      st.markdown("### 🏫 Scuole di Provenienza")
      with st.form("form_scuola"):
        scuola_nome = st.text_input("Nome Scuola")
        comune = st.text_input("Comune")
        provincia = st.text_input("Provincia")
        telefono = st.text_input("Telefono")
        telefono2 = st.text_input("Telefono 2")
        email = st.text_input("Email")
        if st.form_submit_button("Aggiungi Scuola"):
          if scuola_nome:
            nuova_scu = {
                "Scuola": scuola_nome,
                "Comune": comune,
                "Provincia": provincia,
                "Telefono": telefono,
                "Telefono2": telefono2,
                "Email": email,
            }
            df_scuole = pd.concat(
                [df_scuole, pd.DataFrame([nuova_scu])], ignore_index=True
            )
            salva_tabella(df_scuole, "Scuole")
            st.success("Scuola aggiunta!")
            st.rerun()

      st.write("Scuole attuali:")
      if not df_scuole.empty:
        st.dataframe(df_scuole, use_container_width=True)


if __name__ == "__main__":
  main()
