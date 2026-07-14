import streamlit as st
import pandas as pd
import re

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
    # IMPORTANTE: dtype=str fuerza a que TODO se lea como texto, eliminando el error de float
    df = pd.read_csv(file, sep=';', encoding="latin-1", dtype=str)
    return df

def limpiar(valor):
    if pd.isna(valor): return ""
    v = str(valor)
    # Si detecta notación científica (E+), la convierte a número entero string
    if 'E+' in v:
        try: return str(int(float(v.replace(',', '.'))))
        except: pass
    # Elimina todo lo que NO sea un número
    return re.sub(r'[^0-9]', '', v)

if banco_file and profit_file:
    df_b = procesar(banco_file)
    df_p = procesar(profit_file)
    
    # Buscamos la columna que contenga "referencia"
    col_ref_b = [c for c in df_b.columns if 'referencia' in c.lower()][0]
    col_ref_p = [c for c in df_p.columns if 'referencia' in c.lower()][0]
    
    # Limpieza de referencias forzando string
    df_b['Ref_Clean'] = df_b[col_ref_b].apply(limpiar)
    df_p['Ref_Clean'] = df_p[col_ref_p].apply(limpiar)
    
    # Cruce
    df_b['Key'] = df_b['Ref_Clean']
    df_p['Key'] = df_p['Ref_Clean']
    
    cruces = df_b[df_b['Key'].isin(df_p['Key'])]
    solo_b = df_b[~df_b['Key'].isin(df_p['Key'])]
    solo_p = df_p[~df_p['Key'].isin(df_b['Key'])]

    t1, t2, t3 = st.tabs(["✅ Cruces Exitosos", "🏦 Solo Banco", "💻 Solo Profit"])
    t1.dataframe(cruces, use_container_width=True)
    t2.dataframe(solo_b, use_container_width=True)
    t3.dataframe(solo_p, use_container_width=True)
