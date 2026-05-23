import streamlit as st
import pandas as pd

# Configuración de la página del Escritorio Jurídico
st.set_page_config(
    page_title="Escritorio Jurídico - Control de Causas",
    page_icon="⚖️",
    layout="wide"
)

st.title("⚖️ Escritorio Jurídico - Control Digital de Causas")
st.markdown("Plataforma interactiva vinculada a Google Sheets mediante exportación CSV directa.")

# 🔑 REEMPLAZA ESTO: Pon aquí el ID largo de tu Google Sheets (el que va después de /d/)
SHEET_ID = "1-CGHw4jFXPraBcNMPOL9n4EHnCu3jl0U2aib3lfMkhU1-CGHw4jFXPraBcNMPOL9n4EHnCu3jl0U2aib3lfMkhU"

# URLs de exportación directa para cada pestaña en formato CSV
URL_ADMIN = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=administrativos"
URL_TRIBUNAL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=tribunal_causas"

@st.cache_data(ttl=0)
def cargar_datos(url):
    try:
        # Pandas lee el CSV de Google directamente a través de la red
        return pd.read_csv(url)
    except Exception as e:
        st.error(f"Error al leer la pestaña: {e}")
        return None

# Intentar la carga de datos
df_admin = cargar_datos(URL_ADMIN)
df_tribunal = cargar_datos(URL_TRIBUNAL)

# Crear la interfaz de pestañas en Streamlit
tab1, tab2 = st.tabs(["📁 Trámites Administrativos", "🏛️ Causas Tribunalicias"])

with tab1:
    st.subheader("Control de Casos Administrativos")
    if df_admin is not None and not df_admin.empty:
        st.dataframe(df_admin, use_container_width=True)
    else:
        st.info("No hay datos disponibles en la pestaña 'administrativos'.")

with tab2:
    st.subheader("Control de Casos Tribunalicios")
    if df_tribunal is not None and not df_tribunal.empty:
        st.dataframe(df_tribunal, use_container_width=True)
    else:
        st.info("No hay datos disponibles en la pestaña 'tribunal_causas'.")
