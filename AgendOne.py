import datetime
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
    
    # Se la stringa è nel formato ISO YYYY-MM-DD
    if "-" in val_str and len(val_str.split("-")[0]) == 4:
        try:
            return pd.to_datetime(val_str, format="%Y-%m-%d")
        except:
            pass
            
    # Parsing esplicito formato italiano DD/MM/YYYY o D/M/YYYY
    try:
        parti = val_str.split("/")
        if len(parti) == 3:
            giorno, mese, anno = int(parti[0]), int(parti[1]), int(parti[2])
            return datetime.datetime(anno, mese, giorno)
    except:
        pass
        
    return pd.to_datetime(val_str, errors="coerce", dayfirst=True)

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
            "private_key": gsheets_secrets.get("private_key", "").replace("\n", "\n"),
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
    empty_df = pd.DataFrame(columns=[
        "Data", "Mese", "Orario Inizio", "Orario Fine", "Classe", "Sede", "Modalità", "Note"
    ])
    try:
        worksheet = get_gspread_client_and_sheet()
        if worksheet is None:
            return empty_df
        data = worksheet.get_all_records()
        if not data:
            return empty_df
        df = pd.DataFrame(data)
        
        # Retrocompatibilità intestazioni
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
        return df
    except Exception as e:
        return empty_df

