import streamlit as str
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
    df_admin = conn.read(worksheet="administrativos", ttl="0m")
    df_tribunal = conn.read(worksheet="tribunal_causas", ttl="0m")
    
    # Crear pestañas visuales atractivas en la interfaz web
    tab1, tab2 = st.tabs(["📁 Trámites Administrativos", "🏛️ Causas Tribunalicias"])
    
    with tab1:
        st.subheader("Control de Casos Administrativos")
        if not df_admin.empty:
            st.dataframe(df_admin, use_container_width=True)
        else:
            st.info("No hay registros en la pestaña de administrativos.")
            
    with tab2:
        st.subheader("Control de Casos Tribunalicios")
        if not df_tribunal.empty:
            st.dataframe(df_tribunal, use_container_width=True)
        else:
            st.info("No hay registros en la pestaña de tribunal_causas.")

except Exception as e:
    st.error(f"Error al conectar con Google Sheets. Verifica las pestañas: {e}")
