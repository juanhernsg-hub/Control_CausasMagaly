import streamlit as st
from streamlit_gsheets import GSheetsConnection

# =========================
# CONFIGURACIÓN DE PÁGINA
# =========================
st.set_page_config(
    page_title="Escritorio Jurídico - Control Digital de Causas",
    page_icon="⚖️",
    layout="wide"
)

# =========================
# TÍTULO
# =========================
st.title("⚖️ Escritorio Jurídico - Control Digital de Causas")
st.markdown(
    "Plataforma interactiva automatizada vinculada a Google Sheets en tiempo real."
)

# =========================
# CONEXIÓN GOOGLE SHEETS
# =========================
try:
    # Vinculamos la conexión directamente al bloque de secrets correcto
    conn = st.connection(
        "gsheets",
        type=GSheetsConnection
    )

    # Leer hojas (Asegúrate de que los nombres coincidan exactamente en tu Excel)
    df_admin = conn.read(
        worksheet="administrativos",
        ttl=0
    )

    df_tribunal = conn.read(
        worksheet="tribunal_causas",
        ttl=0
    )

    # Crear tabs
    tab1, tab2 = st.tabs([
        "📁 Trámites Administrativos",
        "🏛️ Causas Tribunalicias"
    ])

    # TAB ADMINISTRATIVOS
    with tab1:
        st.subheader("Control de Casos Administrativos")
        if not df_admin.empty:
            st.dataframe(df_admin, use_container_width=True)
        else:
            st.info("No hay registros en la pestaña 'administrativos'.")

    # TAB TRIBUNALES
    with tab2:
        st.subheader("Control de Casos Tribunalicios")
        if not df_tribunal.empty:
            st.dataframe(df_tribunal, use_container_width=True)
        else:
            st.info("No hay registros en la pestaña 'tribunal_causas'.")

except Exception as e:
    st.error(f"Error al conectar con Google Sheets: {e}")
    st.info("💡 Consejo: Revisa que la clave privada en `.streamlit/secrets.toml` no tenga espacios extra y que hayas compartido el Google Sheet con el correo de la cuenta de servicio.")
