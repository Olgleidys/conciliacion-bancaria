import streamlit as st
import pandas as pd
import io
import re

# Configuración de página
st.set_page_config(page_title="Conciliación Bancaria", layout="wide")

st.title("📊 Sistema Automatizado de Conciliación Bancaria")

# 1. MANTENER CONFIGURACIONES
c1, c2 = st.columns(2)
with c1: empresa = st.selectbox("🏢 Empresa:", ["Thermo Group", "Mystic", "Keravital"])
with c2: banco = st.selectbox("🏦 Banco:", ["Banesco", "Venezuela", "Banplus", "Mercantil", "Banco Fondo Común"])

p1, p2, p3 = st.columns(3)
with p1: frecuencia = st.selectbox("⏱️ Frecuencia:", ["Semanal", "Quincenal", "Mensual"])
with p2: mes = st.selectbox("📆 Mes:", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"])
with p3: ano = st.selectbox("📅 Año:", ["2026", "2027", "2025"])

# 2. CARGA DE ARCHIVOS
col1, col2 = st.columns(2)
with col1: banco_file = st.file_uploader("📥 Estado de Cuenta (.csv)", type=["csv"])
with col2: profit_file = st.file_uploader("📥 Reporte Profit (.csv)", type=["csv"])

# 3. PROCESAMIENTO ESTRICTO
def procesar(file):
    # Leemos forzando el separador ";" que es el que usa tu Excel
    df = pd.read_csv(file, sep=';', encoding="latin-1", dtype=str)
    # Seleccionamos solo las 5 columnas base: Fecha, Ref, Desc, Deb, Cred
    df = df.iloc[:, :5]
    df.columns = ['Fecha', 'Ref', 'Desc', 'Deb', 'Cred']
    return df

def limpiar(valor):
    if pd.isna(valor): return ""
    # Corrige notación científica E+
    if 'E+' in str(valor): return str(int(float(valor)))
    return re.sub(r'[^0-9]', '', str(valor))

if banco_file and profit_file:
    df_b = procesar(banco_file)
    df_p = procesar(profit_file)
    
    # Limpieza de referencias
    df_b['Ref_Clean'] = df_b['Ref'].apply(limpiar)
    df_p['Ref_Clean'] = df_p['Ref'].apply(limpiar)
    
    # Cruce (Simplificado para evitar errores)
    df_b['Key'] = df_b['Ref_Clean'] + "_" + df_b['Cred'].astype(str)
    df_p['Key'] = df_p['Ref_Clean'] + "_" + df_p['Haber'].astype(str)
    
    cruces = df_b[df_b['Key'].isin(df_p['Key'])]
    solo_b = df_b[~df_b['Key'].isin(df_p['Key'])]
    solo_p = df_p[~df_p['Key'].isin(df_b['Key'])]

    # 4. MOSTRAR SOLO LO QUE QUIERES (Eliminamos 'Key', 'Ref_Clean' de la vista final)
    cols_a_mostrar = ['Fecha', 'Ref', 'Desc', 'Deb', 'Cred']
    
    t1, t2, t3 = st.tabs(["✅ Cruces Exitosos", "🏦 Solo Banco", "💻 Solo Profit"])
    t1.dataframe(cruces[cols_a_mostrar], use_container_width=True)
    t2.dataframe(solo_b[cols_a_mostrar], use_container_width=True)
    t3.dataframe(solo_p[cols_a_mostrar], use_container_width=True)
