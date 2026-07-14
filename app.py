import streamlit as st
import pandas as pd
import io

# Configuración y CSS (Mantenido)
st.set_page_config(page_title="Conciliación Bancaria con KPIs", page_icon="📊", layout="wide")
custom_css = """
    <style>
    .stApp { background-color: #0d1b2a; color: #e0e1dd; }
    h1, h2, h3 { color: #ffffff !important; }
    div[data-testid="stMetricValue"] { color: #00b4d8 !important; }
    .stDownloadButton button { background-color: #0077b6 !important; color: white !important; }
    </style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

st.title("📊 Sistema Automatizado de Conciliación Bancaria")

# Configuración de Período
c1, c2, c3 = st.columns(3)
mes = c1.selectbox("📆 Mes:", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"])
ano = c2.selectbox("📅 Año:", ["2026", "2027", "2025"])
frecuencia = c3.selectbox("⏱️ Frecuencia:", ["Semanal", "Quincenal", "Mensual"])

# Selección de archivos
col1, col2 = st.columns(2)
banco_file = col1.file_uploader("📥 Estado de Cuenta Bancario", type=["csv"])
profit_file = col2.file_uploader("📥 Reporte de Profit Plus", type=["csv"])

def preparar_df(file):
    # Leemos el archivo y forzamos la fecha al inicio
    df = pd.read_csv(file, sep=None, encoding="latin-1", engine="python", on_bad_lines="skip")
    df.columns = [str(c).strip() for c in df.columns]
    
    # Normalizar columnas: Referencia -> Ref
    if 'Referencia' in df.columns: df.rename(columns={'Referencia': 'Ref'}, inplace=True)
    
    # Asegurar orden de columnas (asumiendo que las primeras 3 son Fecha, Ref, Desc)
    cols = list(df.columns)
    df = df.rename(columns={cols[0]: 'Fecha', cols[1]: 'Ref', cols[2]: 'Desc'})
    
    # Conversión segura de fecha
    df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce', dayfirst=True).dt.strftime('%d/%m/%Y')
    
    # Limpieza de Referencia y Montos
    df['Ref'] = df['Ref'].fillna('').astype(str).str.strip()
    
    # Calcular monto total (usando columnas 3 y 4 como Debe/Haber o Deb/Cred)
    df['M1'] = pd.to_numeric(df.iloc[:, 3].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False), errors='coerce').fillna(0)
    df['M2'] = pd.to_numeric(df.iloc[:, 4].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False), errors='coerce').fillna(0)
    df['Monto_Limpio'] = df['M1'] + df['M2']
    
    return df

if banco_file and profit_file:
    df_b = preparar_df(banco_file)
    df_p = preparar_df(profit_file)

    # Lógica de cruces (100% y últimos 3 dígitos)
    cruce_1 = pd.merge(df_b, df_p, on=['Ref', 'Monto_Limpio'], suffixes=('_B', '_P'))
    
    df_b['Ref_3'] = df_b['Ref'].str[-3:]
    df_p['Ref_3'] = df_p['Ref'].str[-3:]
    
    res_b = df_b[~df_b.index.isin(cruce_1.index)]
    res_p = df_p[~df_p.index.isin(cruce_1.index)]
    
    cruce_2 = pd.merge(res_b, res_p, on=['Ref_3', 'Monto_Limpio'], suffixes=('_B', '_P'))
    
    cruces = pd.concat([cruce_1, cruce_2])
    solo_b = df_b[~df_b.index.isin(cruces.index)]
    solo_p = df_p[~df_p.index.isin(cruces.index)]

    # Visualización limpia
    tab1, tab2, tab3 = st.tabs(["✅ Cruces Exitosos", "🏦 Pendiente Banco", "💻 Pendiente Profit"])
    
    with tab1: st.dataframe(cruces[['Fecha_B', 'Ref_B', 'Desc_B', 'M1_B', 'M2_B']], use_container_width=True)
    with tab2: st.dataframe(solo_b[['Fecha', 'Ref', 'Desc', 'M1', 'M2']], use_container_width=True)
    with tab3: st.dataframe(solo_p[['Fecha', 'Ref', 'Desc', 'M1', 'M2']], use_container_width=True)
    
    st.info(f"Reporte generado para {mes} {ano} - {frecuencia}")
