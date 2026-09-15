import datetime
import json
import os
import pandas as pd
import streamlit as st

# Impostazione pagina
st.set_page_config(page_title="RegistrOne - Registro di Classe", layout="wide")

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


# --- CONNESSIONE GOOGLE SHEETS CON CACHE ---
def get_gsheets_connection():
  try:
    return st.connection("gsheets_registrone", type="GSheetsConnection")
  except Exception as e:
    st.error(f"Errore di connessione a Google Sheets: {e}")
    return None


@st.cache_data(ttl=60)
def carica_dati_gsheets():
  conn = get_gsheets_connection()
  if not conn:
    return None
  try:
    # Legge i vari fogli di lavoro
    classi_df = conn.read(worksheet="Classi", usecols=[0], ttl=0)
    materie_df = conn.read(worksheet="Materie", usecols=[0], ttl=0)
    scuole_df = conn.read(worksheet="Scuole", usecols=[0], ttl=0)
    alunni_df = conn.read(worksheet="Alunni", ttl=0)
    presenze_df = conn.read(worksheet="Presenze", ttl=0)
    voti_df = conn.read(worksheet="Voti", ttl=0)
    note_df = conn.read(worksheet="Note", ttl=0)

    return {
        "classi": (
            classi_df["Classe"].dropna().astype(str).tolist()
            if not classi_df.empty and "Classe" in classi_df.columns
            else []
        ),
        "materie": (
            materie_df["Materia"].dropna().astype(str).tolist()
            if not materie_df.empty and "Materia" in materie_df.columns
            else ["Informatica", "Laboratorio", "Sistemi e Reti"]
        ),
        "scuole_provenienza": (
            scuole_df["Scuola"].dropna().astype(str).tolist()
            if not scuole_df.empty and "Scuola" in scuole_df.columns
            else [
                "Scuola Media Statale",
                "Altro Istituto Professionale",
                "Liceo Scientifico",
            ]
        ),
        "alunni": (
            alunni_df.to_dict(orient="records")
            if not alunni_df.empty
            else []
        ),
        "presenze": (
            presenze_df.to_dict(orient="records")
            if not presenze_df.empty
            else []
        ),
        "voti": voti_df.to_dict(orient="records") if not voti_df.empty else [],
        "note": note_df.to_dict(orient="records") if not note_df.empty else [],
    }
  except Exception as e:
    # Fallback o struttura iniziale se i fogli sono vuoti
    return {
        "classi": [],
        "materie": ["Informatica", "Laboratorio", "Sistemi e Reti"],
        "scuole_provenienza": [
            "Scuola Media Statale",
            "Altro Istituto Professionale",
            "Liceo Scientifico",
        ],
        "alunni": [],
        "presenze": [],
        "voti": [],
        "note": [],
    }


def salva_dati(data):
  conn = get_gsheets_connection()
  if not conn:
    st.error("Impossibile salvare: connessione non disponibile.")
    return

  try:
    # Scrittura atomica sui rispettivi fogli Google Sheets
    conn.update(
        worksheet="Classi", data=pd.DataFrame({"Classe": data["classi"]})
    )
    conn.update(
        worksheet="Materie", data=pd.DataFrame({"Materia": data["materie"]})
    )
    conn.update(
        worksheet="Scuole",
        data=pd.DataFrame({"Scuola": data["scuole_provenienza"]}),
    )
    conn.update(
        worksheet="Alunni",
        data=pd.DataFrame(data["alunni"])
        if data["alunni"]
        else pd.DataFrame(
            columns=[
                "id",
                "nome",
                "cognome",
                "classe",
                "data_inserimento",
                "dimesso",
                "motivo_dimissione",
                "altra_scuola",
                "scuola_prec",
                "parla_italiano",
                "provenienza_orig",
                "famiglia_comunita",
                "problemi_apprendimento",
                "dettagli_apprendimento",
                "nota_testo",
            ]
        ),
    )
    conn.update(
        worksheet="Presenze",
        data=pd.DataFrame(data["presenze"])
        if data["presenze"]
        else pd.DataFrame(columns=["alunno_id", "data", "stato"]),
    )
    conn.update(
        worksheet="Voti",
        data=pd.DataFrame(data["voti"])
        if data["voti"]
        else pd.DataFrame(
            columns=["alunno_id", "materia", "voto", "data", "nota_voto"]
        ),
    )
    conn.update(
        worksheet="Note",
        data=pd.DataFrame(data["note"])
        if data["note"]
        else pd.DataFrame(
            columns=["alunno_id", "tipo", "descrizione", "data"]
        ),
    )

    # Pulisce la cache per ricaricare i dati aggiornati
    st.cache_data.clear()
  except Exception as e:
    st.error(f"Errore durante il salvataggio su Google Sheets: {e}")


