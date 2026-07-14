import streamlit as st
import pandas as pd
import io
import re

# 1. CONFIGURACIÓN DE PÁGINA Y ESTILO
st.set_page_config(page_title="Conciliación Bancaria", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #0d1b2a; color: #e0e1dd; }
    .footer { position: fixed; left: 0; bottom: 0; width: 100%; background-color: #0b132b; color: #bcbed8; text-align: center; padding: 10px; }
    </style>
""", unsafe_allow_html=True)

st.title("📊 Sistema Automatizado de Conciliación Bancaria")

# 2. SELECTORES DE CONFIGURACIÓN
c1, c2 = st.columns(2)
with c1: empresa = st.selectbox("🏢 Empresa:", ["Thermo Group", "Mystic", "Keravital"])
with c2: banco = st.selectbox("🏦 Banco:", ["Banesco", "Venezuela", "Banplus", "Mercantil", "Banco Fondo Común"])

p1, p2, p3 = st.columns(3)
with p1: frecuencia = st.selectbox("⏱️ Frecuencia:", ["Semanal", "Quincenal", "Mensual"])
with p2: mes = st.selectbox("📆 Mes:", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"])
with p3: ano = st.selectbox("📅 Año:", ["2026", "2027", "2025"])

# 3. CARGA DE ARCHIVOS
col1, col2 = st.columns(2)
with col1: banco_file = st.file_uploader("📥 Estado de Cuenta (.csv)", type=["csv"])
with col2: profit_file = st.file_uploader("📥 Reporte Profit (.csv)", type=["csv"])

# 4. PROCESAMIENTO
def limpiar_referencia(valor):
    if pd.isna(valor): return ""
    v = str(valor)
    if 'E+' in v: v = str(int(float(v)))
    return re.sub(r'[^0-9]', '', v)

def procesar_csv(file):
    try:
        df = pd.read_csv(file, sep=';', encoding="latin-1", dtype=str)
        # Buscar columna 'referencia' (sin importar mayúsculas)
        cols_ref = [c for c in df.columns if 'referencia' in c.lower()]
        ref_col = cols_ref[0] if cols_ref else df.columns[1]
        
        # Seleccionar solo lo necesario y limpiar
        df = df[[df.columns[0], ref_col, df.columns[2], df.columns[3], df.columns[4]]]
        df.columns = ['Fecha', 'Ref', 'Desc', 'Deb', 'Cred']
        
        df['Ref_Clean'] = df['Ref'].apply(limpiar_referencia)
        df['Monto'] = pd.to_numeric(df['Cred'].str.replace(',', '.'), errors='coerce').fillna(0)
        return df
    except Exception as e:
        st.error(f"Error procesando archivo: {e}")
        return None

if banco_file and profit_file:
    df_b = procesar_csv(banco_file)
    df_p = procesar_csv(profit_file)
    
    if df_b is not None and df_p is not None:
        df_b['Key'] = df_b['Ref_Clean'] + "_" + df_b['Monto'].astype(str)
        df_p['Key'] = df_p['Ref_Clean'] + "_" + df_p['Monto'].astype(str)
        
        cruces = df_b[df_b['Key'].isin(df_p['Key'])]
        solo_b = df_b[~df_b['Key'].isin(df_p['Key'])]
        solo_p = df_p[~df_p['Key'].isin(df_b['Key'])]
        
        # 5. MOSTRAR TABLAS LIMPIAS (Solo columnas originales)
        cols_finales = ['Fecha', 'Ref', 'Desc', 'Deb', 'Cred']
        t1, t2, t3 = st.tabs(["✅ Cruces Exitosos", "🏦 Solo Banco", "💻 Solo Profit"])
        t1.dataframe(cruces[cols_finales], use_container_width=True)
        t2.dataframe(solo_b[cols_finales], use_container_width=True)
        t3.dataframe(solo_p[cols_finales], use_container_width=True)

st.markdown('<div class="footer"><p>© 2026 | Sistema Automatizado de Conciliación Bancaria</p></div>', unsafe_allow_html=True)
