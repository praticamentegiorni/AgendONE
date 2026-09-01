import datetime
import io
import json
import os
import pandas as pd
import streamlit as st

# Configurazione della pagina
st.set_page_config(
    page_title="Gestione Orari e Classi", page_icon="🕒", layout="wide"
)

# File di configurazione locale delle tabelle
CONFIG_FILE = "config_tabelle.json"

# Dizionario per i mesi in italiano
MESI_ITALIANI = {
    "January": "Gennaio",
    "February": "Febbraio",
    "March": "Marzo",
    "April": "Aprile",
    "May": "Maggio",
    "June": "Giugno",
    "July": "Luglio",
    "August": "Agosto",
    "September": "Settembre",
    "October": "Ottobre",
    "November": "Novembre",
    "December": "Dicembre",
}

def traduci_mese(mese_en):
    return MESI_ITALIANI.get(mese_en, mese_en)

# Parser robusto per date in formato italiano DD/MM/YYYY o ISO YYYY-MM-DD
def parse_data_italiana(val):
    if pd.isna(val) or str(val).strip() == "" or str(val).lower() == "none" or str(val).lower() == "nan":
        return pd.NaT
    val_str = str(val).strip()
    
    if "-" in val_str and len(val_str.split("-")[0]) == 4:
        try:
            return pd.to_datetime(val_str, format="%Y-%m-%d")
        except:
            pass
            
    try:
        parti = val_str.split("/")
        if len(parti) == 3:
            giorno, mese, anno = int(parti[0]), int(parti[1]), int(parti[2])
            return datetime.datetime(anno, mese, giorno)
    except:
        pass
        
    return pd.to_datetime(val_str, errors="coerce", dayfirst=True)

# Calcolo automatico delle ore tra inizio e fine
def calcola_ore(ora_inizio, ora_fine):
    try:
        t_i = datetime.datetime.strptime(str(ora_inizio).strip(), "%H:%M")
    except:
        try:
            t_i = datetime.datetime.strptime(str(ora_inizio).strip(), "%H:%M:%S")
        except:
            return 0.0
    try:
        t_f = datetime.datetime.strptime(str(ora_fine).strip(), "%H:%M")
    except:
        try:
            t_f = datetime.datetime.strptime(str(ora_fine).strip(), "%H:%M:%S")
        except:
            return 0.0
    diff = (datetime.datetime.combine(datetime.date.min, t_f.time()) - 
            datetime.datetime.combine(datetime.date.min, t_i.time())).total_seconds() / 3600.0
    return max(0.0, round(diff, 2))

# Funzione per ottenere il client gspread dai secrets di Streamlit
def get_gspread_client_and_sheet():
    try:
        import gspread
        gsheets_secrets = st.secrets["connections"]["gsheets"]
        spreadsheet_url = gsheets_secrets["spreadsheet"]
        
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
        
        client = gspread.service_account_from_dict(creds_dict)
        spreadsheet = client.open_by_url(spreadsheet_url)
        return spreadsheet.worksheet("Foglio1")
    except Exception as e:
        return None

