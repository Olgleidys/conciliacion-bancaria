import streamlit as st
import pandas as pd
import io
import re

# 1. CONFIGURACIÓN Y ESTILO (Mantenido igual)
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

# Configuración (Mantenida igual)
c1, c2 = st.columns(2)
with c1: empresa = st.selectbox("🏢 Empresa:", ["Thermo Group", "Mystic", "Keravital"])
with c2: banco = st.selectbox("🏦 Banco:", ["Banesco", "Venezuela", "Banplus", "Mercantil", "Banco Fondo Común"])

# Carga de archivos
col1, col2 = st.columns(2)
with col1: banco_file = st.file_uploader("📥 Estado de Cuenta (.csv)", type=["csv"])
with col2: profit_file = st.file_uploader("📥 Reporte Profit (.csv)", type=["csv"])

def procesar(file):
    df = pd.read_csv(file, sep=';', encoding="latin-1", dtype=str)
    cols_ref = [c for c in df.columns if 'referencia' in c.lower()]
    ref_col = cols_ref[0] if cols_ref else df.columns[1]
    df = df[[df.columns[0], ref_col, df.columns[2], df.columns[3], df.columns[4]]]
    df.columns = ['Fecha', 'Ref', 'Desc', 'Deb', 'Cred']
    return df

def limpiar_ref(valor):
    if pd.isna(valor): return ""
    return re.sub(r'[^0-9]', '', str(valor))

def limpiar_monto(valor):
    # Elimina puntos de miles y cambia coma por punto decimal
    v = str(valor).replace('.', '').replace(',', '.')
    return pd.to_numeric(v, errors='coerce')

if banco_file and profit_file:
    df_b = procesar(banco_file)
    df_p = procesar(profit_file)
    
    # Preparación
    for df in [df_b, df_p]:
        df['Ref_Clean'] = df['Ref'].apply(limpiar_ref)
        df['Monto'] = df['Cred'].apply(limpiar_monto).fillna(0)
    
    # Cruces
    df_b['Key1'] = df_b['Ref_Clean'] + "_" + df_b['Monto'].astype(str)
    df_p['Key1'] = df_p['Ref_Clean'] + "_" + df_p['Monto'].astype(str)
    
    df_b['Key2'] = df_b['Ref_Clean'].str[-3:] + "_" + df_b['Monto'].astype(str)
    df_p['Key2'] = df_p['Ref_Clean'].str[-3:] + "_" + df_p['Monto'].astype(str)
    
    # Filtro de seguridad: Ref >= 3 dígitos
    df_b = df_b[df_b['Ref_Clean'].str.len() >= 3]
    df_p = df_p[df_p['Ref_Clean'].str.len() >= 3]
    
    # Lógica de cruce
    cruces = pd.concat([
        df_b[df_b['Key1'].isin(df_p['Key1'])],
        df_b[~df_b['Key1'].isin(df_p['Key1']) & df_b['Key2'].isin(df_p['Key2'])]
    ])
    
    solo_b = df_b[~df_b['Key1'].isin(df_p['Key1']) & ~df_b['Key2'].isin(df_p['Key2'])]
    solo_p = df_p[~df_p['Key1'].isin(df_b['Key1']) & ~df_p['Key2'].isin(df_b['Key2'])]
    
    # Mostrar resultados
    cols = ['Fecha', 'Ref', 'Desc', 'Deb', 'Cred']
    t1, t2, t3 = st.tabs(["✅ Cruces Exitosos", "🏦 Solo Banco", "💻 Solo Profit"])
    t1.dataframe(cruces[cols], use_container_width=True)
    t2.dataframe(solo_b[cols], use_container_width=True)
    t3.dataframe(solo_p[cols], use_container_width=True)
