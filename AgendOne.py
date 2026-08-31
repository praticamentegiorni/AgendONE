import datetime
import json
import os
import pandas as pd
import streamlit as st
from streamlit_gsheets import GSheetsConnection

# Configurazione della pagina (stile e titolo)
st.set_page_config(
    page_title="Gestione Orari e Classi", page_icon="🕒", layout="wide"
)

# File di configurazione locale delle tabelle
CONFIG_FILE = "config_tabelle.json"

# Inizializzazione della connessione a Google Sheets
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error(
        "Errore di connessione a Google Sheets. Verifica i parametri nei Secrets di"
        " Streamlit."
    )


# Gestione configurazione tabelle (Classi, Sedi, Modalità) con retrocompatibilità
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


# Caricamento dati in tempo reale da Google Sheets
def carica_dati():
    try:
        # ttl=0 disabilita la cache per forzare la lettura dei dati aggiornati in tempo reale
        df = conn.read(ttl=0)
        if df is None or df.empty or "Data" not in df.columns:
            return pd.DataFrame(
                columns=[
                    "Data",
                    "Mese",
                    "Orario Inizio",
                    "Orario Fine",
                    "Classe",
                    "Sede",
                    "Modalità",
                    "Note",
                ]
            )
        # Retrocompatibilità se il foglio ha ancora le vecchie intestazioni
        if "Committente" in df.columns and "Classe" not in df.columns:
            df = df.rename(columns={"Committente": "Classe"})
        if "Luogo" in df.columns and "Sede" not in df.columns:
            df = df.rename(columns={"Luogo": "Sede"})

        if "Data" in df.columns:
            df["Data_dt"] = pd.to_datetime(df["Data"], errors="coerce")
        return df
    except Exception as e:
        return pd.DataFrame(
            columns=[
                "Data",
                "Mese",
                "Orario Inizio",
                "Orario Fine",
                "Classe",
                "Sede",
                "Modalità",
                "Note",
            ]
        )


# Salvataggio e aggiornamento dati su Google Sheets tramite gspread (con debug)
def salva_dati(df_to_save):
    if "Data_dt" in df_to_save.columns:
        df_to_save = df_to_save.drop(columns=["Data_dt"])

    try:
        creds = conn._secrets["credentials"]
        spreadsheet_url = conn._secrets["spreadsheet"]

        import gspread

        client = gspread.service_account_from_dict(creds)
        spreadsheet = client.open_by_url(spreadsheet_url)
        worksheet = spreadsheet.get_worksheet(0)

        # Pulisce completamente il foglio
        worksheet.clear()
        
        # Prepara la lista di liste (intestazioni + righe)
        righe = [df_to_save.columns.values.tolist()] + df_to_save.values.tolist()
        
        # Scrive i dati
        worksheet.update("A1", righe)
        st.success("Dati salvati correttamente su Google Sheets!")
    except Exception as e:
        # Mostra l'errore tecnico dettagliato a schermo per capire la causa
        st.error(f"DETTAGLIO ERRORE GSPREAD: {str(e)}")
        raise e

df = carica_dati()

st.title("🕒 Gestione Orari e Classi")
st.markdown("---")