# Funzione per sincronizzare l'evento su Google Calendar
def sincronizza_google_calendar(azione, dati_evento, evento_id_esistente=None):
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build

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

        calendar_id = gsheets_secrets.get("calendar_id", "primary")

        # Pulisci eventuale ID esistente da spazi o valori NaN
        if evento_id_esistente:
            evento_id_esistente = str(evento_id_esistente).strip()
            if evento_id_esistente.lower() in ["nan", "none", ""]:
                evento_id_esistente = None

        if azione != "elimina":
            data_str = dati_evento["Data"] # YYYY-MM-DD
            start_datetime = f"{data_str}T{dati_evento['Orario Inizio']}:00"
            end_datetime = f"{data_str}T{dati_evento['Orario Fine']}:00"

            body = {
                'summary': f"Lezione/Impegno: {dati_evento['Classe']} ({dati_evento['Modalità']})",
                'location': str(dati_evento['Sede']),
                'description': f"Note: {dati_evento['Note']}\nGestito da AgendOne",
                'start': {
                    'dateTime': start_datetime,
                    'timeZone': 'Europe/Rome',
                },
                'end': {
                    'dateTime': end_datetime,
                    'timeZone': 'Europe/Rome',
                },
            }

        if azione == "crea":
            event_result = service.events().insert(calendarId=calendar_id, body=body).execute()
            return event_result.get('id')
        elif azione == "aggiorna" and evento_id_esistente:
            service.events().update(calendarId=calendar_id, eventId=evento_id_esistente, body=body).execute()
            return evento_id_esistente
        elif azione == "aggiorna" and not evento_id_esistente:
            event_result = service.events().insert(calendarId=calendar_id, body=body).execute()
            return event_result.get('id')
        elif azione == "elimina" and evento_id_esistente:
            service.events().delete(calendarId=calendar_id, eventId=evento_id_esistente).execute()
            return None
    except Exception as e:
        st.error(f"Errore di sincronizzazione Google Calendar: {e}")
        return None

# Gestione configurazione tabelle
def carica_config():
    default_config = {
        "classi": ["Classe 1A", "Classe 2B", "Classe 3C"],
        "sedi": ["Sede Centrale", "Succursale", "Smart Working"],
        "modalita": ["Presenza", "Videolezione"],
    }
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
                if "committenti" in data and "classi" not in data:
                    data["classi"] = data.pop("committenti")
                if "luoghi" in data and "sedi" not in data:
                    data["sedi"] = data.pop("luoghi")
                for k, v in default_config.items():
                    if k not in data:
                        data[k] = v
                return data
        except:
            return default_config
    return default_config

def salva_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)

config = carica_config()

# Caricamento dati da Google Sheets
def carica_dati():
    cols_standard = ["Data", "Mese", "Orario Inizio", "Orario Fine", "Ore", "Classe", "Sede", "Modalità", "Svolto", "Note", "Calendar_ID"]
    empty_df = pd.DataFrame(columns=cols_standard)
    try:
        worksheet = get_gspread_client_and_sheet()
        if worksheet is None:
            return empty_df
        data = worksheet.get_all_records()
        if not data:
            return empty_df
        df = pd.DataFrame(data)
        
        if "Committente" in df.columns and "Classe" not in df.columns:
            df = df.rename(columns={"Committente": "Classe"})
        if "Luogo" in df.columns and "Sede" not in df.columns:
            df = df.rename(columns={"Luogo": "Sede"})
            
        if "Data" in df.columns:
            df["Data_dt"] = df["Data"].apply(parse_data_italiana)
            
            mask_valid = df["Data_dt"].notna()
            df.loc[mask_valid, "Data"] = df.loc[mask_valid, "Data_dt"].dt.strftime("%Y-%m-%d")
            df.loc[mask_valid, "Mese"] = df.loc[mask_valid, "Data_dt"].apply(
                lambda dt: traduci_mese(dt.strftime("%B")).capitalize()
            )
            
        if "Svolto" not in df.columns:
            df["Svolto"] = False
        else:
            df["Svolto"] = df["Svolto"].apply(lambda x: True if str(x).lower() in ["true", "1", "yes", "vero", "on"] else False)

        if "Calendar_ID" not in df.columns:
            df["Calendar_ID"] = ""
        else:
            df["Calendar_ID"] = df["Calendar_ID"].fillna("").astype(str)
            
        if "Ore" not in df.columns or df["Ore"].isna().all():
            df["Ore"] = df.apply(lambda r: calcola_ore(r.get("Orario Inizio"), r.get("Orario Fine")), axis=1)
            
        for c in cols_standard:
            if c not in df.columns:
                df[c] = ""
                
        return df
    except Exception as e:
        return empty_df

