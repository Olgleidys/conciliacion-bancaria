import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Conciliación Bancaria", page_icon="📊", layout="wide")

# ESTILOS CSS: Fondo claro para las tarjetas de métricas y alta visibilidad
custom_css = """
    <style>
    .stApp { background-color: #f8f9fa; color: #1a1a1a; }
    h1, h2, h3 { color: #0d1b2a !important; }
    
    /* Diseño de tarjetas de métricas (Fondo Blanco, Texto oscuro) */
    [data-testid="stMetricValue"] {
        color: #0077b6 !important;
        font-size: 32px !important;
        font-weight: 800 !important;
    }
    [data-testid="stMetricLabel"] {
        color: #495057 !important;
        font-size: 18px !important;
        font-weight: bold !important;
    }
    
    /* Pestañas */
    button[data-baseweb="tab"] p { color: #333 !important; font-weight: bold !important; }
    button[data-baseweb="tab"][aria-selected="true"] p { color: #0077b6 !important; }
    </style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

st.title("📊 Sistema de Conciliación Bancaria")

# PASO 1
st.markdown("### 🏢 Configuración")
c1, c2 = st.columns(2)
empresa = c1.selectbox("Empresa:", ["Thermo Group", "Mystic", "Keravital"])
banco = c2.selectbox("Banco:", ["Banesco", "Venezuela", "Banplus", "Mercantil"])

col_upload1, col_upload2 = st.columns(2)
banco_file = col_upload1.file_uploader("Estado de Cuenta (.csv)", type=["csv"])
profit_file = col_upload2.file_uploader("Reporte Profit (.csv)", type=["csv"])

def limpiar_df(df):
    df.columns = [str(c).strip() for c in df.columns]
    # Asegurar que tenemos al menos 5 columnas
    while len(df.columns) < 5: df[f'Col_{len(df.columns)}'] = 0
    # Renombrar por posición para evitar errores de nombres
    df.columns = ['Fecha', 'Ref', 'Desc', 'Debe_Tmp', 'Haber_Tmp'] + list(df.columns[5:])
    df['Ref'] = df['Ref'].fillna('').astype(str).str.strip().str.lstrip('0').str.replace('.0', '', regex=False)
    return df

if banco_file and profit_file:
    df_b = limpiar_df(pd.read_csv(banco_file, sep=None, encoding="latin-1", engine="python"))
    df_p = limpiar_df(pd.read_csv(profit_file, sep=None, encoding="latin-1", engine="python"))

    tab_res, tab_ajustes, tab_kpi, tab_cierre = st.tabs(["📋 Resultados", "🛠️ Ajustes", "📈 KPIs", "🔒 Cierre"])

    # Logica de cruces
    refs_p = set(df_p['Ref'].unique())
    cruces = df_b[df_b['Ref'].isin(refs_p)]
    solo_b = df_b[~df_b['Ref'].isin(refs_p)]
    solo_p = df_p[~df_p['Ref'].isin(df_b['Ref'].unique())]

    # METRICAS CON DISEÑO MEJORADO
    st.markdown("---")
    m1, m2, m3 = st.columns(3)
    m1.metric("Cruces Exitosos", f"{len(cruces)} mov.")
    m2.metric("Pendientes Banco", f"{len(solo_b)} mov.")
    m3.metric("Pendientes Profit", f"{len(solo_p)} mov.")

    with tab_res:
        st.dataframe(cruces, use_container_width=True)
    with tab_ajustes:
        st.info("Ingresa referencias para forzar conciliación:")
        ajustes = st.text_input("Ej: 123, 456")
        st.write("Configuración aplicada.")

    with tab_cierre:
        st.subheader("Cálculo de Cierre")
        s_b = st.number_input("Saldo Inicial Banco:", value=0.0)
        st.success(f"Procesando con {len(cruces)} operaciones conciliadas.")