# Salvataggio dati su Google Sheets
def salva_dati(df_to_save):
    if "Data_dt" in df_to_save.columns:
        df_to_save = df_to_save.drop(columns=["Data_dt"])
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

            nuovo_dato = pd.DataFrame({
                "Data": [data_selezionata.strftime("%Y-%m-%d")],
                "Mese": [mese_str],
                "Orario Inizio": [orario_inizio_str],
                "Orario Fine": [orario_fine_str],
                "Classe": [val_classe],
                "Sede": [val_sede],
                "Modalità": [val_modalita],
                "Note": [note]
            })

            df = pd.concat([df, nuovo_dato], ignore_index=True)
            salva_dati(df)
            st.success("Attività salvata con successo!")
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
        if "Data" in df_vis.columns:
            df_vis["Data_dt"] = df_vis["Data"].apply(parse_data_italiana)
            df_vis["Mese"] = df_vis["Data_dt"].apply(lambda dt: traduci_mese(dt.strftime("%B")).capitalize() if pd.notnull(dt) else "")
            # Formattazione esplicita in stringa DD/MM/YYYY per la visualizzazione corretta
            df_vis["Data"] = df_vis["Data_dt"].dt.strftime("%d/%m/%Y").fillna(df_vis["Data"])
            
            cols = ["Data"] + [c for c in df_vis.columns if c not in ["Data", "Data_dt"]]
            df_vis = df_vis[cols]

        filtro = st.text_input("🔍 Cerca rapidamente nell'archivio:", placeholder="Filtra per parole chiave...")
        df_mostra = df_vis.copy()
        if filtro:
            df_mostra = df_mostra[df_mostra.apply(lambda r: r.astype(str).str.contains(filtro, case=False).any(), axis=1)]

        df_mostra.insert(0, "Seleziona", False)
        df_mostra.insert(1, "ID", df_mostra.index)

        df_editato = st.data_editor(
            df_mostra,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Seleziona": st.column_config.CheckboxColumn(required=True),
                "ID": st.column_config.NumberColumn(disabled=True),
            }
        )

        righe_selezionate = df_editato[df_editato["Seleziona"] == True]["ID"].tolist()

        if st.button("🗑️ Elimina Selezionati", type="primary", use_container_width=True):
            if righe_selezionate:
                df = df.drop(righe_selezionate).reset_index(drop=True)
                salva_dati(df)
                st.success("Righe eliminate con successo!")
                st.rerun()
            else:
                st.warning("Seleziona almeno un appuntamento da eliminare.")

        st.markdown("---")

        if len(righe_selezionate) == 1:
            riga_idx = righe_selezionate[0]
            riga_corrente = df.loc[riga_idx]

            st.markdown(f"### ✏️ Modifica Appuntamento (Riga {riga_idx})")
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

                mod_classe = st.text_input("Classe", value=str(riga_corrente["Classe"]))
                mod_sede = st.text_input("Sede", value=str(riga_corrente["Sede"]))
                mod_modalita = st.text_input("Modalità", value=str(riga_corrente["Modalità"]))
                mod_note = st.text_area("Note", value=str(riga_corrente["Note"]))

                if st.form_submit_button("💾 Salva Modifiche", use_container_width=True):
                    df.loc[riga_idx, "Data"] = mod_data.strftime("%Y-%m-%d")
                    df.loc[riga_idx, "Mese"] = traduci_mese(mod_data.strftime("%B"))
                    df.loc[riga_idx, "Orario Inizio"] = mod_orario_i_str
                    df.loc[riga_idx, "Orario Fine"] = mod_orario_f_str
                    df.loc[riga_idx, "Classe"] = mod_classe
                    df.loc[riga_idx, "Sede"] = mod_sede
                    df.loc[riga_idx, "Modalità"] = mod_modalita
                    df.loc[riga_idx, "Note"] = mod_note

                    salva_dati(df)
                    st.success("Modifiche salvate con successo!")
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
            df_report = df_report.sort_values(by=colonna_ordinamento, ascending=crescente)

        ore_totali = 0.0
        for _, row in df_report.iterrows():
            try:
                t_inizio = datetime.datetime.strptime(str(row["Orario Inizio"]), "%H:%M")
            except:
                try:
                    t_inizio = datetime.datetime.strptime(str(row["Orario Inizio"]), "%H:%M:%S")
                except:
                    t_inizio = None

            try:
                t_fine = datetime.datetime.strptime(str(row["Orario Fine"]), "%H:%M")
            except:
                try:
                    t_fine = datetime.datetime.strptime(str(row["Orario Fine"]), "%H:%M:%S")
                except:
                    t_fine = None

            if t_inizio and t_fine:
                diff = (datetime.datetime.combine(datetime.date.min, t_fine.time()) - 
                        datetime.datetime.combine(datetime.date.min, t_inizio.time())).total_seconds() / 3600.0
                if diff > 0:
                    ore_totali += diff

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
                note = str(row["Note"]) if pd.notnull(row["Note"]) else ""

                # Assegnazione colore di sfondo in base alla modalità (blu tenue per presenza, verde tenue per videolezione)
                mod_lower = modalita.lower()
                if "presenza" in mod_lower:
                    bg_color = "#162238"  # Blu tenue elegante per tema scuro
                    border_color = "#2b4c7e"
                elif "video" in mod_lower:
                    bg_color = "#153322"  # Verde tenue elegante per tema scuro
                    border_color = "#286643"
                else:
                    bg_color = "#1e1e1e"  # Default
                    border_color = "#333333"

                card_html = f"""
                <div style="
                    border: 2px solid {border_color}; 
                    border-radius: 8px; 
                    padding: 12px 16px; 
                    margin-bottom: 10px; 
                    background-color: {bg_color}; 
                    color: #ffffff;
                ">
                    <div style="font-size: 1.1em; font-weight: bold; margin-bottom: 6px;">
                        {data_formattata} &nbsp;|&nbsp; <span style="background-color: rgba(0,0,0,0.3); padding: 3px 8px; border-radius: 4px; border: 1px solid rgba(255,255,255,0.2);">🕒 {orario_i} - {orario_f}</span>
                    </div>
                    <div style="font-size: 0.95em; color: #dddddd;">
                        {classe} &nbsp;-&nbsp; {sede} &nbsp;-&nbsp; {modalita}
                    </div>
                    {f'<div style="font-size: 0.85em; color: #aaaaaa; margin-top: 6px; font-style: italic;">Note: {note}</div>' if note and note != 'nan' else ''}
                </div>
                """
                st.markdown(card_html, unsafe_allow_html=True)

            df_csv = df_report.copy()
            if "Data" in df_csv.columns:
                df_csv["Data"] = df_csv["Data_dt"].dt.strftime("%d/%m/%Y")

            colonne_originali = ["Data", "Mese", "Orario Inizio", "Orario Fine", "Classe", "Sede", "Modalità", "Note"]
            esistenti = [c for c in colonne_originali if c in df_csv.columns]
            df_csv_esportazione = df_csv[esistenti].copy()

            st.markdown("---")
            st.download_button(
                label="📥 Scarica Report Filtrato (CSV)",
                data=df_csv_esportazione.to_csv(index=False, sep=";").encode("utf-8"),
                file_name="report_orari_filtrato.csv",
                mime="text/csv",
                use_container_width=True,
            )
        else:
            st.info("Nessuna attività corrisponde ai criteri di ricerca.")
    else:
        st.info("Nessuna attività registrata nell'archivio.")