# Salvataggio dati su Google Sheets
def salva_dati(df_to_save):
    if "Data_dt" in df_to_save.columns:
        df_to_save = df_to_save.drop(columns=["Data_dt"])
    cols_standard = ["Data", "Mese", "Orario Inizio", "Orario Fine", "Ore", "Classe", "Sede", "Modalità", "Svolto", "Note", "Calendar_ID"]
    for c in cols_standard:
        if c not in df_to_save.columns:
            df_to_save[c] = ""
    df_to_save = df_to_save[cols_standard]
    # Sostituisci eventuali NaN/None con stringhe vuote per gspread
    df_to_save = df_to_save.fillna("")
    try:
        worksheet = get_gspread_client_and_sheet()
        if worksheet is None:
            st.error("Impossibile connettersi a Google Sheets. Verifica i Secrets.")
            return
        worksheet.clear()
        righe = [df_to_save.columns.values.tolist()] + df_to_save.values.tolist()
        worksheet.update("A1", righe)
    except Exception as e:
        st.error(f"Errore durante il salvataggio su Google Sheets: {e}")

df = carica_dati()

st.title("🕒 Gestione Orari e Classi")
st.markdown("---")

tab1, tab2, tab3 = st.tabs([
    "📝 Inserisci Attività",
    "⚙️ Gestione Tabelle & Combo",
    "📊 Archivio, Modifica, Report & Riepilogo",
])

# ================= TAB 1: INSERIMENTO =================
with tab1:
    st.subheader("Registrazione Nuova Attività")
    with st.form("form_orario", clear_on_submit=True):
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            data_selezionata = st.date_input("Giorno", value=datetime.date.today(), format="DD/MM/YYYY")
            mese_str = traduci_mese(data_selezionata.strftime("%B"))
        with col_d2:
            st.info(f"Mese di riferimento: **{mese_str}**")

        st.markdown("**Selezione Orario**")
        col_o1, col_o2, col_o3, col_o4 = st.columns(4)
        with col_o1:
            ora_i = st.selectbox("Ora Inizio", options=list(range(0, 24)), index=9)
        with col_o2:
            min_i = st.selectbox("Minuti Inizio", options=[0, 15, 30, 45], index=0)
        with col_o3:
            ora_f = st.selectbox("Ora Fine", options=list(range(0, 24)), index=18)
        with col_o4:
            min_f = st.selectbox("Minuti Fine", options=[0, 15, 30, 45], index=0)

        orario_inizio_str = f"{ora_i:02d}:{min_i:02d}"
        orario_fine_str = f"{ora_f:02d}:{min_f:02d}"
        ore_calcolate = calcola_ore(orario_inizio_str, orario_fine_str)

        st.caption(f"⏱️ Durata stimata: **{ore_calcolate} ore**")

        col_t1, col_t2, col_t3 = st.columns(3)
        with col_t1:
            classe = st.selectbox("Classe", options=config["classi"], index=0 if config["classi"] else None, key="sel_classe")
            nuova_classe_libera = st.text_input("O digita nuova classe:", placeholder="Se non è in elenco...", key="lib_classe")
        with col_t2:
            sede = st.selectbox("Sede", options=config["sedi"], index=0 if config["sedi"] else None, key="sel_sede")
            nuova_sede_libera = st.text_input("O digita nuova sede:", placeholder="Se non è in elenco...", key="lib_sede")
        with col_t3:
            modalita = st.selectbox("Modalità", options=config["modalita"], index=0 if config["modalita"] else None, key="sel_mod")
            nuovo_mod_libero = st.text_input("O digita nuova modalità:", placeholder="Se non è in elenco...", key="lib_mod")

        svolto_iniziale = st.checkbox("Impegno già svolto", value=False)
        note = st.text_area("Note / Descrizione dettagliata", placeholder="Inserisci eventuali dettagli...")

        submit_button = st.form_submit_button(label="💾 Salva Attività", use_container_width=True)

        if submit_button:
            val_classe = nuova_classe_libera.strip() if nuova_classe_libera else classe
            val_sede = nuova_sede_libera.strip() if nuova_sede_libera else sede
            val_modalita = nuovo_mod_libero.strip() if nuovo_mod_libero else modalita

            if nuova_classe_libera and nuova_classe_libera not in config["classi"]:
                config["classi"].append(nuova_classe_libera)
            if nuova_sede_libera and nuova_sede_libera not in config["sedi"]:
                config["sedi"].append(nuova_sede_libera)
            if nuovo_mod_libero and nuovo_mod_libero not in config["modalita"]:
                config["modalita"].append(nuovo_mod_libero)
            salva_config(config)

            dati_evento = {
                "Data": data_selezionata.strftime("%Y-%m-%d"),
                "Orario Inizio": orario_inizio_str,
                "Orario Fine": orario_fine_str,
                "Classe": val_classe,
                "Sede": val_sede,
                "Modalità": val_modalita,
                "Note": note
            }
            
            cal_id = sincronizza_google_calendar("crea", dati_evento)

            nuovo_dato = pd.DataFrame({
                "Data": [data_selezionata.strftime("%Y-%m-%d")],
                "Mese": [mese_str],
                "Orario Inizio": [orario_inizio_str],
                "Orario Fine": [orario_fine_str],
                "Ore": [ore_calcolate],
                "Classe": [val_classe],
                "Sede": [val_sede],
                "Modalità": [val_modalita],
                "Svolto": [svolto_iniziale],
                "Note": [note],
                "Calendar_ID": [str(cal_id) if cal_id else ""]
            })

            df = pd.concat([df, nuovo_dato], ignore_index=True)
            salva_dati(df)
            st.success("Attività salvata e sincronizzata con Google Calendar!")
            st.rerun()

