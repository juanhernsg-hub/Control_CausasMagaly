import streamlit as st
import pandas as pd
import re
import time

# 1. Configuración de la página (DEBE SER LA PRIMERA LÍNEA DE STREAMLIT)
st.set_page_config(
    page_title="Escritorio Jurídico - Control de Causas",
    page_icon="⚖️",
    layout="wide"
)

# 🔄 SISTEMA DE AUTO-REFRESCO REPARADO
# Verifica el tiempo transcurrido y recarga la app automáticamente cada 15 segundos
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.time()

time_elapsed = time.time() - st.session_state.last_refresh
if time_elapsed > 15:
    st.session_state.last_refresh = time.time()
    st.rerun()

st.title("⚖️ Escritorio Jurídico - Control Digital de Causas")
st.markdown("Plataforma interactiva vinculada a Google Sheets en tiempo real (Auto-refresco cada 15s).")

# 🔗 REEMPLAZA ESTO: Pon aquí el enlace completo de compartir de tu Google Sheets
URL_COMPARTIR = "https://docs.google.com/spreadsheets/d/TU_ENLACE_COMPLETO_AQUI/edit?usp=sharing"

def extraer_sheet_id(url):
    match = re.search(r"/d/([a-zA-Z0-9-_]+)", url)
    if match:
        return match.group(1)
    return None

SHEET_ID = extraer_sheet_id(URL_COMPARTIR)

if not SHEET_ID or "https://docs.google.com/spreadsheets/d/1-CGHw4jFXPraBcNMPOL9n4EHnCu3jl0U2aib3lfMkhU/edit?usp=sharing" in URL_COMPARTIR:
    st.warning("⚠️ Por favor, introduce tu enlace de compartir de Google Sheets real en la línea 24.")
else:
    # Construcción de las URLs apuntando exactamente a tus pestañas reales
    URL_ADMIN = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=administrativos"
    URL_TRIBUNAL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=tribunal_causas"

    # Exigimos ttl=0 para que Streamlit NUNCA almacene datos viejos en memoria
    @st.cache_data(ttl=0)
    def cargar_datos(url_csv):
        try:
            # Añadimos un número aleatorio al final de la URL para engañar al servidor
            # y forzarlo a traer siempre el archivo más nuevo desde Google
            url_anticahe = f"{url_csv}&cache_buster={time.time()}"
            return pd.read_csv(url_anticahe)
        except Exception as e:
            return None

    # Carga de las tablas en tiempo real
    df_admin = cargar_datos(URL_ADMIN)
    df_tribunal = cargar_datos(URL_TRIBUNAL)

    # Renderizado de las pestañas visuales
    tab1, tab2 = st.tabs(["📁 Trámites Administrativos", "🏛️ Causas Tribunalicias"])

    with tab1:
        st.subheader("Control de Casos Administrativos")
        if df_admin is not None and not df_admin.empty:
            st.dataframe(df_admin, use_container_width=True)
        else:
            st.info("No hay datos disponibles en la pestaña 'administrativos' o el formato es incorrecto.")

    with tab2:
        st.subheader("Control de Casos Tribunalicios")
        if df_tribunal is not None and not df_tribunal.empty:
            st.dataframe(df_tribunal, use_container_width=True)
        else:
            st.info("No hay datos disponibles en la pestaña 'tribunal_causas' o el formato es incorrecto.")
