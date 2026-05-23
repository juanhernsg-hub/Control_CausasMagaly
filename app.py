import streamlit as st
from streamlit_gsheets import GSheetsConnection

# Configuración de la página del Escritorio Jurídico
st.set_page_config(
    page_title="Escritorio Jurídico - Control de Causas",
    page_icon="⚖️",
    layout="wide"
)

st.title("⚖️ Escritorio Jurídico - Control Digital de Causas")
st.markdown("Plataforma interactiva automatizada vinculada a Google Sheets en tiempo real.")

# Conexión directa con Google Sheets usando las credenciales de Secrets
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # Lectura de las dos pestañas de tu archivo Google Sheets
    df_admin = conn.read(worksheet="administrativos", ttl=0)
    df_tribunal = conn.read(worksheet="tribunal_causas", ttl=0)
    
    # Crear pestañas visuales atractivas en la interfaz web
    tab1, tab2 = st.tabs(["📁 Trámites Administrativos", "🏛️ Causas Tribunalicias"])
    
    with tab1:
        st.subheader("Control de Casos Administrativos")
        if df_admin is not None and not df_admin.empty:
            st.dataframe(df_admin, use_container_width=True)
        else:
            st.info("No hay registros en la pestaña de administrativos o la tabla está vacía.")
            
    with tab2:
        st.subheader("Control de Casos Tribunalicios")
        if df_tribunal is not None and not df_tribunal.empty:
            st.dataframe(df_tribunal, use_container_width=True)
        else:
            st.info("No hay registros en la pestaña de tribunal_causas o la tabla está vacía.")

except Exception as e:
    st.error(f"Error al conectar con Google Sheets. Verifica las pestañas: {e}")