# ================= TAB 2: GESTIONE TABELLE =================
with tab2:
    st.subheader("Amministrazione Voci e Tabelle")
    def gestisci_tabella_avanzata(nome_tabella, lista_voci):
        st.markdown(f"### {nome_tabella.capitalize()}")
        nuovo = st.text_input(f"Nuovo {nome_tabella[:-1]}", key=f"add_{nome_tabella}")
        if st.button(f"Aggiungi", key=f"btn_add_{nome_tabella}"):
            if nuovo and nuovo not in lista_voci:
                lista_voci.append(nuovo)
                salva_config(config)
                st.success(f"Aggiunto: {nuovo}")
                st.rerun()
        st.markdown("---")
        for i, voce in enumerate(list(lista_voci)):
            c_mod, c_del = st.columns([3, 1])
            voce_modificata = c_mod.text_input(f"Modifica {i}", value=voce, key=f"edit_{nome_tabella}_{i}")
            if c_del.button("🗑️", key=f"del_{nome_tabella}_{i}"):
                lista_voci.remove(voce)
                salva_config(config)
                st.success("Voce eliminata!")
                st.rerun()
            if voce_modificata != voce and voce_modificata:
                if voce_modificata not in lista_voci:
                    lista_voci[i] = voce_modificata
                    salva_config(config)
                    st.success("Voce aggiornata!")
                    st.rerun()

    col_g1, col_g2, col_g3 = st.columns(3)
    with col_g1:
        gestisci_tabella_avanzata("classi", config["classi"])
    with col_g2:
        gestisci_tabella_avanzata("sedi", config["sedi"])
    with col_g3:
        gestisci_tabella_avanzata("modalita", config["modalita"])

