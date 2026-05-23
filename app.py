import streamlit as st
import pandas as pd
import re

# Configuración de la página del Escritorio Jurídico
st.set_page_config(
    page_title="Escritorio Jurídico - Control de Causas",
    page_icon="⚖️",
    layout="wide"
)

st.title("⚖️ Escritorio Jurídico - Control Digital de Causas")
st.markdown("Plataforma interactiva automatizada vinculada a Google Sheets mediante exportación directa.")

# 🔗 REEMPLAZA EL ENLACE DE ABAJO: Pon el enlace de compartir de tu Google Sheets real
URL_COMPARTIR = "https://docs.google.com/spreadsheets/d/1-CGHw4jFXPraBcNMPOL9n4EHnCu3jl0U2aib3lfMkhU/edit?usp=sharing"

def extraer_sheet_id(url):
    match = re.search(r"/d/([a-zA-Z0-9-_]+)", url)
    if match:
        return match.group(1)
    return None

SHEET_ID = extraer_sheet_id(URL_COMPARTIR)

if not SHEET_ID or "TU_ENLACE_COMPLETO_AQUI" in URL_COMPARTIR:
    st.warning("⚠️ Por favor, edita la línea 16 de tu código e introduce tu enlace de compartir de Google Sheets real.")
else:
    # 🛠️ URLs corregidas apuntando exactamente a los nombres reales de tus pestañas
    URL_ADMIN = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=administrativos"
    URL_TRIBUNAL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=tribunalicios"

    @st.cache_data(ttl=0)
    def cargar_datos(url):
        try:
            return pd.read_csv(url)
        except Exception as e:
            return None

    # Intento de lectura de datos
    df_admin = cargar_datos(URL_ADMIN)
    df_tribunal = cargar_datos(URL_TRIBUNAL)

    # Crear la interfaz visual de navegación
    tab1, tab2 = st.tabs(["📁 Trámites Administrativos", "🏛️ Causas Tribunalicias"])

    with tab1:
        st.subheader("Control de Casos Administrativos")
        if df_admin is not None:
            st.dataframe(df_admin, use_container_width=True)
        else:
            st.error("No se pudo leer la pestaña 'administrativos'. Verifica que el archivo esté configurado como 'Cualquier persona con el enlace' en modo Lector.")

    with tab2:
        st.subheader("Control de Casos Tribunalicios")
        if df_tribunal is not None:
            st.dataframe(df_tribunal, use_container_width=True)
        else:
            st.error("No se pudo leer la pestaña 'tribunalicios'. Verifica que el nombre en Google Sheets coincida exactamente.")
