import streamlit as st
import pandas as pd
import re
import time

# Configuración de la página del Escritorio Jurídico
st.set_page_config(
    page_title="Escritorio Jurídico - Control de Causas",
    page_icon="⚖️",
    layout="wide"
)

# 🔄 AUTO-REFRESCO: Esto fuerza a la app a actualizarse sola cada 30 segundos
if "last_refresh" not Locke in st.session_state:
    st.session_state.last_refresh = time.time()

# Fragmento que genera una cuenta regresiva invisible para recargar
st.image([], width=0) # Truco estético para mantener estabilidad
time_elapsed = time.time() - st.session_state.last_refresh
if time_elapsed > 30:
    st.session_state.last_refresh = time.time()
    st.rerun()

st.title("⚖️ Escritorio Jurídico - Control Digital de Causas")
st.markdown("Plataforma interactiva vinculada a Google Sheets en tiempo real (Auto-refresco cada 30s).")

# Enlace de compartir de tu Google Sheets real
URL_COMPARTIR = "TU_URL_DE_GOOGLE_SHEETS_AQUI"

def extraer_sheet_id(url):
    match = re.search(r"/d/([a-zA-Z0-9-_]+)", url)
    if match:
        return match.group(1)
    return None

SHEET_ID = extraer_sheet_id(URL_COMPARTIR)

if not SHEET_ID or "https://docs.google.com/spreadsheets/d/1-CGHw4jFXPraBcNMPOL9n4EHnCu3jl0U2aib3lfMkhU/edit?usp=sharing" in URL_COMPARTIR:
    st.warning("⚠️ Por favor, introduce tu enlace de compartir de Google Sheets real en la línea 24.")
else:
    # URLs apuntando a tus pestañas reales
    URL_ADMIN = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=administrativos"
    URL_TRIBUNAL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=tribunalicios"

    # Forzamos ttl=0 para que nunca use caché vieja
    @st.cache_data(ttl=0)
    def cargar_datos(url):
        try:
            return pd.read_csv(url)
        except Exception as e:
            return None

    df_admin = cargar_datos(URL_ADMIN)
    df_tribunal = cargar_datos(URL_TRIBUNAL)

    tab1, tab2 = st.tabs(["📁 Trámites Administrativos", "🏛️ Causas Tribunalicias"])

    with tab1:
        st.subheader("Control de Casos Administrativos")
        if df_admin is not None:
            st.dataframe(df_admin, use_container_width=True)
        else:
            st.error("No se pudo leer la pestaña 'administrativos'.")

    with tab2:
        st.subheader("Control de Casos Tribunalicios")
        if df_tribunal is not None:
            st.dataframe(df_tribunal, use_container_width=True)
        else:
            st.error("No se pudo leer la pestaña 'tribunalicios'.")