# ================= TAB 3: ARCHIVIO, MODIFICA, REPORT & RIEPILOGO =================
with tab3:
    st.subheader("Storico, Modifica e Gestione Appuntamenti")

    if not df.empty:
        df_vis = df.copy()
        df_vis["ID_originale"] = df_vis.index
        
        if "Data" in df_vis.columns:
            df_vis["Data_dt"] = df_vis["Data"].apply(parse_data_italiana)
            df_vis["Mese"] = df_vis["Data_dt"].apply(lambda dt: traduci_mese(dt.strftime("%B")).capitalize() if pd.notnull(dt) else "")
            df_vis["Data"] = df_vis["Data_dt"].dt.strftime("%d/%m/%Y").fillna(df_vis["Data"])
            
            df_vis["Ore"] = df_vis.apply(lambda r: calcola_ore(r.get("Orario Inizio"), r.get("Orario Fine")), axis=1)
            df_vis = df_vis.sort_values(by=["Data_dt", "Orario Inizio"], ascending=[True, True])
            
            cols = ["Data"] + [c for c in df_vis.columns if c not in ["Data", "Data_dt", "ID_originale", "Calendar_ID"]]
            df_vis = df_vis[cols + ["ID_originale"]]

        filtro = st.text_input("🔍 Cerca rapidamente nell'archivio:", placeholder="Filtra per parole chiave...")
        df_mostra = df_vis.copy()
        if filtro:
            df_mostra = df_mostra[df_mostra.apply(lambda r: r.astype(str).str.contains(filtro, case=False).any(), axis=1)]

        df_mostra.insert(0, "Seleziona", False)
        df_mostra.insert(1, "ID", df_mostra["ID_originale"])
        df_mostra = df_mostra.drop(columns=["ID_originale"])

        def colora_righe_tabella(row):
            svolto = row.get("Svolto", False)
            if svolto:
                return ['background-color: #2b2b2b; color: #7f7f7f; text-decoration: line-through'] * len(row)
            mod = str(row.get("Modalità", "")).lower()
            if "presenza" in mod:
                return ['background-color: #1c3d73; color: #ffffff'] * len(row)
            elif "video" in mod:
                return ['background-color: #155c32; color: #ffffff'] * len(row)
            return [''] * len(row)

        df_styled = df_mostra.style.apply(colora_righe_tabella, axis=1)

        df_editato = st.data_editor(
            df_styled,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Seleziona": st.column_config.CheckboxColumn(required=True),
                "ID": st.column_config.NumberColumn(disabled=True),
                "Svolto": st.column_config.CheckboxColumn(required=True),
                "Ore": st.column_config.NumberColumn(format="%.2f h", disabled=True),
            }
        )

        modificato = False
        for _, riga_ed in df_editato.iterrows():
            idx_orig = int(riga_ed["ID"])
            val_nuovo_svolto = bool(riga_ed["Svolto"])
            if df.loc[idx_orig, "Svolto"] != val_nuovo_svolto:
                df.loc[idx_orig, "Svolto"] = val_nuovo_svolto
                modificato = True
        if modificato:
            salva_dati(df)
            st.rerun()

        righe_selezionate = df_editato[df_editato["Seleziona"] == True]["ID"].tolist()

        col_act1, col_act2 = st.columns(2)
        with col_act1:
            if st.button("🗑️ Elimina Selezionati", type="primary", use_container_width=True):
                if righe_selezionate:
                    for r_idx in righe_selezionate:
                        cal_id_esistente = str(df.loc[r_idx, "Calendar_ID"]) if "Calendar_ID" in df.columns else ""
                        if cal_id_esistente and cal_id_esistente.lower() not in ["nan", "none", ""]:
                            sincronizza_google_calendar("elimina", {}, cal_id_esistente)
                    df = df.drop(righe_selezionate).reset_index(drop=True)
                    salva_dati(df)
                    st.success("Righe eliminate e rimosse da Calendar!")
                    st.rerun()
                else:
                    st.warning("Seleziona almeno un appuntamento da eliminare.")
        with col_act2:
            if st.button("📋 Duplica Selezionato", use_container_width=True):
                if len(righe_selezionate) == 1:
                    riga_idx = righe_selezionate[0]
                    nuova_riga = df.loc[riga_idx].copy()
                    if "Note" in nuova_riga and pd.notnull(nuova_riga["Note"]) and str(nuova_riga["Note"]).strip() != "":
                        nuova_riga["Note"] = str(nuova_riga["Note"]) + " (Copia)"
                    else:
                        nuova_riga["Note"] = "Copia"
                    
                    dati_evento = {
                        "Data": str(nuova_riga["Data"]),
                        "Orario Inizio": str(nuova_riga["Orario Inizio"]),
                        "Orario Fine": str(nuova_riga["Orario Fine"]),
                        "Classe": str(nuova_riga["Classe"]),
                        "Sede": str(nuova_riga["Sede"]),
                        "Modalità": str(nuova_riga["Modalità"]),
                        "Note": str(nuova_riga["Note"])
                    }
                    cal_id = sincronizza_google_calendar("crea", dati_evento)
                    nuova_riga["Calendar_ID"] = str(cal_id) if cal_id else ""
                    
                    df = pd.concat([df, pd.DataFrame([nuova_riga])], ignore_index=True)
                    salva_dati(df)
                    st.success("Appuntamento duplicato e aggiunto a Calendar!")
                    st.rerun()
                elif len(righe_selezionate) > 1:
                    st.warning("Seleziona un solo appuntamento alla volta per la duplicazione rapida.")
                else:
                    st.warning("Seleziona un appuntamento da duplicare.")

        st.markdown("---")

        if len(righe_selezionate) == 1:
            riga_idx = righe_selezionate[0]
            riga_corrente = df.loc[riga_idx]

            st.markdown(f"### ✏️ Modifica Appuntamento (Riga ID {riga_idx})")
            with st.form("form_modifica_multipla"):
                try:
                    data_default = datetime.datetime.strptime(str(riga_corrente["Data"]), "%Y-%m-%d").date()
                except:
                    data_default = datetime.date.today()

                try:
                    parti_i = str(riga_corrente["Orario Inizio"]).split(":")
                    h_def_i, m_def_i = int(parti_i[0]), int(parti_i[1])
                except:
                    h_def_i, m_def_i = 9, 0

                try:
                    parti_f = str(riga_corrente["Orario Fine"]).split(":")
                    h_def_f, m_def_f = int(parti_f[0]), int(parti_f[1])
                except:
                    h_def_f, m_def_f = 18, 0

                mod_data = st.date_input("Data", value=data_default, format="DD/MM/YYYY")

                c_mo1, c_mo2, c_mo3, c_mo4 = st.columns(4)
                with c_mo1:
                    mod_ora_i = st.selectbox("Ora Inizio", options=list(range(0, 24)), index=h_def_i if h_def_i in range(0, 24) else 9)
                with c_mo2:
                    mod_min_i = st.selectbox("Minuti Inizio", options=[0, 15, 30, 45], index=[0, 15, 30, 45].index(m_def_i) if m_def_i in [0, 15, 30, 45] else 0)
                with c_mo3:
                    mod_ora_f = st.selectbox("Ora Fine", options=list(range(0, 24)), index=h_def_f if h_def_f in range(0, 24) else 18)
                with c_mo4:
                    mod_min_f = st.selectbox("Minuti Fine", options=[0, 15, 30, 45], index=[0, 15, 30, 45].index(m_def_f) if m_def_f in [0, 15, 30, 45] else 0)

                mod_orario_i_str = f"{mod_ora_i:02d}:{mod_min_i:02d}"
                mod_orario_f_str = f"{mod_ora_f:02d}:{mod_min_f:02d}"
                mod_ore_calc = calcola_ore(mod_orario_i_str, mod_orario_f_str)

                mod_classe = st.text_input("Classe", value=str(riga_corrente["Classe"]))
                mod_sede = st.text_input("Sede", value=str(riga_corrente["Sede"]))
                mod_modalita = st.text_input("Modalità", value=str(riga_corrente["Modalità"]))
                
                svolto_corrente = bool(riga_corrente["Svolto"]) if "Svolto" in riga_corrente else False
                mod_svolto = st.checkbox("Impegno svolto", value=svolto_corrente)
                
                mod_note = st.text_area("Note", value=str(riga_corrente["Note"]))

                if st.form_submit_button("💾 Salva Modifiche", use_container_width=True):
                    df.loc[riga_idx, "Data"] = mod_data.strftime("%Y-%m-%d")
                    df.loc[riga_idx, "Mese"] = traduci_mese(mod_data.strftime("%B"))
                    df.loc[riga_idx, "Orario Inizio"] = mod_orario_i_str
                    df.loc[riga_idx, "Orario Fine"] = mod_orario_f_str
                    df.loc[riga_idx, "Ore"] = mod_ore_calc
                    df.loc[riga_idx, "Classe"] = mod_classe
                    df.loc[riga_idx, "Sede"] = mod_sede
                    df.loc[riga_idx, "Modalità"] = mod_modalita
                    df.loc[riga_idx, "Svolto"] = mod_svolto
                    df.loc[riga_idx, "Note"] = mod_note

                    dati_evento = {
                        "Data": mod_data.strftime("%Y-%m-%d"),
                        "Orario Inizio": mod_orario_i_str,
                        "Orario Fine": mod_orario_f_str,
                        "Classe": mod_classe,
                        "Sede": mod_sede,
                        "Modalità": mod_modalita,
                        "Note": mod_note
                    }

                    cal_id_esistente = str(df.loc[riga_idx, "Calendar_ID"]) if "Calendar_ID" in df.columns else ""
                    if cal_id_esistente and cal_id_esistente.lower() not in ["nan", "none", ""]:
                        res_id = sincronizza_google_calendar("aggiorna", dati_evento, cal_id_esistente)
                        df.loc[riga_idx, "Calendar_ID"] = str(res_id) if res_id else cal_id_esistente
                    else:
                        cal_id = sincronizza_google_calendar("crea", dati_evento)
                        df.loc[riga_idx, "Calendar_ID"] = str(cal_id) if cal_id else ""

                    salva_dati(df)
                    st.success("Modifiche salvate e calendario aggiornato!")
                    st.rerun()

        # ================= REPORT =================
        st.markdown("---")
        st.subheader("📈 Generazione Report, Ricerca & Ordinamento")

        col_t1, col_t2, col_t3 = st.columns(3)
        with col_t1:
            ricerca_libera = st.text_input("🔍 Ricerca libera", placeholder="Parole chiave...")
        with col_t2:
            data_inizio_filtro = st.date_input("Data Inizio", value=None, format="DD/MM/YYYY")
        with col_t3:
            data_fine_filtro = st.date_input("Data Fine", value=None, format="DD/MM/YYYY")

        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            classi_disponibili = ["Tutti"] + sorted(df["Classe"].dropna().unique().tolist())
            filtro_classe = st.selectbox("Filtra per Classe", options=classi_disponibili)
        with col_f2:
            sedi_disponibili = ["Tutti"] + sorted(df["Sede"].dropna().unique().tolist())
            filtro_sede = st.selectbox("Filtra per Sede", options=sedi_disponibili)
        with col_f3:
            modalita_disponibili = ["Tutti"] + sorted(df["Modalità"].dropna().unique().tolist())
            filtro_modalita = st.selectbox("Filtra per Modalità", options=modalita_disponibili)

        st.markdown("##### 🔃 Opzioni di Ordinamento Report")
        col_ord1, col_ord2 = st.columns(2)
        with col_ord1:
            campi_ordinamento = {
                "Data": "Data_dt",
                "Classe": "Classe",
                "Sede": "Sede",
                "Tipologia / Modalità": "Modalità"
            }
            scelta_ordinamento = st.selectbox("Ordina per", options=list(campi_ordinamento.keys()))
        with col_ord2:
            direzione_ordinamento = st.radio("Direzione", options=["Crescente (A-Z / Dal più vecchio)", "Decrescente (Z-A / Dal più recente)"], horizontal=True)
        crescente = "Crescente" in direzione_ordinamento

        df_report = df.copy()
        if "Data_dt" not in df_report.columns:
            df_report["Data_dt"] = df_report["Data"].apply(parse_data_italiana)
        df_report["Ore"] = df_report.apply(lambda r: calcola_ore(r.get("Orario Inizio"), r.get("Orario Fine")), axis=1)

        if data_inizio_filtro:
            df_report = df_report[df_report["Data_dt"] >= pd.to_datetime(data_inizio_filtro)]
        if data_fine_filtro:
            df_report = df_report[df_report["Data_dt"] <= pd.to_datetime(data_fine_filtro)]

        if filtro_classe != "Tutti":
            df_report = df_report[df_report["Classe"] == filtro_classe]
        if filtro_sede != "Tutti":
            df_report = df_report[df_report["Sede"] == filtro_sede]
        if filtro_modalita != "Tutti":
            df_report = df_report[df_report["Modalità"] == filtro_modalita]

        if ricerca_libera:
            termini = [t.strip() for t in ricerca_libera.split(",") if t.strip()]
            if termini:
                def match_multipli(row):
                    riga_str = " ".join(row.astype(str).values).lower()
                    return any(termine.lower() in riga_str for termine in termini)
                df_report = df_report[df_report.apply(match_multipli, axis=1)]

        colonna_ordinamento = campi_ordinamento[scelta_ordinamento]
        if colonna_ordinamento in df_report.columns:
            if colonna_ordinamento == "Data_dt":
                df_report = df_report.sort_values(by=["Data_dt", "Orario Inizio"], ascending=[crescente, True])
            else:
                df_report = df_report.sort_values(by=[colonna_ordinamento, "Data_dt"], ascending=[crescente, True])

        ore_totali = df_report["Ore"].sum()

        st.markdown(f"Risultati filtrati: **{len(df_report)}** attività | Ore totali: **{ore_totali:.2f} ore**")

        if not df_report.empty:
            st.markdown("---")
            st.markdown("### 📋 Elenco Attività in Evidenza")

            for _, row in df_report.iterrows():
                parsed_dt = parse_data_italiana(row["Data"])
                data_formattata = parsed_dt.strftime("%d/%m/%Y") if pd.notnull(parsed_dt) else str(row["Data"])
                classe = str(row["Classe"])
                sede = str(row["Sede"])
                modalita = str(row["Modalità"])
                orario_i = str(row["Orario Inizio"])
                orario_f = str(row["Orario Fine"])
                ore_val = row["Ore"]
                svolto_card = bool(row["Svolto"]) if "Svolto" in row else False
                note = str(row["Note"]) if pd.notnull(row["Note"]) else ""

                if svolto_card:
                    bg_color = "#2b2b2b"
                    border_color = "#444444"
                    text_style = "color: #7f7f7f; text-decoration: line-through;"
                else:
                    mod_lower = modalita.lower()
                    if "presenza" in mod_lower:
                        bg_color = "#1c3d73"
                        border_color = "#3b73c4"
                    elif "video" in mod_lower:
                        bg_color = "#155c32"
                        border_color = "#2fa866"
                    else:
                        bg_color = "#262626"
                        border_color = "#555555"
                    text_style = "color: #ffffff;"

                st.markdown(
                    f"""
                    <div style="background-color: {bg_color}; border: 1px solid {border_color}; padding: 15px; border-radius: 8px; margin-bottom: 10px; {text_style}">
                        <strong>📅 {data_formattata}</strong> | ⏰ {orario_i} - {orario_f} ({ore_val:.2f}h)<br>
                        <strong>🏫 Classe/Committente:</strong> {classe} | <strong>📍 Sede:</strong> {sede} | <strong>💻 Modalità:</strong> {modalita}<br>
                        <em>📝 Note:</em> {note if note else 'Nessuna nota'}
                    </div>
                    """,
                    unsafe_allow_html=True
                )
