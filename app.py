App.py
import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# Configuración estética de la interfaz web
st.set_page_config(page_title="Control de Causas - Magaly", layout="wide", page_icon="⚖️")

# Inyección de estilos UI Corporativos
st.markdown("""
    <style>
    [data-testid="stMetric"] {
        background-color: #F4F7FA;
        padding: 18px;
        border-radius: 12px;
        border-left: 6px solid #1B365D;
        box-shadow: 0px 2px 5px rgba(0,0,0,0.05);
    }
    .stTabs [data-baseweb="tab"] {
        font-size: 13pt;
        font-weight: bold;
        color: #1B365D;
    }
    </style>
""", unsafe_allow_html=True)

st.title("⚖️ Escritorio Jurídico - Control Digital de Causas")
st.markdown("Plataforma interactiva en tiempo real sincronizada mediante GSheetsConnection.")

# --- PANEL DE BÚSQUEDA LATERAL ---
st.sidebar.markdown("### 🔍 Panel de Búsqueda Integrado")
buscar_global = st.sidebar.text_input("Buscar por Nombre, Cliente o Expediente:")
estado_seleccionado = st.sidebar.selectbox("Filtrar por Estado actual:", ["Todos", "Activo", "Pendiente", "Sentenciado", "Terminado", "Cerrado"])

# --- RENDERIZADO ASÍNCRONO AUTOMÁTICO ---
@st.fragment(run_every=5)
def dibujar_interfaz_usuario():
    try:
        # Inicializar la conexión oficial de Streamlit con Google Sheets
        conn = st.connection("gsheets", type=GSheetsConnection)
        
        # Leer cada pestaña (borrando caché cada 5 segundos para actualización en vivo)
        df_admin = conn.read(worksheet="administrativos", ttl=5)
        df_tribunal = conn.read(worksheet="tribunalicios", ttl=5)
    except Exception as e:
        st.error(f"Error de conexión con la API de Google Sheets: {e}")
        return

    # Limpieza básica de fechas si existen registros
    for df in [df_admin, df_tribunal]:
        if df is not None and not df.empty and 'fecha_registro' in df.columns:
            df['fecha_registro'] = df['fecha_registro'].astype(str).str.slice(0, 10)

    # Homologar nombre de columna de estado por si acaso hay inconsistencias
    for df in [df_admin, df_tribunal]:
        if df is not None and not df.empty:
            if 'estatus' in df.columns:
                df.rename(columns={'estatus': 'Estado'}, inplace=True)

    # Aplicación de filtros interactivos en memoria
    if buscar_global:
        if df_admin is not None and not df_admin.empty and 'cliente' in df_admin.columns:
            df_admin = df_admin[df_admin['cliente'].str.contains(buscar_global, case=False, na=False)]
        if df_tribunal is not None and not df_tribunal.empty and 'partes' in df_tribunal.columns:
            df_tribunal = df_tribunal[df_tribunal['partes'].str.contains(buscar_global, case=False, na=False) | df_tribunal['numero_expediente'].str.contains(buscar_global, case=False, na=False)]
        
    if estado_seleccionado != "Todos":
        if df_admin is not None and not df_admin.empty and 'Estado' in df_admin.columns:
            df_admin = df_admin[df_admin['Estado'] == estado_seleccionado]
        if df_tribunal is not None and not df_tribunal.empty and 'Estado' in df_tribunal.columns:
            df_tribunal = df_tribunal[df_tribunal['Estado'] == estado_seleccionado]

    # SECCIÓN DE MÓDULOS DE CONTROL (Tarjetas KPI)
    cant_admin = len(df_admin) if df_admin is not None else 0
    cant_trib = len(df_tribunal) if df_tribunal is not None else 0
    
    cant_activos = 0
    if df_admin is not None and not df_admin.empty and 'Estado' in df_admin.columns: 
        cant_activos += len(df_admin[df_admin['Estado'] == 'Activo'])
    if df_tribunal is not None and not df_tribunal.empty and 'Estado' in df_tribunal.columns: 
        cant_activos += len(df_tribunal[df_tribunal['Estado'] == 'Activo'])

    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric(label="🏢 Trámites Administrativos", value=cant_admin)
    with m2:
        st.metric(label="🏛️ Causas en Tribunales", value=cant_trib)
    with m3:
        st.metric(label="🟢 Total Casos Activos", value=cant_activos)

    st.markdown("---")

    # MÓDULO DE PESTAÑAS E INTERFACES TABULARES
    tab_admin, tab_trib = st.tabs(["🏢 Historial Administrativo", "🏛️ Expedientes Tribunalicios"])

    with tab_admin:
        if df_admin is not None and not df_admin.empty:
            st.dataframe(
                df_admin, 
                use_container_width=True, 
                hide_index=True,
                column_config={
                    "id": "ID", "fecha_registro": "Fecha Registro", "cliente": "Cliente",
                    "tipo_tramite": "Tipo de Trámite", "recaudos_recibidos": "Recaudos Recibidos",
                    "tramites_realizados": "Trámites Realizados", "Estado": "Estado", "registrado_por": "Usuario"
                }
            )
        else:
            st.info("No se registran trámites administrativos o la hoja de cálculo está vacía.")

    with tab_trib:
        if df_tribunal is not None and not df_tribunal.empty:
            st.dataframe(
                df_tribunal, 
                use_container_width=True, 
                hide_index=True,
                column_config={
                    "id": "ID", "fecha_registro": "Fecha Registro", "circuito": "Circuito",
                    "numero_expediente": "N° Expediente", "tribunal": "Tribunal", "partes": "Partes (Dte vs Ddo)",
                    "recurso": "Recurso", "actuaciones": "Actuaciones", "observaciones": "Observaciones",
                    "Estado": "Estado", "registrado_por": "Usuario"
                }
            )
        else:
            st.info("No se registran causas tribunalicias o la hoja de cálculo está vacía.")

dibujar_interfaz_usuario()