db = carica_dati_gsheets()
if db is None:
  st.stop()

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
    if db["classi"]:
      for idx, c in enumerate(db["classi"]):
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
      if nuova_classe and nuova_classe not in db["classi"]:
        db["classi"].append(nuova_classe)
        salva_dati(db)
        st.success(f"Classe {nuova_classe} aggiunta con successo!")
        st.rerun()
      else:
        st.error("Inserisci un nome valido o già esistente.")

  # Sezione di Modifica ed Eliminazione Classi esistenti
  if db["classi"]:
    st.markdown("---")
    st.markdown("### Modifica o Elimina Classe Esistente")
    classe_selezionata_gestione = st.selectbox(
        "Seleziona classe", db["classi"], key="ges_cl"
    )

    col_m1, col_m2 = st.columns(2)
    with col_m1:
      nuovo_nome_classe = st.text_input(
          "Rinomina classe", value=classe_selezionata_gestione
      )
      if st.button("Aggiorna Nome Classe"):
        if nuovo_nome_classe and nuovo_nome_classe not in db["classi"]:
          vecchio_nome = classe_selezionata_gestione
          idx = db["classi"].index(vecchio_nome)
          db["classi"][idx] = nuovo_nome_classe
          for al in db["alunni"]:
            if al["classe"] == vecchio_nome:
              al["classe"] = nuovo_nome_classe
          salva_dati(db)
          st.success("Classe aggiornata con successo!")
          st.rerun()
        else:
          st.error("Nome non valido o già esistente.")

    with col_m2:
      st.write("")
      st.write("")
      if st.button("Elimina Classe", type="primary"):
        alunni_nella_classe = [
            a for a in db["alunni"] if a["classe"] == classe_selezionata_gestione
        ]
        if alunni_nella_classe:
          st.error(
              "Impossibile eliminare la classe: contiene ancora studenti"
              " iscritti. Sposta o elimina prima gli studenti."
          )
        else:
          db["classi"].remove(classe_selezionata_gestione)
          salva_dati(db)
          st.success("Classe eliminata.")
          st.rerun()

