import streamlit as st
import pandas as pd
import time

# Configuración de la página del Escritorio Jurídico
st.set_page_config(
    page_title="Escritorio Jurídico - Control de Causas",
    page_icon="⚖️",
    layout="wide"
)

st.title("⚖️ Escritorio Jurídico - Control Digital de Causas")
st.markdown("Plataforma interactiva vinculada a Google Sheets mediante exportación CSV directa.")

# ID limpio extraído de tu enlace
SHEET_ID = "1-CGHw4jFXPraBcNMPOL9n4EHnCu3jl0U2aib3lfMkhU"

# Bajamos el tiempo de caché a 2 segundos para permitir la actualización rápida
@st.cache_data(ttl=2)
def cargar_datos(url):
    try:
        # Pandas lee el CSV de Google directamente a través de la red
        return pd.read_csv(url)
    except Exception as e:
        st.error(f"Error al leer la pestaña: {e}")
        return None

# --- CONTENEDOR DE AUTO-REFRESCO AUTOMÁTICO VIA FRAGMENTOS ---
@st.fragment(run_every=3) # ⏳ ¡Aquí ocurre la magia! Recarga esta sección cada 3 segundos de manera invisible
def mostrar_tablero():
    # Creamos un timestamp dinámico para obligar a Google a saltarse su propio caché interno
    timestamp = int(time.time())
    
    URL_ADMIN = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=administrativos&cb={timestamp}"
    URL_TRIBUNAL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=tribunal_causas&cb={timestamp}"

    # Intentar la carga de datos frescos
    df_admin = cargar_datos(URL_ADMIN)
    df_tribunal_causas = cargar_datos(URL_TRIBUNAL)

    # Mostrar indicador visual discreto del estado de actualización
    st.caption(f"🔄 Última sincronización automática: Hace un instante")

    # Crear la interfaz de pestañas en Streamlit
    tab1, tab2 = st.tabs(["📁 Trámites Administrativos", "🏛️ tribunal_causas"])

    with tab1:
        st.subheader("Control de Casos Administrativos")
        if df_admin is not None and not df_admin.empty:
            st.dataframe(df_admin, use_container_width=True)
        else:
            st.info("No hay datos disponibles en la pestaña 'administrativos' o el documento no es público.")

    with tab2:
        st.subheader("Control de Casos Tribunalicios")
        if df_tribunal is not None and not df_tribunal.empty:
            st.dataframe(df_tribunal, use_container_width=True)
        else:
            st.info("No hay datos disponibles en la pestaña 'tribunal_causas' o el documento no es público.")

# Ejecutar el tablero dinámico
mostrar_tablero()
