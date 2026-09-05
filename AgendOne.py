import calendar
from datetime import datetime
import streamlit as st

# ==========================================================
# 1. CSS Personalizzato per i pulsanti di navigazione
# ==========================================================
st.markdown(
    """
    <style>
        /* Styling generale per i pulsanti di navigazione del calendario */
        div[data-testid="column"] button {
            background-color: #f8f9fa !important;
            color: #212529 !important;
            border: 1px solid #ced4da !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            font-size: 14px !important;
            padding: 6px 12px !important;
            transition: all 0.2s ease-in-out !important;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05) !important;
        }
        
        /* Effetto Hover (Passaggio mouse) */
        div[data-testid="column"] button:hover {
            background-color: #0d6efd !important;
            color: #ffffff !important;
            border-color: #0d6efd !important;
            box-shadow: 0 4px 8px rgba(13, 110, 253, 0.25) !important;
            transform: translateY(-1px);
        }

        /* Effetto Click */
        div[data-testid="column"] button:active {
            transform: translateY(0px);
            box-shadow: none !important;
        }

        /* Stile specifico per il pulsante OGGI (con riquadro evidenziato) */
        div[data-testid="column"] button[key="btn_today"] {
            background-color: #e7f1ff !important;
            color: #0d6efd !important;
            border-color: #b6d4fe !important;
        }
        div[data-testid="column"] button[key="btn_today"]:hover {
            background-color: #0b5ed7 !important;
            color: #ffffff !important;
        }
    </style>
""",
    unsafe_allow_html=True,
)

# ==========================================================
# 2. Inizializzazione Session State per Data e Calendario
# ==========================================================
today = datetime.today()

if "current_year" not in st.session_state:
    st.session_state.current_year = today.year

if "current_month" not in st.session_state:
    st.session_state.current_month = today.month

# Nomi dei mesi in italiano per la visualizzazione
MESI_IT = [
    "",
    "Gennaio",
    "Febbraio",
    "Marzo",
    "Aprile",
    "Maggio",
    "Giugno",
    "Luglio",
    "Agosto",
    "Settembre",
    "Ottobre",
    "Novembre",
    "Dicembre",
]

# ==========================================================
# 3. Vista Calendario e Navigazione
# ==========================================================
st.title("Gestione Orari e Classi - AgendOne")
st.subheader("Vista Calendario Mensile")

# Griglia compatta a 6 colonne per ospitare anche il pulsante di reset "Oggi"
col_a1, col_m1, col_title, col_today, col_m2, col_a2 = st.columns(
    [1, 1, 2.5, 0.8, 1, 1]
)

with col_a1:
    if st.button("« Anno", use_container_width=True, key="btn_prev_year"):
        st.session_state.current_year -= 1
        st.rerun()

with col_m1:
    if st.button("‹ Mese", use_container_width=True, key="btn_prev_month"):
        if st.session_state.current_month == 1:
            st.session_state.current_month = 12
            st.session_state.current_year -= 1
        else:
            st.session_state.current_month -= 1
        st.rerun()

with col_title:
    # Mostra Mese ed Anno correnti selezionati
    nome_mese = MESI_IT[st.session_state.current_month]
    st.markdown(
        f"<h3 style='text-align: center; margin: 0; padding-top: 2px; color: #1e293b;'>{nome_mese} {st.session_state.current_year}</h3>",
        unsafe_allow_html=True,
    )

with col_today:
    if st.button("Oggi", use_container_width=True, key="btn_today"):
        st.session_state.current_year = today.year
        st.session_state.current_month = today.month
        st.rerun()

with col_m2:
    if st.button("Mese ›", use_container_width=True, key="btn_next_month"):
        if st.session_state.current_month == 12:
            st.session_state.current_month = 1
            st.session_state.current_year += 1
        else:
            st.session_state.current_month += 1
        st.rerun()

with col_a2:
    if st.button("Anno »", use_container_width=True, key="btn_next_year"):
        st.session_state.current_year += 1
        st.rerun()

st.divider()

# ==========================================================
# 4. Rendering della griglia del mese (Esempio base)
# ==========================================================
# Qui si inserisce la logica del rendering dei giorni del mese
st.write(
    f"Visualizzazione eventi per **{MESI_IT[st.session_state.current_month]} {st.session_state.current_year}**"
)