# ==========================================
# 2. ANAGRAFICA ALUNNI
# ==========================================
with tabs[1]:
  st.subheader("Gestione Anagrafica Studenti")

  if not db["classi"]:
    st.warning(
        "Prima di inserire alunni, devi creare almeno una classe nella scheda"
        " 'Gestione Classi'."
    )
  else:
    classe_filtro = st.selectbox(
        "Seleziona Classe per Anagrafica", ["Tutte"] + db["classi"]
    )

    with st.expander(
        "➕ Inserisci Nuovo Alunno / Modifica Scheda", expanded=False
    ):
      with st.form("form_alunno"):
        col_a, col_b = st.columns(2)
        with col_a:
          nome = st.text_input("Nome")
          cognome = st.text_input("Cognome")
          classe_assegnata = st.selectbox("Classe", db["classi"])
          data_ins = st.date_input(
              "Data Inserimento", datetime.date.today()
          ).strftime("%Y-%m-%d")

        with col_b:
          altra_scuola = st.checkbox("Provenienza da altra scuola")
          scuola_prec = st.selectbox(
              "Scuola di provenienza", db["scuole_provenienza"]
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
          nuovo_alunno = {
              "id": str(len(db["alunni"]) + 1)
              + "_"
              + datetime.datetime.now().strftime("%s"),
              "nome": nome,
              "cognome": cognome,
              "classe": classe_assegnata,
              "data_inserimento": data_ins,
              "dimesso": dimesso,
              "motivo_dimissione": motivo_dim if dimesso else "",
              "altra_scuola": altra_scuola,
              "scuola_prec": scuola_prec if altra_scuola else "",
              "parla_italiano": parla_italiano,
              "provenienza_orig": provenienza_orig,
              "famiglia_comunita": famiglia_comunita,
              "problemi_apprendimento": problemi_apprendimento,
              "dettagli_apprendimento": dettagli_app
              if problemi_apprendimento
              else "",
              "nota_testo": nota_testo,
          }
          db["alunni"].append(nuovo_alunno)
          salva_dati(db)
          st.success(f"Alunno {nome} {cognome} salvato con successo!")
          st.rerun()

    st.markdown("### Elenco Studenti Registrati")
    alunni_filtrati = (
        db["alunni"]
        if classe_filtro == "Tutte"
        else [a for a in db["alunni"] if a["classe"] == classe_filtro]
    )

    if alunni_filtrati:
      df_alunni = pd.DataFrame(alunni_filtrati)
      st.dataframe(
          df_alunni[
              [
                  "nome",
                  "cognome",
                  "classe",
                  "dimesso",
                  "parla_italiano",
                  "famiglia_comunita",
              ]
          ],
          use_container_width=True,
      )

      st.markdown("---")
      scelta_alunno = st.selectbox(
          "Seleziona studente per dettagli o eliminazione",
          options=alunni_filtrati,
          format_func=lambda x: f"{x['cognome']} {x['nome']} ({x['classe']})",
      )
      if scelta_alunno:
        with st.expander(
            f"Scheda Dettaglio: {scelta_alunno['cognome']} {scelta_alunno['nome']}"
        ):
          st.write(
              f"**Data Inserimento:** {scelta_alunno.get('data_inserimento', 'N/D')}"
          )
          st.write(
              f"**Provenienza Altra Scuola:** {'Sì (' + str(scelta_alunno.get('scuola_prec','')) + ')' if scelta_alunno.get('altra_scuola') else 'No'}"
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
              f"**Problemi Apprendimento:** {'Sì - ' + str(scelta_alunno.get('dettagli_apprendimento','')) if scelta_alunno.get('problemi_apprendimento') else 'No'}"
          )
          st.write(
              f"**Dimesso:** {'Sì (Motivo: ' + str(scelta_alunno.get('motivo_dimissione','')) + ')' if scelta_alunno.get('dimesso') else 'No'}"
          )
          st.info(f"**Note:** {scelta_alunno.get('nota_testo', '')}")

          if st.button("Elimina Alunno", type="primary"):
            db["alunni"] = [
                a for a in db["alunni"] if str(a["id"]) != str(scelta_alunno["id"])
            ]
            salva_dati(db)
            st.success("Alunno eliminato.")
            st.rerun()
    else:
      st.info("Nessun alunno trovato per i filtri selezionati.")

# ==========================================
# 3. REGISTRO PRESENZE
# ==========================================
with tabs[2]:
  st.subheader("Registro Presenze e Assenze Giornaliere")

  if not db["classi"]:
    st.warning("Crea prima almeno una classe.")
  else:
    c_sel_cl, c_sel_dt = st.columns(2)
    with c_sel_cl:
      classe_pres = st.selectbox(
          "Seleziona Classe per Registro",
          db["classi"],
          key="pres_classe_selezionata",
      )
    with c_sel_dt:
      data_registro = st.date_input(
          "Data Registro", datetime.date.today()
      ).strftime("%Y-%m-%d")

    alunni_classe = [a for a in db["alunni"] if a["classe"] == classe_pres]

    if alunni_classe:
      st.markdown(f"### Appello del giorno: {data_registro}")
      with st.form("form_appello"):
        stili_presenza = {}
        for al in alunni_classe:
          esistente = next(
              (
                  p
                  for p in db["presenze"]
                  if str(p["alunno_id"]) == str(al["id"])
                  and str(p["data"]) == data_registro
              ),
              None,
          )
          idx_default = 0
          if esistente:
            if esistente["stato"] == "Assente":
              idx_default = 1
            elif esistente["stato"] == "Giustificato":
              idx_default = 2

          stili_presenza[al["id"]] = st.selectbox(
              f"{al['cognome']} {al['nome']}",
              ["Presente", "Assente", "Giustificato"],
              index=idx_default,
              key=f"pres_{al['id']}",
          )

        salva_appello = st.form_submit_button("Registra Presenze Giornaliere")
        if salva_appello:
          db["presenze"] = [
              p
              for p in db["presenze"]
              if not (
                  str(p["data"]) == data_registro
                  and str(p["alunno_id"])
                  in [str(a["id"]) for a in alunni_classe]
              )
          ]
          for al_id, stato in stili_presenza.items():
            db["presenze"].append(
                {"alunno_id": al_id, "data": data_registro, "stato": stato}
            )
          salva_dati(db)
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
        for al in alunni_classe:
          tot_assenze = sum(
              1
              for p in db["presenze"]
              if str(p["alunno_id"]) == str(al["id"])
              and p["stato"] == "Assente"
              and data_inizio.strftime("%Y-%m-%d")
              <= str(p["data"])
              <= data_fine.strftime("%Y-%m-%d")
          )
          report_assenze.append({
              "Alunno": f"{al['cognome']} {al['nome']}",
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

  if not db["classi"]:
    st.warning("Crea prima almeno una classe.")
  else:
    classe_voti = st.selectbox(
        "Seleziona Classe", db["classi"], key="classe_voti_sel"
    )
    alunni_voti = [a for a in db["alunni"] if a["classe"] == classe_voti]

    if alunni_voti:
      tab_v, tab_n = st.tabs(
          ["📊 Inserimento Voti", "📌 Note di Merito / Demerito"]
      )

      with tab_v:
        with st.form("form_voto"):
          alunno_selezionato = st.selectbox(
              "Studente",
              alunni_voti,
              format_func=lambda x: f"{x['cognome']} {x['nome']}",
          )
          col_v1, col_v2 = st.columns(2)
          with col_v1:
            materia_scelta = st.selectbox("Materia", db["materie"])
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
            db["voti"].append({
                "alunno_id": alunno_selezionato["id"],
                "materia": materia_scelta,
                "voto": voto_num,
                "data": data_voto,
                "nota_voto": nota_voto,
            })
            salva_dati(db)
            st.success("Voto inserito con successo!")

        st.markdown("### Storico Voti Studente Selezionato")
        st_sel_storico = st.selectbox(
            "Seleziona studente per visualizzare i voti",
            alunni_voti,
            format_func=lambda x: f"{x['cognome']} {x['nome']}",
            key="storico_voti",
        )
        voti_studente = [
            v
            for v in db["voti"]
            if str(v["alunno_id"]) == str(st_sel_storico["id"])
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
              format_func=lambda x: f"{x['cognome']} {x['nome']}",
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
            db["note"].append({
                "alunno_id": alunno_nota["id"],
                "tipo": tipo_nota,
                "descrizione": desc_nota,
                "data": data_nota,
            })
            salva_dati(db)
            st.success("Nota registrata!")

        st.markdown("### Elenco Note per Studente")
        st_nota_storico = st.selectbox(
            "Seleziona studente per note",
            alunni_voti,
            format_func=lambda x: f"{x['cognome']} {x['nome']}",
            key="storico_note",
        )
        note_studente = [
            n
            for n in db["note"]
            if str(n["alunno_id"]) == str(st_nota_storico["id"])
        ]
        if note_studente:
          for n in note_studente:
            if n["tipo"] == "Merito":
              st.success(f"[{n['data']}] **{n['tipo']}**: {n['descrizione']}")
            else:
              st.error(f"[{n['data']}] **{n['tipo']}**: {n['descrizione']}")
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
      if nuova_materia and nuova_materia not in db["materie"]:
        db["materie"].append(nuova_materia)
        salva_dati(db)
        st.success("Materia aggiunta!")
        st.rerun()

    st.write("Materie attuali:")
    for m in db["materie"]:
      st.write(f"- {m}")

  with col_t2:
    st.markdown("### 🏫 Scuole di Provenienza")
    nuova_scuola = st.text_input("Nome Scuola")
    if st.button("Aggiungi Scuola"):
      if nuova_scuola and nuova_scuola not in db["scuole_provenienza"]:
        db["scuole_provenienza"].append(nuova_scuola)
        salva_dati(db)
        st.success("Scuola aggiunta!")
        st.rerun()

    st.write("Scuole attuali:")
    for s in db["scuole_provenienza"]:
      st.write(f"- {s}")