# Tab principali dell'applicazione
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
            data_selezionata = st.date_input(
                "Giorno", value=datetime.date.today(), format="DD/MM/YYYY"
            )
            mese_str = data_selezionata.strftime("%B")
        with col_d2:
            st.info(f"Mese di riferimento: **{mese_str}**")

        col1, col2 = st.columns(2)
        with col1:
            orario_inizio = st.time_input("Orario Inizio", value=datetime.time(9, 0))
        with col2:
            orario_fine = st.time_input("Orario Fine", value=datetime.time(18, 0))

        col_t1, col_t2, col_t3 = st.columns(3)
        with col_t1:
            classe = st.selectbox(
                "Classe",
                options=config["classi"],
                index=0 if config["classi"] else None,
                key="sel_classe",
            )
            nuova_classe_libera = st.text_input(
                "O digita nuova classe:",
                placeholder="Se non è in elenco...",
                key="lib_classe",
            )

        with col_t2:
            sede = st.selectbox(
                "Sede",
                options=config["sedi"],
                index=0 if config["sedi"] else None,
                key="sel_sede",
            )
            nuova_sede_libera = st.text_input(
                "O digita nuova sede:", placeholder="Se non è in elenco...", key="lib_sede"
            )

        with col_t3:
            modalita = st.selectbox(
                "Modalità",
                options=config["modalita"],
                index=0 if config["modalita"] else None,
                key="sel_mod",
            )
            nuovo_mod_libero = st.text_input(
                "O digita nuova modalità:",
                placeholder="Se non è in elenco...",
                key="lib_mod",
            )

        note = st.text_area(
            "Note / Descrizione dettagliata",
            placeholder="Inserisci eventuali dettagli...",
        )

        submit_button = st.form_submit_button(
            label="💾 Salva Attività", use_container_width=True
        )

        if submit_button:
            val_classe = (
                nuova_classe_libera.strip() if nuova_classe_libera else classe
            )
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
                "Orario Inizio": [str(orario_inizio)],
                "Orario Fine": [str(orario_fine)],
                "Classe": [val_classe],
                "Sede": [val_sede],
                "Modalità": [val_modalita],
                "Note": [note],
            })

            df = pd.concat([df, nuovo_dato], ignore_index=True)
            salva_dati(df)
            st.success("Attività registrata con successo su Google Sheets!")
            st.rerun()

