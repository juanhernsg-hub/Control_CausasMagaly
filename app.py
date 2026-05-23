import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import io

# Configuración estética de la interfaz
st.set_page_config(page_title="Control de Causas - Magaly", layout="wide", page_icon="⚖️")

# Inyección de estilos UI (Tarjetas corporativas azul marino #1B365D)
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
st.markdown("Plataforma interactiva automatizada vinculada a Google Sheets en tiempo real.")

# --- CONEXIÓN DIRECTA A GOOGLE SHEETS EN LA NUBE ---
# Se utiliza el conector oficial configurado en secrets.toml
conn = st.connection("gsheets", type=GSheetsConnection)

# --- PANEL DE BÚSQUEDA LATERAL (UX) ---
st.sidebar.markdown("### 🔍 Panel de Búsqueda Integrado")
buscar_global = st.sidebar.text_input("Buscar por Nombre, Cliente o Expediente:")
estado_seleccionado = st.sidebar.selectbox("Filtrar por Estado actual:", ["Todos", "Activo", "Pendiente", "Sentenciado", "Terminado", "Cerrado"])

# --- RENDERIZADO ASÍNCRONO CADA 5 SEGUNDOS ---
@st.fragment(run_every=5)
def dibujar_interfaz_usuario():
    try:
        # Se leen las dos pestañas de tu Google Sheets de forma independiente
        df_admin = conn.read(worksheet="administrativos", ttl="0m")
        df_tribunal = conn.read(worksheet="tribunalicios", ttl="0m")
    except Exception as e:
        st.error(f"Error al conectar con Google Sheets. Verifica las pestañas: {e}")
        return

    # Homologación de columnas para evitar fallos de inconsistencia de nombres
    for df in [df_admin, df_tribunal]:
        if df is not None and not df.empty:
            if 'estatus' in df.columns:
                df.rename(columns={'estatus': 'Estado'}, inplace=True)
            elif 'Estado' not in df.columns:
                df['Estado'] = 'Activo'
                
            if 'fecha_registro' in df.columns:
                df['fecha_registro'] = df['fecha_registro'].astype(str).str.slice(0, 10)

    # Aplicación de filtros interactivos
    if buscar_global:
        if df_admin is not None and not df_admin.empty and 'cliente' in df_admin.columns:
            df_admin = df_admin[df_admin['cliente'].str.contains(buscar_global, case=False, na=False)]
        if df_tribunal is not None and not df_tribunal.empty and 'partes' in df_tribunal.columns:
            df_tribunal = df_tribunal[df_tribunal['partes'].str.contains(buscar_global, case=False, na=False) | df_tribunal['numero_expediente'].str.contains(buscar_global, case=False, na=False)]
        
    if estado_seleccionado != "Todos":
        if df_admin is not None and not df_admin.empty:
            df_admin = df_admin[df_admin['Estado'] == estado_seleccionado]
        if df_tribunal is not None and not df_tribunal.empty:
            df_tribunal = df_tribunal[df_tribunal['Estado'] == estado_seleccionado]

    # SECCIÓN DE MÓDULOS DE CONTROL (Tarjetas KPI)
    cant_admin = len(df_admin) if df_admin is not None else 0
    cant_trib = len(df_tribunal) if df_tribunal is not None else 0
    cant_activos = 0
    
    if df_admin is not None and not df_admin.empty: 
        cant_activos += len(df_admin[df_admin['Estado'] == 'Activo'])
    if df_tribunal is not None and not df_tribunal.empty: 
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
            st.info("No se registran trámites administrativos bajo los parámetros seleccionados.")

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
            st.info("No se registran causas tribunalicias bajo los parámetros seleccionados.")

    # ACCESO DIRECTO AL ARCHIVO DE RESPALDO EXCEL GENERADO EN MEMORIA VIRTUAL
    st.markdown("### 📥 Descarga de Archivos Matrices")
    
    # Creamos el reporte de Excel en memoria virtual de la nube usando BytesIO
    buffer = io.BytesIO()
    try:
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            if df_admin is not None:
                df_admin.to_excel(writer, sheet_name="Trámites Administrativos", index=False)
            if df_tribunal is not None:
                df_tribunal.to_excel(writer, sheet_name="Trámites Tribunalicios", index=False)
        
        st.download_button(
            label="📥 Descargar Reporte Consolidado en Excel (.xlsx)",
            data=buffer.getvalue(),
            file_name="Control_de_Causas_Magaly.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception as e:
        st.warning(f"El reporte de descarga en Excel se está procesando: {e}")

# Ejecutar la UI
dibujar_interfaz_usuario()
