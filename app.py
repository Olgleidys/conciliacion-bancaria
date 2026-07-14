import streamlit as st
import pandas as pd
import io
import re

# 1. CONFIGURACIÓN Y ESTILO
st.set_page_config(page_title="Conciliación Bancaria", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #0d1b2a; color: #e0e1dd; }
    h1, h2, h3 { color: #ffffff !important; }
    div[data-testid="stMetricValue"] { color: #00b4d8 !important; }
    .stDownloadButton button { background-color: #0077b6 !important; color: white !important; }
    </style>
""", unsafe_allow_html=True)

st.title("📊 Sistema Automatizado de Conciliación Bancaria")

# Configuración
c1, c2 = st.columns(2)
with c1: empresa = st.selectbox("🏢 Empresa:", ["Thermo Group", "Mystic", "Keravital"])
with c2: banco = st.selectbox("🏦 Banco:", ["Banesco", "Venezuela", "Banplus", "Mercantil", "Banco Fondo Común"])

p1, p2, p3 = st.columns(3)
with p1: frecuencia = st.selectbox("⏱️ Frecuencia:", ["Semanal", "Quincenal", "Mensual"])
with p2: mes = st.selectbox("📆 Mes:", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"])
with p3: ano = st.selectbox("📅 Año:", ["2026", "2027", "2025"])

# Carga de archivos
col1, col2 = st.columns(2)
with col1: banco_file = st.file_uploader("📥 Estado de Cuenta (.csv)", type=["csv"])
with col2: profit_file = st.file_uploader("📥 Reporte Profit (.csv)", type=["csv"])

# Lógica de procesamiento
def procesar(file):
    df = pd.read_csv(file, sep=';', encoding="latin-1", dtype=str)
    cols_ref = [c for c in df.columns if 'referencia' in c.lower()]
    ref_col = cols_ref[0] if cols_ref else df.columns[1]
    df = df[[df.columns[0], ref_col, df.columns[2], df.columns[3], df.columns[4]]]
    df.columns = ['Fecha', 'Ref', 'Desc', 'Deb', 'Cred']
    return df

def limpiar(valor):
    if pd.isna(valor): return ""
    v = str(valor)
    if 'E+' in v: v = str(int(float(v.replace(',', '.'))))
    return re.sub(r'[^0-9]', '', v)

if banco_file and profit_file:
    df_b = procesar(banco_file)
    df_p = procesar(profit_file)
    
    # Limpieza básica
    df_b['Ref_Clean'] = df_b['Ref'].apply(limpiar)
    df_p['Ref_Clean'] = df_p['Ref'].apply(limpiar)
    
    # Filtro: Descartar referencias < 3 dígitos antes de procesar
    df_b = df_b[df_b['Ref_Clean'].str.len() >= 3].copy()
    df_p = df_p[df_p['Ref_Clean'].str.len() >= 3].copy()
    
    df_b['Ref_3D'] = df_b['Ref_Clean'].str[-3:]
    df_p['Ref_3D'] = df_p['Ref_Clean'].str[-3:]
    
    df_b['Monto'] = pd.to_numeric(df_b['Cred'].str.replace(',', '.'), errors='coerce').fillna(0)
    df_p['Monto'] = pd.to_numeric(df_p['Cred'].str.replace(',', '.'), errors='coerce').fillna(0)
    
    # --- PASO 1: Cruce 100% (Ref completa + Monto) ---
    df_b['Key1'] = df_b['Ref_Clean'] + "_" + df_b['Monto'].astype(str)
    df_p['Key1'] = df_p['Ref_Clean'] + "_" + df_p['Monto'].astype(str)
    
    cruces_1 = df_b[df_b['Key1'].isin(df_p['Key1'])].copy()
    cruces_1['Metodo_Cruce'] = '100% Exacto'
    
    # Restar los ya conciliados para el siguiente paso
    pendientes_b = df_b[~df_b['Key1'].isin(df_p['Key1'])].copy()
    pendientes_p = df_p[~df_p['Key1'].isin(df_b['Key1'])].copy()
    
    # --- PASO 2: Cruce últimos 3 dígitos (3D Ref + Monto) ---
    pendientes_b['Key2'] =
