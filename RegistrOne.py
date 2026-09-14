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

    /* Container generali */
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

# FILE DI PERSISTENZA LOCALE (Sostituibile con gspread se si collega a Google Sheets)
DB_FILE = "registrone_db.json"


def carica_dati():
  if os.path.exists(DB_FILE):
    try:
      with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)
    except:
      pass
  # Struttura dati iniziale di default
  return {
      "classi": ["1A Informatica", "2A Informatica", "3A Informatica"],
      "materie": ["Informatica", "Laboratorio", "Sistemi e Reti"],
      "scuole_provenienza": [
          "Scuola Media Statale",
          "Altro Istituto Professionale",
          "Liceo Scientifico",
      ],
      "alunni": [],  # [{id, nome, cognome, classe, nota_testo, data_inserimento, dimesso, motivo_dimissione, altra_scuola, scuola_prec, parla_italiano, provenienza_orig, famiglia_comunita, problemi_apprendimento, dettagli_apprendimento}]
      "presenze": (
          []
      ),  # [{alunno_id, data (YYYY-MM-DD), stato ('Presente'/'Assente'/'Giustificato')}]
      "voti": (
          []
      ),  # [{alunno_id, data, materia, voto (3-10), nota_voto}]
      "note": (
          []
      ),  # [{alunno_id, data, tipo ('Merito'/'Demerito'), descrizione}]
  }


def salva_dati(data):
  with open(DB_FILE, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=4)


db = carica_dati()

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
      for c in db["classi"]:
        st.info(f"📁 **{c}**")
    else:
      st.warning("Nessuna classe inserita.")

  with col2:
    st.markdown("### Aggiungi Classe")
    nuova_classe = st.text_input("Nome Classe (es. 4A Informatica)")
    if st.button("Crea Classe"):
      if nuova_classe and nuova_classe not in db["classi"]:
        db["classi"].append(nuova_classe)
        salva_dati(db)
        st.success(f"Classe {nuova_classe} aggiunta con successo!")
        st.rerun()
      else:
        st.error("Inserisci un nome valido o già esistente.")

# ==========================================
# 2. ANAGRAFICA ALUNNI
# ==========================================
with tabs[1]:
  st.subheader("Gestione Anagrafica Studenti")

  # Selezione classe per filtraggio rapido
  classe_filtro = st.selectbox(
      "Seleziona Classe per Anagrafica", ["Tutte"] + db["classi"]
  )

  with st.expander("➕ Inserisci Nuovo Alunno / Modifica Scheda", expanded=False):
    with st.form("form_alunno"):
      col_a, col_b = st.columns(2)
      with col_a:
        nome = st.text_input("Nome")
        cognome = st.text_input("Cognome")
        classe_assegnata = st.selectbox(
            "Classe", db["classi"] if db["classi"] else ["Nessuna"]
        )
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
        famiglia_comunita = st.selectbox("Situazione Abitativa", ["Famiglia", "Comunità", "Altro"])
        dimesso = st.checkbox("Studente Dimesso")
        motivo_dim = st.text_input(
            "Motivo dimissione (se attivo)",
            disabled=not dimesso,
        )

      with col_d:
        problemi_apprendimento = st.checkbox("Problemi di apprendimento / DSA / BES")
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

  # Tabella Visualizzazione e Gestione Alunni
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

    # Sezione di dettaglio e rimozione rapida
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
            f"**Provenienza Altra Scuola:** {'Sì (' + scelta_alunno.get('scuola_prec','') + ')' if scelta_alunno.get('altra_scuola') else 'No'}"
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
            f"**Problemi Apprendimento:** {'Sì - ' + scelta_alunno.get('dettagli_apprendimento','') if scelta_alunno.get('problemi_apprendimento') else 'No'}"
        )
        st.write(f"**Dimesso:** {'Sì (Motivo: ' + scelta_alunno.get('motivo_dimissione','') + ')' if scelta_alunno.get('dimesso') else 'No'}")
        st.info(f"**Note:** {scelta_alunno.get('nota_testo', '')}")

        if st.button("Elimina Alunno", type="primary"):
          db["alunni"] = [
              a for a in db["alunni"] if a["id"] != scelta_alunno["id"]
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
        # Cerca stato esistente per questa data
        esistente = next(
            (
                p
                for p in db["presenze"]
                if p["alunno_id"] == al["id"] and p["data"] == data_registro
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
        # Rimuovi vecchie presenze di quel giorno per quella classe e salva le nuove
        db["presenze"] = [
            p
            for p in db["presenze"]
            if not (
                p["data"] == data_registro
                and p["alunno_id"] in [a["id"] for a in alunni_classe]
            )
        ]
        for al_id, stato in stili_presenza.items():
          db["presenze"].append(
              {"alunno_id": al_id, "data": data_registro, "stato": stato}
          )
        salva_dati(db)
        st.success("Presenze salvate correttamente!")

    # Sezione Ricerca Assenze da Data a Data
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
          f"**Report assenze dal {data_inizio} al {data_fine} per la classe {classe_pres}:**"
      )
      report_assenze = []
      for al in alunni_classe:
        # Conta le assenze nell'intervallo
        tot_assenze = sum(
            1
            for p in db["presenze"]
            if p["alunno_id"] == al["id"]
            and p["stato"] == "Assente"
            and data_inizio.strftime("%Y-%m-%d")
            <= p["data"]
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

  classe_voti = st.selectbox(
      "Seleziona Classe", db["classi"], key="classe_voti_sel"
  )
  alunni_voti = [a for a in db["alunni"] if a["classe"] == classe_voti]

  if alunni_voti:
    tab_v, tab_n = st.tabs(["📊 Inserimento Voti", "📌 Note di Merito / Demerito"])

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
              "Motivo / Spiegazione del voto (es. Interrogazione, Verifica scritta)"
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

      # Mostra pagella/voti studente
      st.markdown("### Storico Voti Studente Selezionato")
      st_sel_storico = st.selectbox(
          "Seleziona studente per visualizzare i voti",
          alunni_voti,
          format_func=lambda x: f"{x['cognome']} {x['nome']}",
          key="storico_voti",
      )
      voti_studente = [
          v for v in db["voti"] if v["alunno_id"] == st_sel_storico["id"]
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
          n for n in db["note"] if n["alunno_id"] == st_nota_storico["id"]
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