# ================= TAB 2: GESTIONE TABELLE =================
with tab2:
    st.subheader("Amministrazione Voci e Tabelle")
    st.write(
        "Aggiungi nuove voci, eliminale o modificale direttamente"
        " aggiornandole."
    )

    col_g1, col_g2, col_g3 = st.columns(3)


    def gestisci_tabella_avanzata(nome_tabella, lista_voci):
        st.markdown(f"### {nome_tabella.capitalize()}")

        nuovo = st.text_input(
            f"Nuovo {nome_tabella[:-1]}", key=f"add_{nome_tabella}"
        )
        if st.button(f"Aggiungi", key=f"btn_add_{nome_tabella}"):
            if nuovo and nuovo not in lista_voci:
                lista_voci.append(nuovo)
                salva_config(config)
                st.success(f"Aggiunto: {nuovo}")
                st.rerun()

        st.markdown("---")
        st.markdown("**Modifica o Elimina voci esistenti:**")

        for i, voce in enumerate(list(lista_voci)):
            c_mod, c_del = st.columns([3, 1])

            voce_modificata = c_mod.text_input(
                f"Modifica {i}", value=voce, key=f"edit_{nome_tabella}_{i}"
            )

            if c_del.button("🗑️", key=f"del_{nome_tabella}_{i}"):
                lista_voci.remove(voce)
                salva_config(config)
                st.success("Voce eliminata!")
                st.rerun()

            if voce_modificata != voce:
                if voce_modificata and voce_modificata not in lista_voci:
                    lista_voci[i] = voce_modificata
                    salva_config(config)
                    st.success("Voce aggiornata!")
                    st.rerun()


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
            df_vis["Data_Italiana"] = pd.to_datetime(
                df_vis["Data"], errors="coerce"
            ).dt.strftime("%d/%m/%Y")
            cols = ["Data_Italiana"] + [
                c for c in df_vis.columns if c not in ["Data_Italiana", "Data", "Data_dt"]
            ]
            df_vis = df_vis[cols]

        filtro = st.text_input(
            "🔍 Cerca rapidamente nell'archivio (testo libero):",
            placeholder="Filtra per parole chiave, note...",
        )
        df_mostra = df_vis.copy()
        if filtro:
            df_mostra = df_mostra[
                df_mostra.apply(
                    lambda r: r.astype(str).str.contains(filtro, case=False).any(),
                    axis=1,
                )
            ]

        # Inserimento spunta e ID di servizio
        df_mostra.insert(0, "Seleziona", False)
        df_mostra.insert(1, "ID", df_mostra.index)

        st.markdown(
            "Spunta la casella **Seleziona** sulla riga che vuoi eliminare o"
            " modificare:"
        )

        df_editato = st.data_editor(
            df_mostra,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Seleziona": st.column_config.CheckboxColumn(required=True),
                "ID": st.column_config.NumberColumn(disabled=True),
            },
        )

        righe_selezionate = df_editato[df_editato["Seleziona"] == True][
            "ID"
        ].tolist()

        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button(
                "🗑️ Elimina Selezionati", type="primary", use_container_width=True
            ):
                if righe_selezionate:
                    df = df.drop(righe_selezionate).reset_index(drop=True)
                    salva_dati(df)
                    st.success("Elementi selezionati eliminati con successo!")
                    st.rerun()
                else:
                    st.warning("Seleziona almeno un appuntamento da eliminare.")

        st.markdown("---")

        # Modifica riga singola
        if len(righe_selezionate) == 1:
            riga_idx = righe_selezionate[0]
            riga_corrente = df.loc[riga_idx]

            st.markdown(
                f"### ✏️ Modifica Appuntamento Selezionato (Riga {riga_idx})"
            )

            with st.form("form_modifica_multipla"):
                try:
                    data_default = datetime.datetime.strptime(
                        str(riga_corrente["Data"]), "%Y-%m-%d"
                    ).date()
                except:
                    data_default = datetime.date.today()

                try:
                    ora_i_def = datetime.datetime.strptime(
                        str(riga_corrente["Orario Inizio"]), "%H:%M:%S"
                    ).time()
                except:
                    try:
                        ora_i_def = datetime.datetime.strptime(
                            str(riga_corrente["Orario Inizio"]), "%H:%M"
                        ).time()
                    except:
                        ora_i_def = datetime.time(9, 0)

                try:
                    ora_f_def = datetime.datetime.strptime(
                        str(riga_corrente["Orario Fine"]), "%H:%M:%S"
                    ).time()
                except:
                    try:
                        ora_f_def = datetime.datetime.strptime(
                            str(riga_corrente["Orario Fine"]), "%H:%M"
                        ).time()
                    except:
                        ora_f_def = datetime.time(18, 0)

                mod_data = st.date_input(
                    "Data", value=data_default, format="DD/MM/YYYY"
                )

                c_m1, c_m2 = st.columns(2)
                with c_m1:
                    mod_ora_inizio = st.time_input("Orario Inizio", value=ora_i_def)
                with c_m2:
                    mod_ora_fine = st.time_input("Orario Fine", value=ora_f_def)

                mod_classe = st.text_input(
                    "Classe", value=str(riga_corrente["Classe"])
                )
                mod_sede = st.text_input("Sede", value=str(riga_corrente["Sede"]))
                mod_modalita = st.text_input(
                    "Modalità", value=str(riga_corrente["Modalità"])
                )
                mod_note = st.text_area("Note", value=str(riga_corrente["Note"]))

                btn_salva_modifica = st.form_submit_button(
                    "💾 Salva Modifiche", use_container_width=True
                )

                if btn_salva_modifica:
                    df.loc[riga_idx, "Data"] = mod_data.strftime("%Y-%m-%d")
                    df.loc[riga_idx, "Mese"] = mod_data.strftime("%B")
                    df.loc[riga_idx, "Orario Inizio"] = str(mod_ora_inizio)
                    df.loc[riga_idx, "Orario Fine"] = str(mod_ora_fine)
                    df.loc[riga_idx, "Classe"] = mod_classe
                    df.loc[riga_idx, "Sede"] = mod_sede
                    df.loc[riga_idx, "Modalità"] = mod_modalita
                    df.loc[riga_idx, "Note"] = mod_note

                    salva_dati(df)
                    st.success("Modifiche salvate con successo!")
                    st.rerun()
        elif len(righe_selezionate) > 1:
            st.info(
                "ℹ️ Per modificare un appuntamento, spunta **una sola riga** alla"
                " volta nella tabella sopra."
            )

        # ================= SEZIONE REPORT E FILTRI AVANZATI =================
        st.markdown("---")
        st.subheader("📈 Generazione Report & Ricerca Avanzata")
        st.write(
            "Filtra per Classe, Sede, Modalità, intervallo di date o usa la"
            " ricerca testuale libera (puoi separare più termini con la virgola)."
        )

        col_t1, col_t2, col_t3 = st.columns(3)
        with col_t1:
            ricerca_libera = st.text_input(
                "🔍 Ricerca libera (es. parole chiave, orari, date)",
                placeholder="Es: 1A, mattina, 09:00 o separi con virgola...",
            )
        with col_t2:
            data_inizio_filtro = st.date_input(
                "Data Inizio (opzionale)", value=None, format="DD/MM/YYYY"
            )
        with col_t3:
            data_fine_filtro = st.date_input(
                "Data Fine (opzionale)", value=None, format="DD/MM/YYYY"
            )

        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            classi_disponibili = ["Tutti"] + sorted(
                df["Classe"].dropna().unique().tolist()
            )
            filtro_classe = st.selectbox(
                "Filtra per Classe", options=classi_disponibili
            )

        with col_f2:
            sedi_disponibili = ["Tutti"] + sorted(
                df["Sede"].dropna().unique().tolist()
            )
            filtro_sede = st.selectbox("Filtra per Sede", options=sedi_disponibili)

        with col_f3:
            modalita_disponibili = ["Tutti"] + sorted(
                df["Modalità"].dropna().unique().tolist()
            )
            filtro_modalita = st.selectbox(
                "Filtra per Modalità", options=modalita_disponibili
            )

        df_report = df.copy()

        if "Data_dt" not in df_report.columns:
            df_report["Data_dt"] = pd.to_datetime(
                df_report["Data"], errors="coerce"
            )

        if data_inizio_filtro:
            df_report = df_report[
                df_report["Data_dt"] >= pd.to_datetime(data_inizio_filtro)
            ]
        if data_fine_filtro:
            df_report = df_report[
                df_report["Data_dt"] <= pd.to_datetime(data_fine_filtro)
            ]

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

        ore_totali = 0.0
        for _, row in df_report.iterrows():
            try:
                t_inizio = datetime.datetime.strptime(
                    str(row["Orario Inizio"]), "%H:%M:%S"
                )
            except:
                try:
                    t_inizio = datetime.datetime.strptime(
                        str(row["Orario Inizio"]), "%H:%M"
                    )
                except:
                    t_inizio = None

            try:
                t_fine = datetime.datetime.strptime(str(row["Orario Fine"]), "%H:%M:%S")
            except:
                try:
                    t_fine = datetime.datetime.strptime(str(row["Orario Fine"]), "%H:%M")
                except:
                    t_fine = None

            if t_inizio and t_fine:
                diff = (
                    datetime.datetime.combine(datetime.date.min, t_fine.time())
                    - datetime.datetime.combine(datetime.date.min, t_inizio.time())
                ).total_seconds() / 3600.0
                if diff > 0:
                    ore_totali += diff

        st.markdown(
            f"Risultati filtrati: **{len(df_report)}** attività trovate | Ore totali"
            f" stimate: **{ore_totali:.2f} ore**"
        )

        if not df_report.empty:
            df_report_vis = df_report.copy()
            if "Data" in df_report_vis.columns:
                df_report_vis["Data_Italiana"] = pd.to_datetime(
                    df_report_vis["Data"], errors="coerce"
                ).dt.strftime("%d/%m/%Y")
                cols_rep = ["Data_Italiana"] + [
                    c
                    for c in df_report_vis.columns
                    if c not in ["Data_Italiana", "Data", "Data_dt"]
                ]
                df_report_vis = df_report_vis[cols_rep]

            st.dataframe(df_report_vis, use_container_width=True, hide_index=True)

            st.download_button(
                label="📥 Scarica Report Filtrato (CSV)",
                data=df_report.drop(
                    columns=["Data_dt"], errors="ignore"
                ).to_csv(index=False).encode("utf-8"),
                file_name="report_orari_filtrato.csv",
                mime="text/csv",
                use_container_width=True,
            )
        else:
            st.info("Nessuna attività corrisponde ai criteri di ricerca selezionati.")

        st.markdown("---")
        st.download_button(
            label="📥 Scarica Backup Completo (CSV)",
            data=df.drop(columns=["Data_dt"], errors="ignore")
            .to_csv(index=False)
            .encode("utf-8"),
            file_name="orari_lavoro.csv",
            mime="text/csv",
            use_container_width=True,
        )
    else:
        st.info("Nessuna attività registrata nell'archivio.")
